# Radar Pulse AI

A sentiment analysis platform that monitors Reddit discussions about products and provides AI-powered Q&A capabilities.

## Tech Stack

**Frontend:** React, TypeScript, Tailwind CSS, Recharts
**Backend:** FastAPI, Supabase, Weaviate, OpenAI, PRAW

## Prerequisites

- Node.js, Python, Docker
- Reddit API credentials
- OpenAI API key
- Supabase project

## Quick Start

### 1. Setup Backend

```bash
cd api
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp env.example .env
```

**Configure `api/.env`:**
```env
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=ProductSocialSensing/1.0

# Supabase credentials
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI API credentials
OPENAI_API_KEY=your_openai_key

# Weaviate configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your_weaviate_api_key

# Defaults and limits
DEFAULT_PRODUCTS=iPhone16
MAX_COMMENTS_PER_SUBMISSION=50
MAX_SUBMISSIONS_PER_PRODUCT=20
MAX_DISCOVERY_RESULTS=20
TOP_SUBREDDITS_LIMIT=2
ANALYSIS_LIMIT=100

# API metadata
API_TITLE=Product Social Sensing API
API_VERSION=0.1.0
```

### 2. Setup Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

**Configure `frontend/.env`:**
```env
VITE_SUPABASE_PROJECT_ID=your_project_id
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Start Services

```bash
# Terminal 1: Weaviate
cd api && docker compose up -d weaviate

# Terminal 2: Backend
cd api && venv\Scripts\activate && python main.py

# Terminal 3: Frontend
cd frontend && npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Sync Vector Database:**
```bash
curl -X POST "http://localhost:8000/qa/sync?limit=1000"
```

## 🔌 API Endpoints

**Core:** `/health`, `/discover`, `/ingest`, `/comments`
**Q&A:** `/qa/ask`, `/qa/search`, `/qa/sync`, `/qa/stats`

## 🔧 Setup Requirements

**Reddit API:** Create app at https://www.reddit.com/prefs/apps
**Supabase:** Create project and get URL/key
**OpenAI:** Get API key from https://platform.openai.com/account/api-keys

## 🚨 Troubleshooting

- **Weaviate**: Check `docker compose ps` and `curl http://localhost:8080/v1/meta`
- **API**: Verify environment variables and credentials
- **Frontend**: Check console for CORS errors

---

**API Docs:** http://localhost:8000/docs