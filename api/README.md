# Product Social Sensing API

A FastAPI application that discovers and ingests social media content (Reddit) for product analysis.

## Features

- **Discover**: Find relevant Reddit subreddits for specific products
- **Ingest**: Collect comments and posts from Reddit and store them in Supabase
- **Comments API**: Retrieve stored comments from the database

## Project Structure

This project follows a clean, modular architecture:

```
api/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── env.example                      # Environment variables template
├── README.md                        # Project documentation
├── PROJECT_STRUCTURE.md             # Detailed structure documentation
└── app/                            # Main application package
    ├── __init__.py                 # Package initialization
    ├── config.py                   # Configuration settings
    ├── models.py                   # Pydantic models for API schemas
    ├── database.py                 # Database operations (Supabase)
    ├── services/                   # Business logic services
    │   ├── __init__.py
    │   ├── reddit_service.py       # Reddit API operations
    │   ├── discovery_service.py    # Channel discovery logic
    │   └── ingestion_service.py    # Content ingestion logic
    └── routers/                    # API route handlers
        ├── __init__.py
        ├── health.py               # Health check endpoints
        ├── discovery.py            # Discovery endpoints
        ├── ingestion.py            # Ingestion endpoints
        └── comments.py             # Comments endpoints
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your Reddit API credentials
```

3. Get Reddit API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Create a new app (script type)
   - Copy the client ID and secret

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /health` - Check if the API is running

### Discovery
- `POST /discover` - Discover relevant Reddit channels for products
  ```json
  {
    "products": ["iPhone", "Samsung Galaxy"]
  }
  ```

### Ingestion
- `POST /ingest` - Ingest content from discovered sources
  ```json
  {
    "products": ["iPhone", "Samsung Galaxy"]
  }
  ```

### Comments
- `GET /comments` - Get stored comments
  - Query parameters:
    - `product_name` (optional): Filter by product name
    - `limit` (optional): Number of comments to return (default: 100)
- `GET /comments/brand/{brand_name}` - Get comments by brand
- `GET /comments/recent` - Get most recent comments

## Database Schema

The application uses Supabase with the `main_reddit` table:

- `brand_name`: Brand of the product
- `product_name`: Specific product name
- `comment`: The actual comment text
- `comment_sentiment`: Sentiment analysis result
- `comment_timestamp`: When the comment was posted
- `thread_name`: Title of the Reddit thread
- `upvotes`: Number of upvotes
- `attribute_discussed`: Product attribute being discussed
- `attribute_sentiment`: Sentiment about the attribute

## Architecture Benefits

- **Modular Design**: Clean separation of concerns with dedicated modules
- **Maintainable**: Easy to locate and modify specific functionality
- **Testable**: Services can be unit tested independently
- **Scalable**: Easy to add new services, routers, or models
- **Reusable**: Services can be reused across different routers
- **Configurable**: Centralized settings with environment variable support

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
