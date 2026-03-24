# Design Document: Autonomous Content Factory

## 1. System Objective
To build an AI-powered system that autonomously processes a "Source Document" through specialized AI agents to generate a coordinated marketing campaign (blog, social thread, email), while ensuring factual accuracy, creative tone and human-in-the-loop control.

## 2. Tech Stack Chosen
### Orchestration: LangGraph (Stateful Multi-Agent Workflows)
- **Why**: Allows complex, cyclic graphs (e.g. the Editor rejecting a Copywriter's draft and routing it back for regeneration). Superior to linear LangChain chains for robust, agentic workflows.

### AI Models: Hybrid Cloud + Local
- **Agent 1 (Researcher) & Agent 3 (Editor)**: Google Gemini 1.5 Flash (via API).
  - *Why*: Large context window, fast extraction capabilities and low local hardware cost.
- **Agent 2 (Creative Copywriter)**: Llama-3-8B-Instruct (Local via Ollama).
  - *Why*: Provides creative control, entirely private and showcases the ability to integrate local, quantized open-source models seamlessly.

### Backend: FastAPI (Python)
- **Why**: Python is the industry standard for AI/LangGraph integration. FastAPI provides fast asynchronous execution and natural support for WebSockets/Server-Sent Events (SSE) to stream agent logs to the frontend.

### Frontend: Next.js + Tailwind CSS
- **Why**: A React-based framework that allows rapid, responsive UI development. Perfect for building dashboards with real-time data streaming.

### Deployment: Docker-Compose
- **Why**: Containerizes the Web App (Frontend + Backend) for standard, one-command deployment across any OS.

## 3. Trade-offs Made
- **Local LLM Outside of Docker**: Rather than containerizing Ollama alongside the web app, we opted to instruct the user to run Ollama natively on their host machine.
  - *Trade-off*: Adds one minor manual pre-requisite for the user (downloading Ollama natively).
  - *Benefit*: Bypasses complex and fragile GPU-passthrough driver issues entirely (especially on Windows WSL2 or macOS), guaranteeing that the app will run smoothly on the user's machine without crashing. This vastly improves deployability.
- **Stateless Execution vs. Database**: For this iteration, we keep the AI workflow mostly memory-stateful during the session. We deliberately avoided implementing a heavy database like PostgreSQL to keep the deployment ultra-lightweight and focused strictly on the AI agent coordination.

## 4. Edge Case Handling
- **Hallucinations**: Mitigated by our dedicated "Editor-in-Chief" Agent. If the Copywriter invents a feature not found in the established "Source of Truth," the Editor catches it, rejects the draft and forces an automatic regeneration.
- **Unexpected/Messy Source Data**: Agent 1 (Researcher) uses Gemini 1.5 Flash specifically to sanitize and structure raw input into a clean JSON/Markdown schema before it reaches the other creative agents.
- **API Errors**: Try/Catch blocks and fallback retries will be implemented around LangGraph node executions to ensure the pipeline doesn't crash on a single API timeout.
