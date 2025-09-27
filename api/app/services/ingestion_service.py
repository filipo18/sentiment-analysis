"""Service for ingesting content from various sources."""
from typing import List
import logging
from app.services.reddit_service import RedditService
from app.database import db_service
from app.config import get_settings

class IngestionService:
    """Service for ingesting content from various sources."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.reddit_service = RedditService()
        self.logger = logging.getLogger("app.ingestion_service")
        self.settings = get_settings()
    
    async def run_once(self, products: List[str]) -> None:
        """Run ingestion for the given products."""
        self.logger.info(f"Starting ingestion for products: {products}")
        # Global cleanup: delete all comments before a fresh run
        deleted_total = db_service.delete_all_comments()
        self.logger.info(f"Deleted all existing comments: {deleted_total}")
        await self._ingest_reddit(products)
    
    async def _ingest_reddit(self, products: List[str]) -> None:
        """Ingest Reddit content for the given products."""
        self.logger.info(f"Ingesting Reddit content for products: {products}")
        
        for product in products:
            await self._ingest_reddit_product(product)
    
    async def _ingest_reddit_product(self, product: str) -> None:
        """Ingest Reddit content for a specific product."""
        try:
            # Clean existing comments for this product to avoid duplicates/stale data
            deleted = db_service.delete_comments_for_product(product)
            self.logger.info(f"Product='{product}' deleted_existing={deleted}")
            # Determine the top subreddits from SourceChannel
            top_subreddits = db_service.get_top_reddit_channels(limit=self.settings.TOP_SUBREDDITS_LIMIT) or []
            if not top_subreddits:
                # Fallback to single top or 'all'
                fallback = db_service.get_top_reddit_channel() or "all"
                top_subreddits = [fallback]
            self.logger.info(f"Product='{product}' top_subreddits={top_subreddits}")

            # Fetch and merge comments from each subreddit
            comments_data: List[dict] = []
            for sub in top_subreddits:
                part = await self.reddit_service.get_comments_for_product(product, subreddit_name=sub)
                comments_data.extend(part)
            self.logger.info(f"Product='{product}' fetched_comments={len(comments_data)}")
            
            # Store comments in database
            success_count = 0
            fail_count = 0
            for comment_data in comments_data:
                success = db_service.insert_comment(comment_data)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            print(f"[INGEST] Product='{product}' inserted={success_count} failed={fail_count}")
            self.logger.info(f"Product='{product}' inserted={success_count} failed={fail_count}")
                    
        except Exception as e:
            print(f"[INGEST] Failed to ingest Reddit content for product {product}: {e}")
            self.logger.exception(f"Failed to ingest Reddit content for product {product}: {e}")
