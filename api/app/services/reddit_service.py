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
    
    async def get_comments_for_product(self, product: str, subreddit_name: str) -> List[Dict[str, Any]]:
        """Get comments for a specific product from Reddit.

        Behavior mirrors the reference flow but restricted to a single subreddit:
        - Search within the provided subreddit
        - Fetch top posts (last week)
        - Expand comments with replace_more(limit=4)
        - Collect up to MAX_COMMENTS_PER_SUBMISSION comments per submission
        """
        comments_data: List[Dict[str, Any]] = []

        try:
            self.logger.info(f"Reddit fetching for product='{product}' subreddit='{subreddit_name}'")
            # For ingestion we use sync PRAW in a worker thread to avoid Windows asyncio issues
            # Keep this method async to match call sites
            def _fetch_sync() -> List[Dict[str, Any]]:
                out: List[Dict[str, Any]] = []
                try:
                    subreddit_sync = self.reddit.subreddit(subreddit_name)
                    seen_ids: set[str] = set()
                    posts_processed = 0
                    total_comments_found = 0

                    def handle_submission(submission) -> None:
                        nonlocal posts_processed, total_comments_found
                        sid = getattr(submission, "id", None)
                        if sid in seen_ids:
                            return
                        if sid:
                            seen_ids.add(sid)
                        try:
                            submission.comments.replace_more(limit=2)
                            comments_list = submission.comments.list() or []
                            comments_added = 0
                            
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
                                comments_added += 1
                            
                            posts_processed += 1
                            total_comments_found += comments_added
                            self.logger.info(f"submission='{sid}' total_comments={len(comments_list)} added={comments_added}")
                        except Exception as ex:
                            self.logger.warning(f"Failed handling submission '{sid}': {ex}")

                    for submission in subreddit_sync.search(product, sort="top", time_filter="week", limit=settings.MAX_POSTS_PER_SUBREDDIT): # finds posts matching product
                        handle_submission(submission)
                    
                    # Log summary statistics
                    self.logger.info(f"Reddit search completed: product='{product}' subreddit='{subreddit_name}' posts_processed={posts_processed} total_comments={total_comments_found}")
                except Exception as e:
                    self.logger.exception(f"PRAW sync fetch failed: {e}")
                return out

            return await asyncio.to_thread(_fetch_sync)
        except Exception as e:
            self.logger.exception(f"Failed to get Reddit comments for product {product}: {e}")
            return []
