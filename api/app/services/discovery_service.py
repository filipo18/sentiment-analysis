"""Service for discovering relevant channels and sources (OpenAI-assisted)."""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional

from app.config import get_settings
from app.services.aci_mcp_client import Gate22MCPClient
from app.services.alias_helper import AliasHelper

settings = get_settings()
logger = logging.getLogger("app.discovery_service")


class ChannelDiscoveryService:
    """Service for discovering relevant channels/subreddits for products."""

    def __init__(self) -> None:
        self.alias = AliasHelper()

        base_url = os.getenv("GATE22_MCP_URL")
        token = os.getenv("GATE22_MCP_TOKEN")
        self._reddit_tool = os.getenv("ACI_REDDIT_TOOL_ID", "reddit")
        self._lookback_days = max(int(os.getenv("DISCOVERY_LOOKBACK_DAYS", "7")), 1)
        self._posts_limit = max(int(os.getenv("DISCOVERY_POSTS_LIMIT", "120")), 1)
        self._neutral_query = "*"

        self.mcp_client: Optional[Gate22MCPClient] = None
        if base_url:
            try:
                self.mcp_client = Gate22MCPClient(base_url=base_url, token=token)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to initialize Gate22 MCP client: %s", exc)
        else:
            logger.warning("GATE22_MCP_URL not configured; discovery will yield empty Reddit results")

    async def discover_reddit(self, products: List[str]) -> List[Dict[str, Any]]:
        suggested_subs = await self.alias.suggest_subreddits(products)
        suggested_queries = await self.alias.suggest_reddit_queries(products)

        if not self.mcp_client:
            return []

        lookback_seconds = max(self._lookback_days, 1) * 24 * 60 * 60
        earliest_ts = time.time() - lookback_seconds
        neutral_query = (products[0] if products else None) or self._neutral_query

        def as_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        def as_int(value: Any) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        def bump(metrics_map: Dict[str, Dict[str, Any]], subreddit: str, submission: Dict[str, Any]) -> None:
            data = metrics_map.setdefault(
                subreddit,
                {
                    "platform": "reddit",
                    "channel_id": subreddit,
                    "name": f"r/{subreddit}",
                    "metrics": {"mentions": 0, "avg_score": 0.0, "comments": 0},
                },
            )
            metrics = data["metrics"]
            metrics["mentions"] += 1
            metrics["avg_score"] += as_float(submission.get("score", 0))
            metrics["comments"] += as_int(submission.get("num_comments", submission.get("comments", 0)))

        def extract_submissions(payload: Any) -> List[Dict[str, Any]]:
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
            if not isinstance(payload, dict):
                return []

            queue: List[Any] = [payload]
            seen: set[int] = set()
            while queue:
                current = queue.pop(0)
                if isinstance(current, list):
                    return [item for item in current if isinstance(item, dict)]
                if isinstance(current, dict):
                    ident = id(current)
                    if ident in seen:
                        continue
                    seen.add(ident)
                    for key in ("items", "results", "data", "submissions", "value"):
                        if key in current:
                            queue.append(current[key])
            return []

        def resolve_subreddit_name(submission: Dict[str, Any], fallback: Optional[str] = None) -> Optional[str]:
            subreddit = submission.get("subreddit")
            if isinstance(subreddit, dict):
                name = subreddit.get("display_name") or subreddit.get("name") or subreddit.get("id")
                if isinstance(name, str) and name:
                    return name
            if isinstance(subreddit, str) and subreddit:
                return subreddit
            if fallback:
                return fallback
            return None

        def created_after_threshold(submission: Dict[str, Any]) -> bool:
            created = submission.get("created_utc") or submission.get("created")
            if created is None:
                return True
            try:
                created_ts = float(created)
            except (TypeError, ValueError):
                return True
            return created_ts >= earliest_ts

        def fetch_submissions(actions: Iterable[str], params: Dict[str, Any]) -> List[Dict[str, Any]]:
            action_sequence = tuple(actions)
            last_error: Optional[Exception] = None
            for action in action_sequence:
                try:
                    response = self.mcp_client.execute(self._reddit_tool, action, params)
                    return extract_submissions(response)
                except Exception as exc:  # noqa: BLE001 - we want to keep discovery resilient
                    last_error = exc
                    logger.debug("Reddit MCP action %s failed: %s", action, exc)
            if last_error:
                logger.warning("Reddit MCP request failed after trying %s: %s", action_sequence, last_error)
            return []

        def measure_sync() -> List[Dict[str, Any]]:
            aggregated: Dict[str, Dict[str, Any]] = {}

            # Measure suggested subreddits via recent posts
            for sub in (suggested_subs or [])[:20]:
                params = {
                    "subreddit": sub,
                    "time_filter": "week",
                    "limit": self._posts_limit,
                }
                submissions = fetch_submissions(("list_new",), params)
                if not submissions:
                    params_with_query = {**params, "query": neutral_query, "sort": "new"}
                    submissions = fetch_submissions(("search",), params_with_query)
                for submission in submissions:
                    subreddit_name = resolve_subreddit_name(submission, fallback=sub)
                    if not subreddit_name or not created_after_threshold(submission):
                        continue
                    try:
                        bump(aggregated, subreddit_name, submission)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.debug("Skipping submission due to error: %s", exc)

            # Search suggested queries across r/all
            for query in (suggested_queries or [])[:5]:
                params = {
                    "query": query,
                    "subreddit": "all",
                    "sort": "new",
                    "time_filter": "week",
                    "limit": self._posts_limit,
                }
                submissions = fetch_submissions(("search",), params)
                for submission in submissions:
                    subreddit_name = resolve_subreddit_name(submission)
                    if not subreddit_name or not created_after_threshold(submission):
                        continue
                    try:
                        bump(aggregated, subreddit_name, submission)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.debug("Skipping submission due to error: %s", exc)

            results: List[Dict[str, Any]] = []
            for item in aggregated.values():
                metrics = item["metrics"]
                mentions = max(metrics["mentions"], 1)
                metrics["avg_score"] = metrics["avg_score"] / mentions
                item["score"] = float(
                    metrics["mentions"] * 0.6 + metrics["avg_score"] * 0.2 + metrics["comments"] * 0.2
                )
                results.append(item)

            return sorted(results, key=lambda it: it.get("score", 0), reverse=True)[: settings.MAX_DISCOVERY_RESULTS]

        try:
            return await asyncio.to_thread(measure_sync)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Reddit discovery failed: %s", exc)
            return []
    
    async def discover(self, products: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Main discovery method that returns results for all platforms."""
        sources: Dict[str, List[Dict[str, Any]]] = {}
        sources["reddit"] = await self.discover_reddit(products)
        return sources
