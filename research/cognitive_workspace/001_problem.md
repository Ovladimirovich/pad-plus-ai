# Cognitive Workspace Research — 001: Problem Statement

**Status:** Draft  
**Date:** 2026-07-31  
**Owner:** Research Stream  
**Related:** PHASE_PLAN_TWO_STREAMS.md, ARCHITECTURE_EVOLUTION_PLAN.md

---

## TL;DR

**Current pipeline processes one user message → one LLM response.**  
But "thinking" requires *workspace* — a place to hold intermediate state across phases, across turns, across reasoning steps.  
We don't have it. What we have:

| What we have | What's missing |
|--------------|----------------|
| `ctx.context` — untyped `Dict[str, Any]` bag | Typed, structured workspace |
| `PipelineResult` — final output only | Working state during execution |
| `session_id` in 3+ systems (dialogs, X-Ray, sessions) | Single source of truth for "this conversation" |
| 4 independent MetaLearners | Unified learning bus |
| Emotion/Impulse now per-session (Phase C) | Cross-turn workspace for reasoning |

---

## Concrete Pain Points (Evidence)

### 1. Pipeline `ctx.context` is an untyped grab-bag

```python
# 70+ keys read/written across phases, no schema:
ctx.context["strategy"]           # str
ctx.context["rag_context"]        # str
ctx.context["emotion_state"]      # Dict
ctx.context["impulse_primary"]    # str
ctx.context["procedure_name"]     # Optional[str]
ctx.context["pipeline_result"]    # PipelineResult (circular!)
# ... 60 more keys
```

**ContractValidator exists but unused** — `contracts.py` defines `requires/produces` but `ContractValidator.pre_check()` never called in executor.

### 2. No working memory across turns

```
Turn 1: User asks "What is quantum entanglement?"
  → Pipeline runs → response generated → discarded

Turn 2: User asks "Can you explain it simpler?"
  → Pipeline runs AGAIN from scratch
  → No access to Turn 1's reasoning, sources, or intent
```

**Missing:** `ConversationWorkspace` that persists:
- Current topic / sub-topics
- Active goals / sub-goals
- Working hypotheses
- Open questions
- Source references (so Turn 2 can cite Turn 1's sources)

### 3. Reasoning trace is implicit, not first-class

```
Safety → Intent → RAG → Episodic → Semantic → Emotion → Impulse → Generate → TruthLoop → Eval
```

Each phase writes to `ctx.context`, but:
- No explicit "I am now reasoning about X" step
- TruthLoop verifies *output*, not *reasoning*
- Reflection phase runs *after* response, not *during* reasoning
- No way to "pause, think, continue" — single-pass pipeline

### 4. Learning signals fragmented across 4 MetaLearners

| Learner | Tracks | Input | Output |
|---------|--------|-------|--------|
| `meta_learner.py` (X-Ray) | Strategy success | Phase timings | Strategy weights |
| `ReflectionLoop` | Response quality | Evaluation | Adjustments |
| `ExperienceLearner` | Interaction patterns | Dialog events | Style adjustments |
| `PersonaEvolution` | Personality drift | Dialog analysis | Trait adjustments |

**No unified `LearningBus`** — each sees different slice, duplicates work, can't share credit assignment.

### 5. Session identity fractured across systems

| System | ID | Scope |
|--------|-----|-------|
| `SessionManager` | `sess_...` or `user_id` | 24h TTL, JSON file |
| `X-Ray TraceCollector` | `request_id` (UUID) | Per-request |
| `Dialogs API` | `dialog_id` (UUID) | Per-conversation |
| `Experience Store` | `dialog_id` | Per-turn |
| `Supabase Auth` | `user.id` (UUID) | Per-user |

**No canonical "this conversation" ID** that all systems agree on. Phase C fixed Emotion/Impulse to use `user_id`, but others still use own IDs.

---

## What "Cognitive Workspace" Should Enable

### Minimal viable workspace (per turn)

```python
@dataclass
class TurnWorkspace:
    session_id: str
    turn_id: int
    
    # Input
    user_message: str
    intent: Intent
    available_context: ContextBundle
    
    # Working state (mutable during turn)
    current_hypothesis: Optional[str] = None
    sub_goals: List[SubGoal] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    reasoning_trace: List[ReasoningStep] = field(default_factory=list)
    
    # Output (filled by end of turn)
    response_draft: Optional[str] = None
    confidence: float = 0.0
    citations: List[Citation] = field(default_factory=list)
```

### Cross-turn workspace (conversation-level)

```python
@dataclass
class ConversationWorkspace:
    session_id: str
    dialog_id: str
    
    # Persistent across turns
    topic_stack: List[Topic] = field(default_factory=list)
    active_goals: List[Goal] = field(default_factory=list)
    user_model: UserModel
    shared_context: Dict[str, Any] = field(default_factory=dict)
    # e.g., "user prefers concise answers", "working on Python project"
    
    # Learning signals (unified)
    learning_events: List[LearningEvent] = field(default_factory=list)
```

---

## What This Blocks

| Next Phase | Blocked Because |
|------------|-----------------|
| **Phase D: Learning Unification** | No unified `LearningEvent` schema; 4 learners write different formats |
| **Phase E: Cognitive Context** | No workspace to snapshot; `CognitiveContextSnapshot` would be empty |
| **Phase F: Conversation State** | No `ConversationWorkspace` to track topics/goals across turns |
| **Phase G: Decision Engine** | No `WorkingMemory` to hold alternatives during strategy selection |

---

## Acceptance Criteria for "Problem Understood"

- [ ] Documented: **exact list of keys** in `ctx.context` with types (auto-generated from code)
- [ ] Documented: **exact data flow** per phase (reads → writes)
- [ ] Documented: **3 concrete scenarios** where current architecture fails
  1. Multi-turn reasoning (user asks follow-up requiring previous turn's context)
  2. Complex task decomposition (user asks "plan a trip" → needs sub-goals)
  3. Learning credit assignment (which phase caused success/failure?)
- [ ] Measured: **overhead** of current untyped `ctx.context` (memory, GC pressure)
- [ ] Measured: **latency** of pipeline phases (which are hot paths)

---

## Next Steps

| Step | Output | Owner |
|------|--------|-------|
| 002_examples.md | Collect 10+ reference implementations (MemGPT, LangGraph, ACT-R, etc.) | Research |
| 003_requirements.md | Formal requirements from above | Research |
| 004_design_options.md | 3-5 workspace designs with tradeoffs | Research |
| 005_prototype.md | Throw-away PoC (< 500 LOC) | Research |
| 006_comparison.md | Decision matrix | Research |
| 007_adr.md | Architecture Decision Record | Team |

---

## Appendix: Current `ctx.context` Key Inventory (Auto-generated)

*To be filled by script scanning `phases/*.py` for `ctx.context.get/[]`*

```json
{
  "strategy_keys": ["strategy", "intent", "pipeline", "call_count", "start_time", "xray_request_id", "pipeline_result", "pipeline_success"],
  "memory_keys": ["rag_used", "rag_context", "facts_used", "episodic_context", "procedure_name", "procedure_context", "graph_context", "sources", "episode_id"],
  "emotion_keys": ["emotion_style", "emotion_state", "emotion_shift", "pad_vector"],
  "impulse_keys": ["impulse_primary", "impulse_state", "impulse_bias", "impulse_updated", "impulse_active", "impulse_prompt_line"],
  "persona_keys": ["roots_context", "persona_context", "persona_adjustments"],
  "truth_keys": ["truth_confidence", "claims_verified", "sources_info", "add_disclaimer"],
  "learning_keys": ["evaluation", "experience_interaction_type", "experience_significance", "memory_maintenance"],
  "session_keys": ["user_id", "session_id", "key_id", "blocked", "warning", "safety_passed", "sanitized_message"]
}
```

---

*This document is the anchor for the Research Stream. All subsequent docs (002-007) reference back here.*