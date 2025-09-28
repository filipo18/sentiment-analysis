# Radar Pulse AI

A sentiment analysis platform that monitors Reddit discussions about products and provides AI-powered Q&A capabilities.

## 🚀 Features

- **Real-time Sentiment Analysis**: Track consumer sentiment with interactive charts
- **Product Discovery**: Find relevant Reddit channels for any product
- **Content Ingestion**: Automatically collect and analyze Reddit comments
- **AI-Powered Search**: Semantic search through comments using vector database
- **Natural Language Q&A**: Ask questions about your data and get AI-generated answers

## 🏗️ Architecture

```
radar-pulse-ai/
├── frontend/          # React/TypeScript frontend
├── api/               # FastAPI Python backend
├── supabase/          # Database migrations
└── docker-compose.yaml # Weaviate vector database
```

## 🛠️ Tech Stack

**Frontend:** React, TypeScript, Tailwind CSS, Recharts
**Backend:** FastAPI, Supabase, Weaviate, OpenAI, PRAW

## 📋 Prerequisites

- Node.js, Python, Docker
- Reddit API credentials
- OpenAI API key
- Supabase project

## 🚀 Quick Start

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
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
```

### 2. Setup Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

**Configure `frontend/.env`:**
```env
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

## 📊 Usage

1. **Discover Products**: Find relevant Reddit channels for products
2. **Ingest Content**: Collect and analyze Reddit comments
3. **View Analytics**: Check sentiment dashboard with real-time charts
4. **Search & Q&A**: Use semantic search or ask natural language questions

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

- **Weaviate**: Check `docker compose ps` and `curl http://localhost:8082/v1/meta`
- **API**: Verify environment variables and credentials
- **Frontend**: Check console for CORS errors

---

**API Docs:** http://localhost:8000/docs