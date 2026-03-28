# CrisisLens - AI Medical Emergency Triage

> Gemini-powered app that converts messy, unstructured real-world inputs into structured, verified, life-saving actions.

Built for **PromptWars** hackathon by Google for Developers.

## What It Does

CrisisLens takes **any combination** of messy inputs:
- Photos of medications, injuries, or medical documents
- Voice recordings describing symptoms
- Free-text descriptions of emergencies

And runs them through **3 AI pipelines**:
1. **INTAKE** (Gemini 2.5 Flash) - Parses multimodal input into structured data
2. **REASON** (Gemini 2.5 Pro) - Deep analysis against medical protocols
3. **VERIFY** (Gemini 2.5 Flash + Google Search Grounding) - Verified action plan

Output: A **structured, verified action plan** with triage level, prioritized actions, confidence scores, and verification sources.

## Google Cloud Services Used

| Service | Purpose |
|---------|---------|
| Vertex AI (Gemini) | Core AI engine - multimodal analysis |
| Google Search Grounding | Verify actions against real medical protocols |
| Cloud Firestore | Persist analysis sessions |
| Cloud Storage | Store uploaded files |
| Cloud Logging | Structured observability |
| Cloud Run | Backend deployment |
| Firebase Hosting | Frontend deployment |

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # Opens on port 3000
```

### Run Tests
```bash
# Backend
cd backend && source .venv/Scripts/activate && pytest -v

# Frontend
cd frontend && npm test
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, google-genai SDK, Pydantic v2
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4
- **Testing**: pytest + pytest-asyncio, Vitest + React Testing Library
- **AI**: Gemini 2.5 Pro + Flash via Vertex AI

## Architecture

```
User Input (text/image/audio)
        │
        ▼
┌─────────────────┐
│  FastAPI Backend │
│                  │
│  Pipeline 1:     │──→ Gemini Flash (parse)
│  INTAKE          │
│                  │
│  Pipeline 2:     │──→ Gemini Pro (reason)
│  REASON          │
│                  │
│  Pipeline 3:     │──→ Gemini Flash + Search
│  VERIFY          │    (grounding)
│                  │
│  ┌─────────────┐ │
│  │ Firestore   │ │  Session storage
│  │ Cloud Store │ │  File uploads
│  │ Cloud Log   │ │  Observability
│  └─────────────┘ │
└─────────────────┘
        │
        ▼
  Verified Action Plan (JSON)
```
