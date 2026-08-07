# 004_design_options.md — Cognitive Workspace Design Options

**Status:** Draft  
**Feeds into:** 005_prototype.md → 006_comparison.md → 007_adr.md

---

## Design Space Overview

Each option addresses the requirement clusters from 003_requirements.md. Options are **not mutually exclusive** — the final architecture will likely be a hybrid. We evaluate each cluster independently, then compose.

---

## Cluster A: Turn Workspace (FR-001) + State Persistence (FR-008)

### Option A1: LangGraph-Style Checkpointer (Recommended Base)

**Core Idea:** Use LangGraph's `StateGraph` + `BaseCheckpointSaver` as the turn workspace engine.

```python
# Schema (Pydantic)
class TurnWorkspace(BaseModel):
    session_id: str
    turn_id: int
    user_message: str
    intent: Intent
    # Phase outputs (immutable after phase completes)
    safety_result: Optional[SafetyResult] = None
    rag_result: Optional[RagResult] = None
    episodic_result: Optional[EpisodicResult] = None
    semantic_result: Optional[SemanticResult] = None
    emotion_result: Optional[EmotionResult] = None
    impulse_result: Optional[ImpulseResult] = None
    generation_result: Optional[GenerationResult] = None
    truth_result: Optional[TruthResult] = None
    evaluation_result: Optional[EvaluationResult] = None
    # Working scratchpad (mutable during turn)
    working: WorkingScratchpad = Field(default_factory=WorkingScratchpad)

# Checkpointer saves after each phase
class PostgresCheckpointer(BaseCheckpointSaver):
    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint) -> None:
        # INSERT INTO workspace_checkpoints (session_id, turn_id, phase, state_json) ...
    
    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        # SELECT state_json FROM workspace_checkpoints WHERE ...
```

| Pros | Cons |
|------|------|
| ✅ Battle-tested, production-ready | ❌ Adds LangGraph as heavy dependency |
| ✅ Time-travel, branching built-in | ❌ Checkpointer = full state serialization (heavy) |
| ✅ Contract validation via Pydantic | ❌ LangGraph graph compilation overhead |
| ✅ Time-travel debugging (X-Ray integration) | ❌ State = full history (grows unbounded) |

---

### Option A2: Custom Lightweight Checkpointer (Recommended for PAD+)

**Core Idea:** Minimal checkpointer tailored to PAD+ pipeline phases. No LangGraph dependency.

```python
# Phase-aware checkpointing
class PipelineCheckpointer:
    """Saves workspace after each phase; lightweight, phase-aware."""
    
    async def save_after_phase(
        self,
        session_id: str,
        turn_id: int,
        phase_name: str,
        workspace: TurnWorkspace
    ) -> None:
        # UPSERT INTO turn_workspaces (session_id, turn_id, phase, state_json)
        # + async pg_notify for X-Ray real-time
    
    async def load_latest(self, session_id: str, turn_id: int) -> Optional[TurnWorkspace]:
        # SELECT state_json FROM turn_workspaces WHERE session_id=? AND turn_id=?
        # ORDER BY phase_order DESC LIMIT 1
    
    async def load_at_phase(self, session_id: str, turn_id: int, phase: str) -> Optional[TurnWorkspace]:
        # Time-travel: load state AFTER specific phase
    
    async def branch(self, session_id: str, turn_id: int, from_phase: str, new_turn_id: int) -> TurnWorkspace:
        # Fork for what-if analysis

# Phase order defines serialization points
PHASE_ORDER = [
    "safety", "intent", "rag", "knowledge_graph", "episodic", "semantic",
    "emotion", "impulse", "persona", "roots", "identity", "generate",
    "truth_loop", "evaluation", "save_episode", "extraction", "emotion_update",
    "impulse_update", "events_broadcast", "response_guard"
]
```

| Pros | Cons |
|------|------|
| ✅ Zero external deps (pure asyncpg + Pydantic) | ❌ Must implement time-travel/branching ourselves |
| ✅ Phase-aware serialization (only changed fields) | ❌ No built-in graph compilation |
| ✅ Native PostgreSQL, async, asyncpg | ❌ Contract validation manual |
| ✅ X-Ray integration via pg_notify | ❌ No LangGraph ecosystem tools |

---

### Option A3: Hybrid — LangGraph for Graph, Custom for Storage

**Core Idea:** Use LangGraph's `StateGraph` for phase orchestration + custom Postgres checkpointer for storage.

```python
# Build graph with our phases as nodes
graph = StateGraph(TurnWorkspace)
graph.add_node("safety", SafetyPhaseNode())
graph.add_node("intent", IntentPhaseNode())
# ... all phases
graph.add_edge("safety", "intent")
# ... pipeline edges

# Custom checkpointer replaces LangGraph's
compiled = graph.compile(checkpointer=PipelineCheckpointer())
```

| Pros | Cons |
|------|------|
| ✅ Best of both: LangGraph orchestration + custom storage | ❌ Still depends on LangGraph |
| ✅ LangGraph handles parallel phases, retries, interrupts | ❌ Complexity: two systems to understand |

---

### **Recommendation for Turn Workspace: Option A2 (Custom Lightweight)**

**Rationale:** PAD+ already has a mature pipeline executor with 25 phases, parallel groups, background phases, X-Ray integration. Adding LangGraph would duplicate orchestration logic. A custom phase-aware checkpointer fits existing architecture with minimal friction.

---

## Cluster B: Conversation Workspace (FR-002)

### Option B1: Generative Agents Memory Stream (Append-Only Log)

```python
class ConversationWorkspace:
    session_id: str
    dialog_id: str
    
    # Append-only memory stream (Generative Agents style)
    memory_stream: List[MemoryRecord] = []
    
    # Derived views (computed on demand or cached)
    topic_stack: List[Topic] = []
    goal_stack: List[Goal] = []
    entity_registry: Dict[str, Entity] = {}
    summary: str = ""
    
    def append(self, record: MemoryRecord):
        self.memory_stream.append(record)
        self._update_derived_views(record)
    
    def _update_derived_views(self, record: MemoryRecord):
        # Incremental topic detection, entity extraction, goal tracking
    
    def get_relevant_context(self, query: str, k: int = 10) -> List[MemoryRecord]:
        # Retrieval: recency + importance + relevance (Generative Agents)
```

| Pros | Cons |
|------|------|
| ✅ Rich, expressive (topics, goals, entities emerge) | ❌ Computationally heavy (incremental updates per record) |
| ✅ Natural fit for LLM-based reasoning | ❌ Summary quality depends on LLM |
| ✅ Natural language queries ("what are we discussing?") | ❌ No strong consistency guarantees |

---

### Option B2: Structured Conversation State (Explicit Schema)

```python
class ConversationWorkspace(BaseModel):
    session_id: str
    dialog_id: str
    
    # Explicit structured state (no emergent magic)
    current_topic: Optional[str] = None
    topic_stack: List[Topic] = Field(default_factory=list)
    
    active_goals: List[Goal] = Field(default_factory=list)
    suspended_goals: List[Goal] = Field(default_factory=list)
    
    entities: Dict[str, Entity] = Field(default_factory=dict)
    key_facts: List[Fact] = Field(default_factory=list)
    
    summary: str = ""
    last_summary_turn: int = 0
    
    # Explicit update methods (no emergent behavior)
    def push_goal(self, goal: Goal) -> None: ...
    def suspend_goal(self, goal_id: str) -> None: ...
    def add_entity(self, entity: Entity) -> None: ...
    def add_fact(self, fact: Fact) -> None: ...
    def update_summary(self, llm: LLM) -> None: ...
```

| Pros | Cons |
|------|------|
| ✅ Predictable, debuggable, type-safe | ❌ Less "emergent" intelligence |
| ✅ Easy to test, serialize, migrate | ❌ Requires explicit updates (more code) |
| ✅ Fits PAD+ typed pipeline contracts | ❌ Less "human-like" emergence |

---

### Option B3: Hybrid — Structured Core + LLM-Enriched Views

```python
class ConversationWorkspace(BaseModel):
    # Core structured state (authoritative)
    core: ConversationCore
    
    # LLM-enriched views (cached, recomputed on demand)
    enriched: ConversationEnriched = Field(default_factory=ConversationEnriched)
    
    def refresh_enriched(self, llm: LLM) -> None:
        """LLM re-reads core state, produces enriched views."""
        self.enriched.summary = llm.summarize(self.core.recent_turns)
        self.enriched.topics = llm.extract_topics(self.core.memory_stream)
        self.enriched.implicit_goals = llm.infer_goals(self.core.memory_stream)

# Core = source of truth (structured, typed)
# Enriched = LLM-derived (fuzzy, updated periodically)
```

| Pros | Cons |
|------|------|
| ✅ Best of both: reliable core + intelligent views | ❌ Two sources of truth (cache invalidation) |
| ✅ LLM only runs periodically (cost control) | ❌ Cache staleness issues |

---

### **Recommendation for Conversation Workspace: Option B2 (Structured Core)**

**Rationale:** PAD+ values type safety, contracts, observability. Structured core with explicit update methods fits Pipeline contracts, ContractValidator, X-Ray tracing. LLM enrichment (Option B3) can be added later as enrichment layer.

---

## Cluster C: Working Memory / Scratchpad (FR-003)

### Option C1: ReAct-Style Scratchpad (Free-Form Text)

```python
class WorkingScratchpad:
    content: str = ""  # Free-form: "Hypothesis: X. Evidence: Y. Need to check Z."
    
    def append(self, text: str): ...
    def clear(): ...
    def get() -> str: ...
```

| Pros | Cons |
|------|------|
| ✅ Simple, flexible, LLM-native | ❌ No structure for tooling/validation |
| ✅ Matches ReAct pattern | ❌ Hard to extract structured evidence |

---

### Option C2: Structured Evidence/Hypothesis Graph (Recommended)

```python
class WorkingScratchpad(BaseModel):
    # Structured reasoning trace
    evidence: List[Evidence] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    current_focus: Optional[str] = None
    
    def add_evidence(self, e: Evidence): ...
    def propose_hypothesis(self, h: Hypothesis): ...
    def link_evidence_to_hypothesis(self, ev_id: str, hyp_id: str): ...
    def resolve_question(self, q: str): ...
    
    def to_prompt_context(self) -> str:
        """Render for LLM injection."""
```

| Pros | Cons |
|------|------|
| ✅ Structured, queryable, type-safe | ❌ More verbose for LLM |
| ✅ X-Ray can trace evidence → hypothesis | ❌ More code to maintain |
| ✅ ContractValidator can validate | |

---

### **Recommendation: Option C2 (Structured Scratchpad)**

---

## Cluster D: Memory Hierarchy (FR-004)

### Option D1: Three-Tier (MemGPT Style)

| Tier | Name | Storage | TTL | Use Case |
|------|------|---------|-----|----------|
| L1 | Working Memory | In-memory (per turn) | Turn | Scratchpad, intermediate |
| L2 | Conversation Memory | Redis / PG (per session) | 24h | ConversationWorkspace |
| L3 | Archival Memory | Vector DB (pgvector) | Forever | Semantic/episodic/reflection |

| Pros | Cons |
|------|------|
| ✅ Clear separation, token budget awareness | ❌ Three systems to maintain |
| ✅ Matches MemGPT proven pattern | ❌ Cross-tier queries complex |

---

### Option D2: Two-Tier + Conversation (PAD+ Adapted)

| Tier | Name | Storage | Scope |
|------|------|---------|-------|
| T1 | Turn Workspace | PG (checkpoint) | Per turn |
| T2 | Conversation Workspace | PG (session row) | Per session |
| T3 | Long-term Memory | Vector DB (pgvector) | Cross-session |

- **SessionEmotionStore / SessionImpulseStore** already implement T2 for emotion/impulse
- **ConversationWorkspace** adds T2 for topics/goals/entities
- **Vector DB** (existing pgvector) for T3

| Pros | Cons |
|------|------|
| ✅ Reuses existing stores (SessionEmotionStore, pgvector) | ❌ Less tier separation than MemGPT |
| ✅ Simpler ops (2 DBs: PG + pgvector) | |

---

### **Recommendation: Option D2 (Two-Tier + Conversation)**

**Rationale:** Aligns with existing PAD+ architecture (SessionEmotionStore, SessionImpulseStore, pgvector). Avoids new infrastructure.

---

## Cluster E: Goal Stack (FR-005)

### Option E1: ACT-R Style Goal Stack (Hierarchical)

```python
class GoalStack:
    stack: List[Goal] = []  # LIFO: current goal at top
    
    def push(self, goal: Goal): ...
    def pop() -> Goal: ...
    def suspend(goal_id: str): ...  # Move to suspended list
    def resume(goal_id: str): ...
    def current() -> Optional[Goal]: ...
```

| Pros | Cons |
|------|------|
| ✅ Theoretical grounding (ACT-R) | ❌ Complex for simple chat |
| ✅ Natural suspend/resume | ❌ Overhead for single-turn tasks |

---

### Option E2: Flat Task List with Parent Links (AutoGPT Style)

```python
class Task:
    id: str
    parent_id: Optional[str]
    name: str
    status: TaskStatus
    subtasks: List[str] = []
```

| Pros | Cons |
|------|------|
| ✅ Simple, intuitive | ❌ No true suspend/resume (only parent/child) |
| ✅ Easy to visualize | ❌ No goal suspension semantics |

---

### Option E3: Hybrid — Hierarchical Goals with Explicit Suspend/Resume

```python
class GoalStack:
    # Active goals (hierarchical)
    root_goals: List[Goal] = []
    current_path: List[str] = []  # Path from root to current
    
    # Suspended goals (with full context)
    suspended: Dict[str, SuspendedGoal] = {}
    
    def push_goal(self, goal: Goal, parent_id: Optional[str]): ...
    def suspend_current(self, reason: str): ...
    def resume_goal(self, goal_id: str): ...
```

| Pros | Cons |
|------|------|
| ✅ True suspend/resume with context | ❌ More complex |
| ✅ Fits multi-turn complex tasks | |

---

### **Recommendation: Option E3 (Hybrid Goal Stack)**

---

## Cluster F: Reflection Engine (FR-006)

### Option F1: Generative Agents Style (Periodic + LLM)

```python
class ReflectionEngine:
    def __init__(self, interval_turns: int = 10):
        self.interval = interval_turns
        self.turn_counter = 0
    
    def maybe_reflect(self, workspace: ConversationWorkspace, llm: LLM) -> List[Reflection]:
        self.turn_counter += 1
        if self.turn_counter % self.interval == 0:
            return self._periodic_reflect(workspace, llm)
        return []
    
    def on_failure(self, error: Exception, workspace: ConversationWorkspace, llm: LLM) -> List[Reflection]:
        return self._failure_reflect(error, workspace, llm)
```

| Pros | Cons |
|------|------|
| ✅ Proven pattern (Generative Agents) | ❌ LLM cost per reflection |
| ✅ Periodic + failure-triggered | ❌ Quality varies |

---

### Option F2: Lightweight — Structured Reflection (No LLM for Simple Cases)

```python
class ReflectionEngine:
    def on_phase_failure(self, phase: str, error: Exception) -> Reflection:
        return Reflection(
            type="phase_failure",
            content=f"Phase {phase} failed: {error}",
            actionable=f"Add fallback for {phase}"
        )
    
    def on_low_confidence(self, confidence: float) -> Reflection:
        if confidence < 0.3:
            return Reflection(
                type="low_confidence",
                content=f"Confidence {confidence:.2f} below threshold",
                actionable="Trigger TruthLoop verification"
            )
```

| Pros | Cons |
|------|------|
| ✅ Zero LLM cost for common cases | ❌ Less rich insights |
| ✅ Fast, deterministic | ❌ Misses semantic patterns |

---

### Option F3: Hybrid — Structured + LLM for Deep Reflection

```python
class ReflectionEngine:
    def reflect(self, workspace: ConversationWorkspace, trigger: Trigger, llm: LLM) -> List[Reflection]:
        # Fast structured reflections (always)
        reflections = self._structured_reflect(workspace, trigger)
        
        # Deep LLM reflection (periodic or high-impact failure)
        if self._should_deep_reflect(trigger):
            reflections += self._deep_reflect(workspace, llm)
        
        return reflections
```

| Pros | Cons |
|------|------|
| ✅ Best of both | ❌ Two code paths |

---

### **Recommendation: Option F3 (Hybrid)**

---

## Cluster G: Planning Engine (FR-007)

### Option G1: Semantic Kernel Planner (Structured)

```python
class Planner:
    def create_plan(self, goal: Goal, context: ConversationWorkspace, available_tools: List[Tool]) -> Plan:
        # Use SK's sequential/stepwise planner
```

| Pros | Cons |
|------|------|
| ✅ Battle-tested | ❌ SK dependency |
| ✅ Handles tool dependencies | ❌ Plan = static (no dynamic replanning) |

---

### Option G2: LLM-as-Planner (ReAct + Structured Output)

```python
class Planner:
    def create_plan(self, goal: Goal, context: ConversationWorkspace) -> Plan:
        prompt = f"""Goal: {goal}
Context: {context.summary}
Available tools: {tools}
Output JSON plan with steps, dependencies, expected outcomes."""
        return llm.structured_output(Plan, prompt)
    
    def replan(self, failed_step: int, error: Exception, current_plan: Plan) -> Plan:
        # Dynamic replanning
```

| Pros | Cons |
|------|------|
| ✅ Dynamic replanning | ❌ LLM cost |
| ✅ Flexible | ❌ Needs structured output enforcement |

---

### **Recommendation: Option G2 (LLM-as-Planner with Structured Output)**

**Rationale:** PAD+ already uses LLM for generation. Structured output (Pydantic) gives type safety. Replanning is critical for complex tasks.

---

## Cluster H: Learning Bus (FR-004 + FR-006 → Unified Learning)

### Option H1: Event Bus + Handlers (Decoupled)

```python
class LearningBus:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def publish(self, event: LearningEvent):
        for handler in self.handlers[event.type]:
            handler(event)
    
    def subscribe(self, event_type: str, handler: Callable):
        self.handlers[event_type].append(handler)

# Events:
@dataclass
class StrategyOutcome:
    strategy: str
    success: bool
    confidence: float
    turn_id: int

@dataclass
class ReflectionInsight:
    reflection: Reflection
    applied: bool
```

| Pros | Cons |
|------|------|
| ✅ Decouples learners | ❌ Eventual consistency |
| ✅ Easy to add new learners | ❌ Debugging event flow |

---

### Option H2: Centralized Learning Coordinator (PAD+ Style)

```python
class LearningCoordinator:
    """Single component owns all learning signals."""
    
    def record_strategy_outcome(self, outcome: StrategyOutcome): ...
    def record_reflection_insight(self, insight: ReflectionInsight): ...
    def record_persona_drift(self, drift: PersonaDrift): ...
    
    def get_strategy_stats(self) -> StrategyStats: ...
    def get_reflection_patterns(self) -> List[Pattern]: ...
```

| Pros | Cons |
|------|------|
| ✅ Single source of truth | ❌ Centralized bottleneck |
| ✅ Easy cross-learner queries | ❌ Must modify to add new signal types |

---

### **Recommendation: Option H2 (Learning Coordinator)**

**Rationale:** PAD+ already has centralized components (PersonaMemory, ImpulseManager). LearningCoordinator fits architecture. 4 MetaLearners → 1 Coordinator = unification.

---

## Summary: Recommended Option Composition

| Cluster | Recommended Option | Key Rationale |
|---------|-------------------|---------------|
| **A: Turn Workspace** | A2: Custom Lightweight Checkpointer | Fits existing pipeline, no LangGraph dep |
| **B: Conversation Workspace** | B2: Structured Core | Type safety, contracts, debuggable |
| **C: Working Memory** | C2: Structured Scratchpad | Evidence/hypothesis links, X-Ray traceable |
| **D: Memory Hierarchy** | D2: Two-Tier + Conversation | Reuses existing stores |
| **E: Goal Stack** | E3: Hybrid with Suspend/Resume | True suspend/resume for multi-turn |
| **F: Reflection** | F3: Hybrid (Structured + LLM) | Cost control + rich insights |
| **G: Planning** | G2: LLM-as-Planner | Dynamic replanning, structured output |
| **H: Learning Bus** | H2: Learning Coordinator | Single source of truth, fits architecture |

---

## Next: 005_prototype.md

Build throw-away PoC for the **core workspace loop** (TurnWorkspace + ConversationWorkspace + Checkpointer) — < 500 LOC, stdlib + pydantic + asyncpg only.