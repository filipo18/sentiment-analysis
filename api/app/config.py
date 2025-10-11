"""Configuration settings for the application."""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    # Supabase configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://aqrtbnzjephixlekcmsr.supabase.co")
    # Prefer SUPABASE_KEY env; allow SUPABASE_ANON_KEY for compatibility
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    
    # Reddit configuration (support both upper/lower env var names)
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID") or os.getenv("reddit_client_id", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET") or os.getenv("reddit_client_secret", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT") or os.getenv("reddit_user_agent", "ProductSocialSensing/1.0")
    
    # Default products for testing (comma-separated string in env)
    DEFAULT_PRODUCTS: List[str] = [p.strip() for p in (os.getenv("DEFAULT_PRODUCTS", "iPhone16").split(",")) if p.strip()]
    
    # API settings
    API_TITLE: str = os.getenv("API_TITLE", "Product Social Sensing API")
    API_VERSION: str = os.getenv("API_VERSION", "0.1.0")
    
    # Ingestion/Discovery settings
    MAX_COMMENTS_PER_SUBMISSION: int = int(os.getenv("MAX_COMMENTS_PER_SUBMISSION", "50"))
    MAX_DISCOVERY_RESULTS: int = int(os.getenv("MAX_DISCOVERY_RESULTS", "20"))
    TOP_SUBREDDITS_LIMIT: int = int(os.getenv("TOP_SUBREDDITS_LIMIT", "2"))
    ANALYSIS_LIMIT: int = int(os.getenv("ANALYSIS_LIMIT", "100"))


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
