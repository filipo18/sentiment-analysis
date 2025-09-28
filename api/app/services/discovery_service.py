"""Service for discovering relevant channels and sources (OpenAI-assisted)."""
from typing import Dict, List, Any
import asyncio
import logging

import praw

from app.services.alias_helper import AliasHelper
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("app.discovery_service")


class ChannelDiscoveryService:
    """Service for discovering relevant channels/subreddits for products."""

    def __init__(self):
        self.alias = AliasHelper()
        # Use sync PRAW in worker thread to avoid asyncio issues on Windows
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

    async def discover_reddit(self, products: List[str]) -> List[Dict[str, Any]]:
        suggested_subs = await self.alias.suggest_subreddits(products)
        suggested_queries = await self.alias.suggest_reddit_queries(products)

        def _measure_sync() -> List[Dict[str, Any]]:
            aggregated: Dict[str, Dict[str, Any]] = {}

            def bump(sub: str, submission) -> None:
                data = aggregated.setdefault(
                    sub,
                    {
                        "platform": "reddit",
                        "channel_id": sub,
                        "name": f"r/{sub}",
                        "metrics": {"mentions": 0, "avg_score": 0.0, "comments": 0},
                    },
                )
                m = data["metrics"]
                m["mentions"] += 1
                m["avg_score"] += getattr(submission, "score", 0)
                m["comments"] += getattr(submission, "num_comments", 0)

            try:
                # Measure suggested subreddits via recent posts
                for sub in (suggested_subs or [])[:20]:
                    try:
                        s = self.reddit.subreddit(sub)
                        for post in s.new(limit=20):
                            bump(sub, post)
                    except Exception:
                        continue

                # Search suggested queries in r/all
                if suggested_queries:
                    allsub = self.reddit.subreddit("all")
                    for q in suggested_queries[:5]:
                        try:
                            for post in allsub.search(q, sort="new", time_filter="week", limit=80):
                                sub = post.subreddit.display_name
                                bump(sub, post)
                        except Exception:
                            continue
            except Exception:
                return []

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

        return await asyncio.to_thread(_measure_sync)
    
    async def discover(self, products: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Main discovery method that returns results for all platforms."""
        sources: Dict[str, List[Dict[str, Any]]] = {}
        sources["reddit"] = await self.discover_reddit(products)
        return sources
