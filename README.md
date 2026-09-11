# 🧠 Knowly — Enterprise Document AI Workspace

> **Understand. Analyze. Compare. Act on your documents with AI.**

Knowly is a full-stack enterprise document intelligence platform powered by a **Next.js 16** frontend and a **FastAPI** backend. It offers hybrid semantic search, multi-agent orchestration, deep research, tabular analysis, document comparison, automated workflows, and Stripe-based subscription billing — all in one polished workspace.

---

## 📸 Features at a Glance

| Feature | Description |
|---|---|
| 📄 **Document Ingestion** | Layout-aware parsing for PDF, DOCX, PPTX, XLSX, TXT, and images |
| 💬 **AI Chat** | RAG with citations, page numbers, and bounding box highlights |
| 🔬 **Deep Research** | Multi-step planner for cross-document synthesis |
| 📊 **Tabular Analyst** | Deterministic Pandas execution on structured data |
| 🔀 **Document Comparison** | Diff highlighting and clause-level matrix view |
| 📝 **Report Builder** | Live Markdown editor with Markdown / DOCX / PDF / HTML export |
| ⚙️ **Workflows** | Event-driven pipeline triggers (on upload, schedule, manual) |
| 💳 **Billing** | Free & Pro tiers with Stripe Checkout and quota management |

---

## 🏗️ Architecture

```
Knowly/
├── frontend/          # Next.js 16 (App Router) · React 19 · Tailwind CSS v4 · Radix UI
└── backend/           # FastAPI · SQLAlchemy · Qdrant · BM25 Hybrid Search · APScheduler
```

### Frontend Stack
- **Framework**: Next.js 16 (App Router) + React 19
- **Styling**: Tailwind CSS v4 · Radix UI · Lucide React icons
- **HTTP**: Fetch API with typed route handlers

### Backend Stack
- **API**: FastAPI + Uvicorn (ASGI)
- **Database**: SQLite (dev) / PostgreSQL (prod) via SQLAlchemy 2.0
- **Vector DB**: Qdrant with BM25 Hybrid Search + Contextual Reranking
- **LLMs**: OpenAI, Anthropic, Groq (configurable per tier)
- **Auth**: JWT (python-jose + passlib)
- **Payments**: Stripe SDK
- **Background Tasks**: APScheduler

---

## 🚀 Local Development

### Prerequisites

| Tool | Version |
|---|---|
| Node.js | ≥ 18.x |
| Python | ≥ 3.11 |
| pip / uv | latest |
| Qdrant | Running locally on port 6333 (optional for full vector search) |

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/knowly.git
cd knowly
```

---

### 2. Backend Setup

```bash
cd backend

# Copy and fill in environment variables
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY / ANTHROPIC_API_KEY / GROQ_API_KEY

# Install dependencies
pip install -e .

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- **API Root**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:3000**

---

### 4. Environment Variables

#### Backend (`backend/.env`)

```env
# Required — at least one LLM key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...

# Database (SQLite by default)
DATABASE_URL=sqlite:///./knowly.db

# Vector DB (optional for full search)
QDRANT_URL=http://localhost:6333

# Security
JWT_SECRET=your-secret-key-here

# Stripe (optional for billing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# CORS
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── auth/          # Login / register pages
│   │   ├── billing/       # Subscription & billing UI
│   │   ├── chat/          # AI chat interface
│   │   ├── comparison/    # Document comparison view
│   │   ├── dashboard/     # Main dashboard
│   │   ├── docs/          # Document library
│   │   ├── pricing/       # Pricing page
│   │   ├── reports/       # Report builder
│   │   ├── settings/      # User settings
│   │   ├── workflows/     # Workflow automation
│   │   └── page.tsx       # Landing page
│   ├── components/        # Shared UI components
│   └── lib/               # Utility functions & API clients

backend/
├── app/
│   ├── agents/            # Multi-agent orchestration
│   ├── ingestion/         # Document parsers & chunkers
│   ├── llm/               # LLM abstraction layer
│   ├── models/            # SQLAlchemy ORM models
│   ├── retrieval/         # Qdrant + BM25 retrieval & citations
│   ├── routers/           # FastAPI route handlers
│   ├── schemas/           # Pydantic request/response schemas
│   ├── workflows/         # Workflow runner & scheduler
│   ├── auth.py            # JWT authentication
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py        # DB engine & session factory
│   └── main.py            # FastAPI application entry point
```

---

## ☁️ Deployment

### Frontend → Vercel

The frontend is optimized for one-click Vercel deployment.

#### Option A: Vercel CLI

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy (preview)
vercel

# Deploy to production
vercel --prod
```

#### Option B: Vercel Dashboard (Recommended)

1. Push your code to GitHub / GitLab / Bitbucket
2. Go to [vercel.com/new](https://vercel.com/new)
3. Import the repository and set **Root Directory** to `frontend`
4. Add environment variables (see table below)
5. Click **Deploy**

#### Vercel Environment Variables

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | Your deployed backend URL e.g. `https://api.knowly.app` |

> **Important**: The backend cannot be deployed to Vercel (serverless). Use **Railway**, **Render**, or **Fly.io** for the FastAPI backend.

---

### Backend → Docker / Railway / Render

A `Dockerfile` is included in `backend/`:

```bash
cd backend
docker build -t knowly-backend .
docker run -p 8000:8000 --env-file .env knowly-backend
```

For **Railway**:
1. Create a new project → Deploy from GitHub
2. Set root directory to `backend/`
3. Add all environment variables from `.env.example`
4. Railway auto-detects the Dockerfile and deploys

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend lint
cd frontend
npm run lint
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is proprietary. All rights reserved.

---

<div align="center">
  Built with ❤️ using Next.js, FastAPI, and AI
</div>
