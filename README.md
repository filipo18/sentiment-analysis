Environment variables
---------------------

Frontend (Vite):

Create a `.env` at the repository root or in the `frontend/` folder with:

```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

API:

See `api/env.example` for available settings (Supabase, Reddit, analysis, limits).

# Radar Pulse AI

A sentiment analysis application with React frontend and FastAPI backend.

## Project Structure

```
radar-pulse-ai/
├── frontend/          # React/TypeScript frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── api/               # FastAPI Python backend
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
└── supabase/          # Database migrations
```

## Getting Started

### Frontend (React/TypeScript)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:8081`

### Backend (FastAPI)

```bash
cd api
pip install -r requirements.txt
python run.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the backend is running, you can access:
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Latest comments: `http://localhost:8000/comments/latest`

## Database

The application uses Supabase as the database. Both frontend and backend connect to the same Supabase instance.

## Features

- **Frontend**: Real-time sentiment analysis dashboard with charts and visualizations
- **Backend**: FastAPI server with endpoints to fetch and analyze Reddit comments
- **Database**: Supabase integration for storing and retrieving sentiment data