# PrismAI Design Document

## 1. Document Control

- Product: PrismAI - Autonomous Content Factory
- Version: 2.0
- Last updated: 2026-04-07
- Status: Active implementation-aligned design
- Audience: Engineers, reviewers, technical stakeholders, maintainers

## 2. Executive Summary

PrismAI converts one source input into a multi-channel campaign draft using a 3-agent pipeline:

1. Researcher extracts structured facts and ambiguity risks from raw source material.
2. Copywriter generates blog, social, and email drafts from the researcher output.
3. Editor audits quality and either approves or requests revisions.

The system is built as a FastAPI backend with a Next.js frontend that streams pipeline events over Server-Sent Events (SSE) for a real-time "agent room" experience.

## 3. Problem Statement

Marketing teams repeatedly rewrite the same source content into different channel formats. This creates:

- Creative burnout
- Inconsistent message quality
- Hallucination risk and factual drift
- Slow campaign turnaround

PrismAI addresses this by turning one source document into a coordinated, reviewable, exportable campaign kit.

## 4. Goals and Non-Goals

### 4.1 Goals

- Generate three coordinated outputs from one source:
  - Blog draft
  - 5-post social set
  - Email draft
- Preserve factual consistency using a "Source of Truth"
- Support iterative correction loops with explicit editor feedback
- Provide real-time execution telemetry in UI
- Support local and cloud copywriter runtime modes
- Export campaign outputs as a zip bundle

### 4.2 Non-Goals (Current Version)

- No persistent campaign history storage
- No vector semantic retrieval layer in production path
- No multi-tenant auth or role-based access control
- No asynchronous job queue (single-request lifecycle)
- No formal metrics pipeline (logs and UI status only)

## 5. Scope

### In Scope

- End-to-end campaign generation pipeline
- Channel-level regeneration
- Runtime failover from local copywriter to cloud copywriter
- UI state updates from streamed backend events
- Campaign zip export

### Out of Scope

- Database-backed campaign memory
- Enterprise governance policies and approvals
- Deep CMS integrations
- Prompt management UI

## 6. System Context and Flow

### 6.1 High-Level Flow

1. User submits source material and mode from frontend.
2. Frontend calls backend `/api/generate-stream`.
3. Backend executes:
   - Researcher node
   - Copywriter node
   - Editor node
   - Optional rewrite loops (max 4 revision cycles)
4. Backend streams per-node events and state snapshots to frontend.
5. Frontend updates agent statuses, chat feed, and output panels.
6. User can approve/regenerate by channel.
7. User exports campaign artifacts via `/api/export-campaign`.

### 6.2 Architectural Pattern

- Pattern: Stateful multi-agent orchestration with deterministic control loop
- Orchestration style: Pipeline with conditional revision loop
- Delivery style: Request-response + SSE for progress

## 7. Functional Requirements

### FR-1: Source Ingestion

- Accept source text from UI.
- Build initial graph state with required defaults.

### FR-2: Researcher Agent

- Extract core facts, value proposition, and target audience.
- Produce ambiguity flags.
- Build normalized Source of Truth text block.
- Fall back to local extraction if model output fails.

### FR-3: Copywriter Agent

- Generate blog, social, and email payload as strict JSON.
- Enforce channel shape and structure constraints.
- Support both local and cloud runtime modes.
- Support channel-specific regeneration.
- Fall back to deterministic templates on malformed or failed generation.

### FR-4: Editor Agent

- Compare drafts against Source of Truth.
- Approve or reject with actionable feedback.
- Trigger rewrite loop until approved or revision cap reached.

### FR-5: Streaming and Observability in UI

- Stream node start/update/revision/end/error events.
- Render status transitions and chat feed in real time.

### FR-6: Export

- Export source_of_truth, blog, social, and email into a zip.

## 8. Non-Functional Requirements

- Reliability: graceful degradation during model/network errors
- Latency: progressive SSE updates during long-running generation
- Usability: human-readable feedback and regeneration controls
- Portability: local dev on Windows/macOS/Linux
- Maintainability: typed state contracts and separable agents

## 9. Component Design

## 9.1 Backend

### Framework and API Layer

- FastAPI application with CORS enabled
- Primary endpoints:
  - `GET /`
  - `POST /api/generate`
  - `POST /api/generate-stream`
  - `POST /api/regenerate-channel`
  - `POST /api/export-campaign`

### State Model

GraphState fields include:

- source_material
- source_of_truth
- ambiguity_flags
- target_audience
- value_proposition
- draft_copy
- social_draft
- email_draft
- editor_feedback
- is_approved
- revision_count
- copywriter_mode (`local` or `groq`)
- copywriter_runtime_note

### Orchestration

- Declared graph: researcher -> copywriter -> editor with conditional loop
- Runtime control: explicit loop in backend endpoint logic with max revision cap
- Final-attempt safety: force approval when maximum revisions reached

## 9.2 Agent Design

### Agent 1: Researcher

- Model: Gemini 2.5 Flash (cloud)
- Output contract:
  - core_facts[]
  - target_audience
  - value_proposition
  - ambiguity_flags[]
- Robust parsing:
  - code-fence stripping
  - JSON fragment recovery
- Fallback behavior:
  - heuristic extraction from source text
  - ambiguity pattern checks (vague claims, timeline ambiguity, pricing ambiguity)

### Agent 2: Copywriter

- Runtime modes:
  - Local: Ollama `llama3:8b-instruct-q4_K_M`
  - Cloud: Groq with default `llama-3.1-8b-instant`
- Output contract: strict JSON with keys `blog`, `social`, `email`
- Post-generation enforcement:
  - Blog constrained to 400-600 words with paragraph-safe trimming/extension
  - Social constrained to exactly 5 distinct LinkedIn-style posts
  - Email normalized to subject/salutation/body/signoff shape
- Recovery strategy:
  - self-repair prompt for malformed JSON
  - deterministic fallback drafts if still invalid
  - local-unreachable failover to Groq
  - Groq 429 handling with Retry-After aware backoff

### Agent 3: Editor

- Model: Gemini 2.5 Flash (cloud)
- Decision contract:
  - Must start with `APPROVE` or `REJECT`
- Rejection path:
  - Returns detailed feedback used by copywriter in next revision cycle

## 9.3 Frontend

- Framework: Next.js App Router
- State management: React hooks (`useCampaign`)
- Data transport:
  - Stream generation via SSE from `/api/generate-stream`
  - Channel regeneration via `/api/regenerate-channel`
  - Export via `/api/export-campaign`
- UX patterns:
  - agent status indicators
  - real-time chat feed
  - tabbed channel review
  - channel-level regenerate/approve actions

## 10. API Contract Summary

### 10.1 `POST /api/generate-stream`

Request:

- source_material: string
- copywriter_mode: `local` | `groq`

SSE message types:

- node_start
- node_update
- revision
- end
- error

### 10.2 `POST /api/regenerate-channel`

Request includes:

- channel (`blog` | `social` | `email`)
- source_of_truth
- current drafts and context fields
- copywriter_mode

Response includes updated channel content and copywriter runtime metadata.

### 10.3 `POST /api/export-campaign`

Response is a zip containing:

- source_of_truth.md
- blog_draft.md
- social_thread.txt
- email_teaser.txt

## 11. Tech Stack Chosen and Rationale

### Backend

- Python 3 + FastAPI
- LangGraph + LangChain ecosystem
- Uvicorn for serving

Why:

- Fast integration with model SDKs
- Clean async support for streaming endpoints
- Strong ecosystem for agent orchestration

### Frontend

- Next.js, React, TypeScript
- Tailwind-based styling and custom visual components

Why:

- Rapid UI composition for real-time dashboards
- Strong TypeScript contracts for streamed state handling

### Models

- Researcher and Editor: Gemini 2.5 Flash
- Copywriter local mode: Ollama `llama3:8b-instruct-q4_K_M`
- Copywriter cloud mode: Groq Llama-family model

Why:

- Gemini 2.5 Flash balances speed and extraction/review quality for analytical tasks.
- Local Ollama mode enables privacy-first/offline-friendly operation where available.
- Groq cloud mode provides resilient fallback and generally faster hosted inference.

### Data Layer

- No persistent database in current release.
- No vector database in current release.

Why:

- Current workflow is single-session and can derive outputs directly from provided source material.
- Avoiding a vector DB reduces operational complexity and cost for this phase.
- Retrieval augmentation can be introduced later if cross-document memory and semantic search become required.

## 12. Trade-offs Made

### 12.1 No Vector DB (Yet)

- Decision: skip Pinecone/Weaviate/Chroma in V1.
- Benefit: lower complexity, no embedding pipeline, no index management.
- Cost: no semantic retrieval across historical campaigns and no reusable memory layer.

### 12.2 No Persistent SQL/NoSQL Store

- Decision: process state in-memory per request.
- Benefit: simple deployment and fewer failure points.
- Cost: no historical audit trail and no durable campaign snapshots.

### 12.3 SSE Instead of WebSocket

- Decision: one-way server-to-client streaming for progress updates.
- Benefit: simpler infra and implementation for linear status events.
- Cost: no bidirectional channel over same connection.

### 12.4 Dual Runtime for Copywriter

- Decision: local model + cloud failover.
- Benefit: privacy option with reliability fallback.
- Cost: higher branching complexity and more runtime edge cases.

### 12.5 Fixed Revision Cap

- Decision: max 4 revision cycles.
- Benefit: bounded runtime and cost.
- Cost: may accept "good enough" output when strict approval is not reached earlier.

## 13. Edge Case Handling

| Edge case | Detection | Handling |
|---|---|---|
| Researcher returns invalid JSON | JSON parse failure | Local fallback extraction builds Source of Truth |
| Gemini connectivity/TLS issues | exception text checks | Graceful fallback result instead of request failure |
| Copywriter malformed output | strict parser + key checks | self-repair prompt, then deterministic fallback drafts |
| Social output duplicates | normalized text dedupe | enforce exactly 5 distinct posts with unique templates |
| Blog too short/long | word count validation | paragraph-safe extension/trimming to 400-600 range |
| Email missing structure | structure checks | auto-normalize subject/salutation/body/signoff |
| Local Ollama unavailable | connection error signatures | automatic failover to Groq mode |
| Groq 429 rate limit | HTTP 429 + Retry-After parsing | wait and retry with configurable backoff |
| Groq auth/forbidden errors | HTTP 401/403 | fallback drafts + runtime notes |
| Repeated rejections | revision_count reaches cap | force-approval safeguard with explicit note |
| SSE partial chunk parsing | event framing logic in frontend | buffer-and-split on `\n\n` to avoid dropped events |

## 14. Security and Privacy Considerations

- Secrets loaded from environment variables (`GEMINI_API_KEY`, `GROQ_API_KEY`).
- CORS currently allows all origins for local development convenience.
- Source content may be sent to cloud providers in cloud mode.
- Local mode reduces external data transfer but depends on host Ollama setup.

Recommended hardening for production:

- Restrict CORS origins
- Add authn/authz for API routes
- Add request size limits and abuse throttling
- Add structured redaction in logs

## 15. Performance and Scalability

Current characteristics:

- Single-request synchronous orchestration with async wrappers in endpoints
- Suitable for small to medium interactive loads
- Runtime depends on LLM latency and revision count

Future scaling options:

- Move generation to background job queue
- Add durable state store and request id tracking
- Add horizontal worker pool for campaign executions

## 16. Reliability and Recovery

- Multi-layer fallback strategy in copywriter and researcher
- Runtime notes surfaced to UI for transparent failover messaging
- Defensive parsing and normalization to keep output usable

## 17. Browser and UX Compatibility Notes

- Core generation functionality is browser-agnostic.
- Some advanced visual effects are tuned for Chromium engines.
- Design should retain functional behavior even when visual effects degrade.

## 18. Testing Strategy

Recommended test matrix:

- Unit tests:
  - parser and normalizer functions in copywriter/researcher
  - editor decision parsing
- Integration tests:
  - `/api/generate`, `/api/generate-stream`, `/api/regenerate-channel`, `/api/export-campaign`
- Resilience tests:
  - simulate local model outage
  - simulate Groq 429/401/403
  - malformed model outputs
- Frontend tests:
  - SSE event parsing with partial chunks
  - state transitions and channel actions

## 19. Deployment and Configuration

### Required environment variables

- Backend:
  - GEMINI_API_KEY
  - GROQ_API_KEY (for cloud copywriter mode)
  - GROQ_MODEL (optional override)
  - GROQ_RATE_LIMIT_RETRIES (optional)
  - GROQ_RATE_LIMIT_WAIT_SECONDS (optional)
- Frontend:
  - NEXT_PUBLIC_BACKEND_API_URL (recommended for direct SSE target)
  - BACKEND_API_URL (rewrite destination)

### Runtime dependencies

- Local copywriter mode requires Ollama runtime and model availability.

## 20. Known Limitations

- No durable campaign history
- No vector retrieval augmentation
- No user authentication
- Limited structured telemetry and metrics
- Visual design includes effects with uneven browser support

## 21. Future Enhancements

- Introduce campaign persistence and audit trail
- Add optional vector retrieval for multi-document memory
- Add policy-based editorial rules and safety classifiers
- Add retry budget telemetry and distributed tracing
- Add full browser compatibility mode toggle for visual components

## 22. Conclusion

PrismAI currently provides a practical and resilient multi-agent content generation pipeline with real-time feedback and strong fallback behavior. The architecture deliberately optimizes for rapid delivery, operational simplicity, and graceful degradation. The next phase should focus on persistence, governance, and scale while preserving the current reliability patterns.
