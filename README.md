# Project Title

PrismAI - Autonomous Content Factory

## Live Demo

- https://prism-ai-autonomous-content-factory-five.vercel.app/

## The Problem

Marketing teams often need to transform one source document into multiple channel-ready assets, but manual drafting is slow and inconsistent. The same product details can be interpreted differently across blog, social, and email formats, which creates quality gaps and rework. Teams need a faster way to generate consistent campaign content while still preserving editorial review.

## The Solution

PrismAI is a multi-agent content generation system that turns a single source input into coordinated campaign drafts. A researcher agent extracts structured facts, a copywriter agent generates channel-specific content, and an editor agent reviews quality with iterative refinement. The app provides a Next.js dashboard and FastAPI backend, with support for cloud and local LLM runtimes.

## Tech Stack

- Programming languages: Python, TypeScript, JavaScript
- Frontend frameworks and UI: Next.js (App Router), React, Tailwind CSS
- Backend frameworks and orchestration: FastAPI, LangGraph, LangChain
- AI and model runtimes: Google Gemini API (gemini-2.5-flash), Groq API, Ollama (llama3:8b-instruct-q4_K_M)
- Databases: No persistent database is used in the current version
- APIs and third-party tools: Uvicorn, python-dotenv, Docker Compose

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Ajay-Krishna00/PrismAI-_-Autonomous-Content-Factory
cd PrismAI
```

### 2. Backend setup (Python)

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env` and set keys:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

If you want to use local model mode, install Ollama and pull the model:

```bash
ollama run llama3:8b-instruct-q4_K_M
```

### 3. Frontend setup (Next.js)

```bash
cd ../frontend
npm install
```

### 4. Run the project locally

Start backend (Terminal 1):

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Start frontend (Terminal 2):

```bash
cd frontend
npm run dev
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

### 5. Optional Docker run

```bash
docker-compose up --build
```

## Sample Input

You can use the sample product source file at [sample_product.md](sample_product.md), or provide any source material you prefer (product brief, URL content, launch notes, etc.).

