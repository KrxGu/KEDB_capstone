# KEDB Platform

Enterprise knowledge database with AI-powered incident resolution. Captures symptoms, solutions, and execution steps with full audit trails and workflow management.

## Architecture

**Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + pgvector  
**Search:** Meilisearch (lexical) + pgvector (semantic)  
**Queue:** Redis + RQ for async workers  
**AI:** OpenAI/Anthropic integration with citation tracking

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                        │
│                    (Web UI / API Clients)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CRUD API    │  │  Search API  │  │  Agent API   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────-┬──────┘      │
│         │                 │                  │             │
│  ┌──────▼─────────────────▼──────────────────▼───────┐     │
│  │            Service Layer + Auth                   │     │
│  └──────┬─────────────────┬──────────────────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼─────────────┘
          │                 │                  │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐
    │PostgreSQL │    │Meilisearch│    │   Redis     │
    │+ pgvector │    │  (BM25)   │    │   (Queue)   │
    └───────────┘    └───────────┘    └──────┬──────┘
                                             │
                                      ┌──────▼──────-─┐
                                      │  RQ Workers   │
                                      │(Async Tasks)  │
                                      └───────────────┘
```

### Data Flow: AI Agent Suggestions

```
User Query → Agent API
      │
      ├─→ Semantic Search (pgvector cosine similarity)
      │   └─→ Top-K entries by embedding distance
      │
      ├─→ Lexical Search (Meilisearch BM25)
      │   └─→ Keyword matches with filters
      │
      └─→ Hybrid Results
          │
          ├─→ Cross-encoder Re-ranking
          │   └─→ Score recalculation for precision
          │
          └─→ LLM Synthesis (OpenAI/Anthropic)
              ├─→ Citation extraction (entry_id/solution_id)
              ├─→ Policy check (RBAC enforcement)
              └─→ Response with evidence + scores
```

### Database Entity Relationships

```
Entry ──┬─→ EntrySymptom (1:N)
        ├─→ EntryIncident (1:N)
        ├─→ EntryEmbedding (1:N)
        ├─→ Solution (1:N)
        │   ├─→ SolutionStep (1:N)
        │   └─→ SolutionEmbedding (1:N)
        ├─→ EntryTag (M:N) ←─→ Tag
        ├─→ Review (1:N)
        │   └─→ ReviewParticipant (1:N)
        └─→ AuditLog (1:N)

AgentSession ──┬─→ AgentCall (1:N)
               ├─→ AgentSuggestion (1:N)
               └─→ PolicyDecision (1:N)
```

## Core Features

**Entry Management**
- Workflow states: Draft → InReview → Published → Retired/Merged
- Multi-solution support with ordered execution steps
- Symptom tracking and incident linking (PagerDuty, Opsgenie)

**AI Agent**
- `/agent/suggest` - Returns cited recommendations with evidence scores
- `/agent/run` - Guarded tool execution with RBAC policy enforcement
- Token usage and cost tracking per session

**Search**
- Dual retrieval: BM25 lexical + vector semantic search
- Cross-encoder re-ranking for precision
- 3072-dimension embeddings (text-embedding-3-large)

**Governance**
- Multi-participant review workflow
- Complete audit logs with JSON diffs
- Analytics: MTTR deltas, adoption metrics, content health

## Database Schema

21 tables across 8 model files:
- Core: entries, solutions, solution_steps, tags
- Embeddings: entry_embeddings, solution_embeddings
- Agent: agent_sessions, agent_calls, agent_suggestions, policy_decisions
- Workflow: reviews, review_participants
- Audit: audit_logs, suggestion_events
- Utilities: prompts, attachments, synonyms

## Setup

**Prerequisites**
- Python 3.13+ (3.14 not yet supported due to asyncpg)
- Poetry 2.2+
- Docker Desktop

**Quick Start (Automated)**

```bash
# Run the automated setup script
chmod +x setup_phase_a.sh
./setup_phase_a.sh
```

This script will:
1. Install Python dependencies via Poetry
2. Start Docker services (Postgres, Redis, Meilisearch)
3. Enable pgvector extension
4. Run database migrations
5. Verify installation

**Manual Installation**

```bash
# Start infrastructure
docker compose -f deploy/docker-compose.yml up -d

# Install dependencies
cd backend
poetry install

# Run migrations
poetry run alembic upgrade head

# Start API
poetry run uvicorn app.main:app --reload --port 8080
```

**Database Services**
- PostgreSQL: localhost:5432 (kedb/kedb/kedb)
- Redis: localhost:6379
- Meilisearch: localhost:7700

## Project Structure

```
backend/
  app/
    models/       # SQLAlchemy ORM models
    api/          # FastAPI endpoints
    agent/        # AI agent logic
    search/       # Search integrations
    services/     # Business logic
    workers/      # Background jobs
  alembic/        # Database migrations
  tests/          # Test suite

deploy/
  docker-compose.yml

plan/
  # Architecture diagrams and specs
```

## Development Status

Phase A (Bootstrap) - Complete
- Database schema and migrations
- Docker infrastructure
- Health checks and testing

Next phases: CRUD endpoints, search integration, AI agent implementation, workflow automation, analytics dashboard.
