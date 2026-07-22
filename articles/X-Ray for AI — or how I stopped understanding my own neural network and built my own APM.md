---
title: X-Ray for AI — or how I stopped understanding my own neural network and built my own APM
published: false
description: I built a modular cognitive architecture around LLMs. Then I stopped understanding my own program. Here is how I built an observability library that shows what happens inside an AI pipeline — and why it is not "just another OpenTelemetry wrapper."
tags: observability, tracing, python, opensource
series: PAD+ AI
cover_image: https://raw.githubusercontent.com/Ovladimirovich/pad-plus-ai/main/screenshots/research_microscope.png
---

**I no longer understood my own program.**

Let me show you exactly when it happened.

A user asked a perfectly ordinary question. Something like *"Summarize our discussion about neural architecture search."* The answer looked correct. Fluent. Polished.

But later I discovered that the response had completely bypassed Semantic Memory because one span silently failed. The system had answered from raw conversation history alone — no long-term knowledge, no personal context, no verified facts.

The logs showed nothing unusual.

That is when I realized I was not debugging a program anymore. I was debugging a process I could not see.

[Previously](https://dev.to/_a9de0f38ed294cfb7e5e/building-a-modular-cognitive-architecture-around-modern-language-models-2lc1), I wrote about building PAD+ AI — a modular cognitive architecture that routes requests through a structured pipeline instead of throwing a prompt at an LLM. Intent analysis. Memory retrieval. Emotional context. Personality. Verification.

That system works. But somewhere between millions of test runs and growing complexity, I hit a wall.

---

## The Shape of the Problem

Most AI applications follow a simple pattern:

```
Request → Prompt → LLM → Response
```

That shape is easy to debug. Add memory, RAG, knowledge graphs, emotion models, multiple verification passes, and persona evolution, and the shape changes to something far more complex. Now you see the input. You see the output. Everything in between is a black box.

You cannot answer basic questions:

- Which components participated in this response?
- In what order did they execute?
- Where did the 12-second delay come from?
- Did any step silently fail?

In my case, the answer to the last question was *yes* — and I had no way of knowing which one or why.

---

## Logging vs. Tracing: Why the Distinction Matters

The first instinct is to add more logs. I tried that. The logs grew. The understanding did not.

Here is the fundamental difference:

| Logging | Tracing |
|---------|---------|
| Individual events | Complete execution path |
| Flat sequence | Hierarchical structure |
| Timestamp tells *when* | Causality tells *why* |
| Difficult to reconstruct | Full reconstruction on demand |
| Passive recording | Active structural capture |

A log says: *"Event X occurred at time T."*

A trace says: *"Here is the complete path the system took to reach this result, with all dependencies, timings, and causal relationships."*

That difference makes it possible to reconstruct the full processing picture — days or even weeks later. It also makes it possible to answer the question that logs cannot: *Did every step that was supposed to happen actually happen?*

---

## How Traces Changed Everything

I stopped looking at individual events and started looking at execution paths. Each user request became a **Trace**. Inside it, each operation became a **Span**.

The pipeline that was invisible became visible:

```
┌─ Trace ──────────────────────────────────┐
│                                           │
│  Safety → Intent → RAG                    │
│                   ↓                       │
│           Knowledge Graph                  │
│                   ↓                       │
│           Semantic Memory                  │
│                   ↓                       │
│           Persona → Generate → Truth Loop  │
│                                  ↓        │
│                          Response Guard    │
│                                           │
└───────────────────────────────────────────┘
```

This is not a metaphor. Every phase has a start time, end time, status, parent span, and optional error context. You can watch it execute in real time through a WebSocket endpoint:

![AI Under Microscope](https://raw.githubusercontent.com/Ovladimirovich/pad-plus-ai/main/screenshots/research_microscope.png)

Once the structure was there, observability stopped being a nice-to-have and became part of the architecture itself.

---

## The Question Everyone Asks: Why Not OpenTelemetry?

It is the first comment on every observability post, so let me answer it directly.

OpenTelemetry is excellent at answering the question: *"What happened inside my infrastructure?"*

X-Ray was designed to answer a different question: *"What happened inside the cognitive process itself?"*

Its spans represent reasoning stages rather than network requests. Its audit validates causal chains rather than distributed service calls. Its replay reconstructs cognitive execution instead of infrastructure metrics.

You can absolutely use OpenTelemetry for AI observability. Many teams do. But I wanted something that treats a reasoning pipeline the way APM tools treat a request lifecycle — with the assumption that execution has a *structure* worth preserving, not just events worth logging.

That difference became the foundation of the project.

---

## What X-Ray Looks Like Today

X-Ray is mature enough to support production workloads inside PAD+ AI. Its job is not to manage the application or make decisions. Its job is to record execution with enough fidelity that you can reconstruct any request hours or days later.

**Capabilities that matter in practice:**

- **Trace/Span model** with parent-child relationships and causal depth tracking
- **Transparent trace_id propagation** across service boundaries
- **FastAPI middleware** integration (one decorator, zero config)
- **Persistence to disk** — every completed trace is saved as JSON; on restart, all traces are recovered; active traces become `interrupted` with all spans preserved
- **Operation modes:** `live`, `shadow`, `readonly`, `disabled`
- **Integrity audit** — automated validation that every span has a valid parent and no causal chain is broken
- **JSON/CSV export** for external analysis

The directory layout after a day of production use:

```
trace_store/
├── traces/{trace_id}.json
├── spans/{trace_id}/span_{id}.json
├── index.json
├── archive/
└── quarantine/    # Auto-detected corruption
```

It is a flight recorder, not a dashboard. The value is not real-time alerts. The value is that when something goes wrong, you have the complete picture — not a pile of log lines.

---

## The Integration Story

Adding X-Ray to a FastAPI application takes a few minutes. The middleware extracts propagation context, creates spans around external calls, and persistence works out of the box.

I will not paste the full code here — the repository has working examples and a quick-start guide. The point is that the integration surface is minimal because the library assumes nothing about the application. It only needs to know when a trace starts, when spans open and close, and where to store the result.

Everything else — the structure, the hierarchy, the causal links — is derived from those three signals.

---

## Watching It Live

X-Ray is running in production as part of PAD+ AI, deployed on Render.

👉 [pad-plus-ai.onrender.com](https://pad-plus-ai.onrender.com)

Each request leaves a complete trace. You can watch it happen in real time through a WebSocket live view at `/api/v1/xray/ws` — every pipeline stage lights up as it executes:

```
Safety → Intent → Retrieve → Persona → Generate → Verify → Remember → Emit
```

Each stage shows execution time, success status, and position in the pipeline. You can also query recent traces via REST API and export them as JSON or CSV.

---

## Where This Is Going

After X-Ray came online, something interesting happened. The system could now see everything happening inside. Every phase, every error, every degradation, every deviation.

> *If it can already see its own problems... why can't it start fixing them?*

That question led to another project — **HEALER** — but that is a story for the next article in this series.

---

## Build With Me

X-Ray started as a debugging tool for a single AI architecture. Today it is a standalone observability library. But I do not believe its architecture is finished.

I am looking for engineers interested in:

- Distributed tracing
- Causal execution graphs
- Middleware integrations for non-FastAPI frameworks
- Replay and debugger tooling
- Storage backends beyond local JSON
- Developer experience for observability

If any of these topics interest you, I would love to discuss ideas, architecture, or pull requests.

**GitHub:** [github.com/Ovladimirovich/pad-plus-ai](https://github.com/Ovladimirovich/pad-plus-ai)

The X-Ray code lives inside the repository. It is also available as a standalone integration kit (private repository — access on request via [Telegram](https://t.me/padplusai)).

---

X-Ray answered one question for me: *How can we observe complex cognitive systems in a way that does not require reading log files?*

I do not think it has found the final answer. If you are interested in tracing, observability, distributed systems, or AI infrastructure, I would like this project to become a place where those ideas are debated, tested, and improved together.

That is the reason it is open source.
