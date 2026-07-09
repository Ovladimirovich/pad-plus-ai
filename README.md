<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <img src="assets/logo.svg" width="500" alt="PAD+ AI">
  </picture>
</p>

<p align="center">
  <strong>Cognitive Pipeline Layer for LLMs</strong>
  <br>
  <em>PAD+ AI adds emotions, memory, autonomy, and meta-cognition to any LLM</em>
</p>

<p align="center">
  <a href="https://pad-plus-ai.onrender.com">
    <img src="https://img.shields.io/badge/Live-Demo-06b6d4?style=flat-square&logo=render&logoColor=white" alt="Live Demo">
  </a>
  <a href="https://pypi.org/project/pad-plus-ai/">
    <img src="https://img.shields.io/pypi/v/pad-plus-ai?style=flat-square&logo=pypi&logoColor=white&color=a855f7" alt="PyPI">
  </a>
  <a href="https://github.com/Ovladimirovich/pad-plus-ai/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/Ovladimirovich/pad-plus-ai/ci-cd.yml?style=flat-square&logo=github&label=CI" alt="CI">
  </a>
  <a href="https://pypi.org/project/pad-plus-ai/">
    <img src="https://img.shields.io/pypi/pyversions/pad-plus-ai?style=flat-square&logo=python&logoColor=white" alt="Python versions">
  </a>
  <a href="https://github.com/Ovladimirovich/pad-plus-ai/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square" alt="License">
  </a>
  <a href="https://github.com/Ovladimirovich/pad-plus-ai/issues">
    <img src="https://img.shields.io/github/issues/Ovladimirovich/pad-plus-ai?style=flat-square" alt="Issues">
  </a>
  <a href="https://github.com/Ovladimirovich/pad-plus-ai/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome">
  </a>
</p>

---

## What is PAD+ AI?

PAD+ AI is an **open-source cognitive architecture** that sits on top of any LLM, transforming it into a self-aware, emotionally-grounded, memory-augmented AI system.

**PAD+ = Pleasure, Arousal, Dominance + Curiosity, Confidence, Social Connection**

Traditional LLMs process requests → generate responses. PAD+ AI adds:

- **Emotions** — the PAD+ model tracks 6 emotional dimensions, decays them over time, and adapts the response style
- **Memory** — 6 types of memory (RAG, episodic, semantic, facts, roots, persona) with consolidation and hygiene
- **Autonomy** — planning, hierarchical goals, dreams (offline memory processing), self-reflection
- **Meta-cognition** — intent routing, truth verification, cognitive health monitoring
- **Safety** — injection protection, anti-loop guard, rate limiting

All running through a 9-stage processing pipeline.

> **Live demo:** https://pad-plus-ai.onrender.com

---

## Screenshots

| Control Center | Chat Interface |
|---|---|
| <img src="assets/screenshots/control-center.png" width="360" alt="Control Center"> | <img src="assets/screenshots/chat.png" width="360" alt="Chat"> |

| X-Ray Observability | Healer Diagnostics |
|---|---|
| <img src="assets/screenshots/xray.png" width="360" alt="X-Ray"> | <img src="assets/screenshots/healer.png" width="360" alt="Healer"> |

---

## Quick Start

### Requirements

- Python 3.10+
- Node.js 18+
- OpenRouter API key (for LLM access)

### Install

```bash
# Backend
pip install pad-plus-ai
# or from source:
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### Configure

```bash
cp .env.example .env
# Edit .env → add your OPENROUTER_API_KEY
```

### Run

```bash
# Windows
.\start.bat

# Manual — Terminal 1 (Backend)
cd backend && uvicorn main:app --reload --port 8080

# Manual — Terminal 2 (Frontend)
cd frontend && npm run dev
```

Open **http://localhost:5174**

---

## Core Capabilities

### 🧠 Memory System

| Type | Description |
|------|-------------|
| **RAG Memory v3.0** | Semantic search via ChromaDB, topic classification, entity extraction, hybrid ranking |
| **Episodic Memory** | Episode storage with timestamps for event recall |
| **Semantic Memory** | General knowledge and concepts |
| **Fact Memory** | Structured facts (subject-predicate-object) |
| **Roots Memory** | Fundamental principles — philosophy, ethics, identity |
| **Persona** | Evolving personality with character traits |
| **Consolidation** | Memory consolidation analog to sleep (offline processing) |
| **Hygiene** | Automatic cleanup: deduplication, pruning, orphan removal |

### 😊 PAD+ Emotion Model

Six-dimensional emotional state that evolves with every interaction:

- **P**leasure — satisfaction with outcomes
- **A**rousal — engagement and alertness
- **D**ominance — sense of control
- **C**uriosity — drive to explore
- **C**onfidence — self-assurance
- **S**ocial Connection — relationship quality

Emotions decay naturally over time and influence response style, tone, and content.

### 🔄 Autonomy System

- **Planner** — formulates independent questions and tasks
- **Hierarchical Planner** — multi-level goals: Goals → Tasks → Actions
- **Dreams** — offline memory processing during idle periods
- **Auto-reflection** — triggered every N dialogues
- **Quality Assessor** — self-evaluation of response quality
- **Knowledge Auto-Updater** — autonomous knowledge graph population

### 🛡️ Safety Layer

- **Injection Protection** — prompt injection defense
- **Anti-Loop Guard** — prevents infinite reasoning loops
- **Rate Limiter** — request throttling per user/session
- **Truth Verification** — fact-checking via Truth Loop

### 🧩 Meta-Cognition

- **Meta Controller** — strategy selection for processing
- **Intent Router** — intent classification for routing
- **Truth Loop** — iterative truth verification
- **Health Monitor** — cognitive health assessment
- **Cognitive Load** — load estimation and management

### 📊 Analytics & Infrastructure

- **Metrics & Dashboard** — usage analytics with visualization
- **Response Cache** — intelligent response caching
- **Session Manager** — session lifecycle management
- **Config Manager** — dynamic system configuration
- **Data Manager** — export/import operations
- **Event Bus** — pub/sub event system

---

## Architecture

### 9-Stage Pipeline

```
User Message
     │
     ▼
┌─────────────┐
│   Safety    │ ← Injection protection, anti-loop
└─────┬───────┘
      ▼
┌─────────────┐
│   Intent    │ ← Intent classification
└─────┬───────┘
      ▼
┌─────────────┐
│  Retrieve   │ ← RAG + Facts + Knowledge Graph
└─────┬───────┘
      ▼
┌─────────────┐
│   Persona   │ ← Personality context + emotion state
└─────┬───────┘
      ▼
┌─────────────┐
│  Generate   │ ← LLM call (OpenRouter / LiteLLM)
└─────┬───────┘
      ▼
┌─────────────┐
│   Truth     │ ← Fact verification
└─────┬───────┘
      ▼
┌─────────────┐
│  Remember   │ ← Store in all memory types
└─────┬───────┘
      ▼
┌─────────────┐
│   Emit      │ ← Events, metrics, WebSocket updates
└─────────────┘
```

### Project Structure

```
pad-plus-ai/
├── backend/
│   ├── core/               # Pipeline executor, safety, intent, meta
│   ├── memory/             # RAG v3.0, episodic, semantic, persona
│   ├── emotion/            # PAD+ emotion model
│   ├── llm/                # LiteLLM provider integration
│   ├── knowledge/          # Knowledge graph (NetworkX)
│   ├── autonomy/           # Planner, hierarchical planner
│   ├── analytics/          # Metrics and analytics
│   ├── api/                # FastAPI routes (145+ endpoints)
│   └── main.py             # Entry point
├── frontend/               # React 18 + Vite + TypeScript
│   └── src/                # Chat, Dashboard, Settings, Effects
├── docs/                   # 18 documentation files
├── tests/                  # Unit + integration tests
└── scripts/                # Utilities
```

---

## API Overview

145+ API endpoints across 11 categories. Full documentation at `/docs` when running (Swagger UI) or in [docs/API.md](docs/API.md).

| Category | Key Endpoints |
|----------|---------------|
| **Auth** | `POST /api/v1/auth/register`, `/login`, `/profile` |
| **Chat** | `POST /api/v1/chat`, `/chat/stream` (SSE) |
| **State** | `GET /api/v1/mind-state` — full system state |
| **Memory** | `GET /api/v1/rag/stats`, `/rag/search`, `/rag/hybrid` |
| **Facts** | `GET /api/v1/facts/stats`, `/facts/search`, `/facts/contradictions` |
| **Emotions** | `GET /api/v1/emotion/state` |
| **Persona** | `GET /api/v1/persona/stats`, `/persona/traits` |
| **Roots** | `GET /api/v1/roots/philosophy`, `/roots/ethics`, `/roots/identity` |
| **Autonomy** | `GET /api/v1/autonomy/status`, `/impulse/status` |
| **Analytics** | `GET /api/v1/analytics/dashboard`, `/analytics/report` |
| **Health** | `GET /api/v1/health`, `/health/report`, `/health/issues` |
| **WebSocket** | `WS /ws` — real-time updates |

---

## Comparison: PAD+ AI vs Alternatives

| Feature | PAD+ AI | LangChain | AutoGen | CrewAI |
|---------|---------|-----------|---------|--------|
| **Emotion model** | ✅ PAD+ (6 dims) | ❌ | ❌ | ❌ |
| **Memory types** | 6 types (RAG, episodic, semantic, facts, roots, persona) | 3 types (buffer, summary, vector) | 1 type (conversation) | 1 type (conversation) |
| **Autonomy** | ✅ Planner + hierarchical + dreams + reflection | ❌ | ✅ Agent autonomy | ✅ Role-based |
| **Pipeline** | ✅ 9-stage deterministic pipeline | ✅ Chain-based | ❌ Sequential | ❌ Sequential |
| **Safety layer** | ✅ Injection + anti-loop + truth verification | ❌ Basic | ❌ | ❌ |
| **Meta-cognition** | ✅ Meta controller + health monitor + cognitive load | ❌ | ❌ | ❌ |
| **Knowledge graph** | ✅ NetworkX with auto-population | ❌ | ❌ | ❌ |
| **Memory consolidation** | ✅ Sleep-like offline processing | ❌ | ❌ | ❌ |
| **Frontend** | ✅ React 18 + Vite + TypeScript | ❌ CLI-only | ❌ CLI-only | ❌ CLI-only |
| **Deployment** | ✅ Render + Docker out of box | ❌ Manual | ❌ Manual | ❌ Manual |
| **API endpoints** | 145+ | Limited | Limited | Limited |

> **PAD+ AI** is designed for developers who want a production-ready cognitive architecture with emotional grounding, rich memory, and autonomous capabilities — not just another LLM wrapper.

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Specification](docs/API.md) | Full REST API reference (1632 lines) |
| [Architecture](docs/ARCHITECTURE.md) | System design and pipeline details |
| [Memory System](docs/MEMORY.md) | RAG v3.0, episodic, semantic, consolidation |
| [Emotion Model](docs/EMOTION.md) | PAD+ model — 6 dimensions |
| [Autonomy](docs/AUTONOMY.md) | Planner, hierarchical planner, dreams |
| [Safety](docs/SAFETY.md) | Injection protection, anti-loop, truth verification |
| [Meta-Cognition](docs/INTENT_ROUTER.md) | Intent routing, meta-controller |
| [Persona](docs/PERSONA.md) | Personality evolution system |
| [Evolution](docs/EVOLUTION.md) | Full system evolution history |
| [Frontend](docs/FRONTEND.md) | React 18 component architecture |
| [Quick Start](QUICKSTART.md) | v4.0 quick start guide |
| [Changelog](CHANGELOG.md) | Release history |

---

## Testing

```bash
# All tests
pytest tests/

# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific components
pytest -m rag
pytest -m autonomy
pytest -m emotion
pytest -m pipeline

# Frontend tests
cd frontend && npm test && cd ..
```

---

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Philosophical Core

> *"Do not anchor knowledge. Question, verify. Every assertion is a hypothesis."*

The ANTI_DIRECTIVE is the philosophical foundation of PAD+ AI — a built-in skepticism that prevents the system from treating any knowledge as absolute truth.

---

## License

[Apache License 2.0](LICENSE) © 2026 PAD+ AI Contributors

---

<p align="center">
  <sub>PAD+ AI — Cognitive Pipeline Layer for LLMs</sub>
  <br>
  <a href="https://pad-plus-ai.onrender.com">Live Demo</a> •
  <a href="https://github.com/Ovladimirovich/pad-plus-ai">GitHub</a> •
  <a href="https://pypi.org/project/pad-plus-ai/">PyPI</a>
</p>
