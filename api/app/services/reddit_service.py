"""Reddit API service for content discovery and ingestion."""
import asyncpraw
import praw
import asyncio
from typing import Dict, List, Any
import logging
from datetime import datetime, timezone
from app.config import get_settings

settings = get_settings()

class RedditService:
    """Service for Reddit API operations."""
    
    def __init__(self):
        """Initialize Reddit clients (async for discovery, sync for ingestion)."""
        self.reddit_async = asyncpraw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        self.logger = logging.getLogger("app.reddit_service")
    
    async def discover_subreddits(self, products: List[str]) -> List[Dict[str, Any]]:
        """Discover Reddit subreddits relevant to the given products.

        Uses sync PRAW via a background thread to avoid Windows asyncio issues.
        """
        print(f"Starting Reddit discovery for products: {products}")

        def _discover_sync() -> List[Dict[str, Any]]:
            aggregated: Dict[str, Dict[str, Any]] = {}
            try:
                subreddit_sync = self.reddit.subreddit("all")
                for product in products:
                    try:
                        for submission in subreddit_sync.search(product, sort="new", time_filter="week", limit=50):
                            sub = submission.subreddit.display_name
                            data = aggregated.setdefault(
                                sub,
                                {
                                    "platform": "reddit",
                                    "channel_id": sub,
                                    "name": f"r/{sub}",
                                    "metrics": {"mentions": 0, "avg_score": 0.0, "comments": 0},
                                },
                            )
                            metrics = data["metrics"]
                            metrics["mentions"] += 1
                            metrics["avg_score"] += getattr(submission, "score", 0)
                            metrics["comments"] += getattr(submission, "num_comments", 0)
                    except Exception as exc:
                        print(f"Query '{product}' search failed: {exc}")
            except Exception as e:
                self.logger.exception(f"PRAW sync discovery failed: {e}")
                print(f"[REDDIT] (sync) discovery failed: {e}")

            # Calculate scores and return ranked results
            results: List[Dict[str, Any]] = []
            for item in aggregated.values():
                metrics = item["metrics"]
                mentions = max(metrics["mentions"], 1)
                metrics["avg_score"] = metrics["avg_score"] / mentions
                item["score"] = float(
                    metrics["mentions"] * 0.6
                    + metrics["avg_score"] * 0.2
                    + metrics["comments"] * 0.2
                )
                results.append(item)
            return sorted(results, key=lambda it: it.get("score", 0), reverse=True)[: settings.MAX_DISCOVERY_RESULTS]

        return await asyncio.to_thread(_discover_sync)
    
    async def get_comments_for_product(self, product: str, subreddit_name: str | None = None) -> List[Dict[str, Any]]:
        """Get comments for a specific product from Reddit.

        Behavior mirrors the reference flow but restricted to a single subreddit:
        - Search within the provided subreddit (or r/all if not provided)
        - Fetch top posts (last week) and most-commented posts (last week)
        - Expand comments with replace_more(limit=4)
        - Collect up to MAX_COMMENTS_PER_SUBMISSION comments per submission
        """
        comments_data: List[Dict[str, Any]] = []

        try:
            target_sub = subreddit_name or "all"
            self.logger.info(f"Reddit fetching for product='{product}' subreddit='{target_sub}'")
            print(f"[REDDIT] product='{product}' subreddit='{target_sub}'")
            # For ingestion we use sync PRAW in a worker thread to avoid Windows asyncio issues
            # Keep this method async to match call sites
            def _fetch_sync() -> List[Dict[str, Any]]:
                out: List[Dict[str, Any]] = []
                try:
                    subreddit_sync = self.reddit.subreddit(target_sub)
                    seen_ids: set[str] = set()

                    def handle_submission(submission) -> None:
                        sid = getattr(submission, "id", None)
                        if sid in seen_ids:
                            return
                        if sid:
                            seen_ids.add(sid)
                        try:
                            submission.comments.replace_more(limit=2)
                            comments_list = submission.comments.list() or []
                            self.logger.info(f"submission='{sid}' comments={len(comments_list)}")
                            print(f"[REDDIT] (sync) submission='{sid}' comments={len(comments_list)}")
                            for c in comments_list[: settings.MAX_COMMENTS_PER_SUBMISSION]:
                                body = getattr(c, "body", None)
                                if not body:
                                    continue
                                out.append(
                                    {
                                        "brand_name": product or "unknown",
                                        "product_name": product,
                                        "comment": body,
                                        "comment_timestamp": datetime.fromtimestamp(getattr(c, "created_utc", 0) or 0, timezone.utc).isoformat(),
                                        "thread_name": getattr(submission, "title", ""),
                                        "upvotes": getattr(c, "score", 0),
                                    }
                                )
                        except Exception as ex:
                            self.logger.warning(f"Failed handling submission '{sid}': {ex}")
                            print(f"[REDDIT] (sync) failed submission '{sid}': {ex}")

                    for submission in subreddit_sync.search(product, sort="top", time_filter="week", limit=5):
                        handle_submission(submission)
                    for submission in subreddit_sync.search(product, sort="comments", time_filter="week", limit=5):
                        handle_submission(submission)
                except Exception as e:
                    self.logger.exception(f"PRAW sync fetch failed: {e}")
                    print(f"[REDDIT] (sync) fetch failed: {e}")
                return out

            return await asyncio.to_thread(_fetch_sync)
        except Exception as e:
            print(f"[REDDIT] Failed to get Reddit comments for product {product}: {e}")
            self.logger.exception(f"Failed to get Reddit comments for product {product}: {e}")
            return []
