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
        """Discover relevant Reddit subreddits for given products."""
        # Get suggested subreddit names from LLM
        suggested_subreddits = await self.alias.suggest_subreddits(products)
        logger.info(f"LLM suggested {len(suggested_subreddits)} subreddits: {suggested_subreddits}")

        def _verify_subreddits() -> List[Dict[str, Any]]:
            results = []
            
            for sub_name in suggested_subreddits:
                try:
                    # Check if subreddit exists
                    subreddit = self.reddit.subreddit(sub_name)
                    
                    # Basic info
                    subscribers = getattr(subreddit, 'subscribers', 0)
                    title = getattr(subreddit, 'title', '')
                    description = getattr(subreddit, 'public_description', '')
                    
                    # Simple score based on subscriber count
                    score = min(subscribers / 10000.0, 1.0)  # Normalize to 0-1
                    
                    results.append({
                        "platform": "reddit",
                        "channel_id": sub_name,
                        "name": f"r/{sub_name}",
                        "score": score,
                        "metrics": {
                            "mentions": 1,  # Placeholder
                            "avg_score": 0,  # Placeholder
                            "comments": 0,  # Placeholder
                            "subscribers": subscribers
                        }
                    })
                    
                    logger.info(f"Verified r/{sub_name}: {subscribers} subscribers")
                    
                except Exception as e:
                    logger.warning(f"Subreddit r/{sub_name} not found or inaccessible: {e}")
                    continue
            
            # Sort by subscriber count (score)
            results.sort(key=lambda x: x["score"], reverse=True)
            logger.info(f"Found {len(results)} valid subreddits")
            
            return results[:settings.MAX_DISCOVERY_RESULTS]

        return await asyncio.to_thread(_verify_subreddits)
    
    async def discover(self, products: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Main discovery method that returns results for all platforms."""
        sources: Dict[str, List[Dict[str, Any]]] = {}
        sources["reddit"] = await self.discover_reddit(products)
        return sources
