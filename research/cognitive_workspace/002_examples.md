# Cognitive Workspace Research — 002: Reference Implementations

**Status:** Draft  
**Date:** 2026-07-31  
**Owner:** Research Stream  
**Related:** 001_problem.md, 003_requirements.md, 004_design_options.md

---

## Purpose

Collect and analyze **10+ reference implementations** of cognitive workspace / working memory / conversation state systems. Each entry covers:

- Core abstraction
- Key data structures
- Persistence model
- Integration pattern
- Strengths/weaknesses for our use case

---

## 1. MemGPT (v0.2+, 2023-2024)

**Source:** `https://github.com/cpacker/memgpt` | Paper: "MemGPT: Towards LLMs as Operating Systems" (Packer et al., 2023)

### Core Abstraction: **Virtual Memory Management**

```
┌─────────────────────────────────────────────────────────┐
│                    Main Context (Token Budget)          │
│  [System] [User] [Assistant] [Recall] [Working Memory]  │
└─────────────────────────────────────────────────────────┘
                              ↓ evict / recall
┌─────────────────────────────────────────────────────────┐
│                 External Context (Vector DB)            │
│  [Archival Memory] [Recall Memory] [Metadata Index]     │
└─────────────────────────────────────────────────────────┘
```

### Key Data Structures

```python
# Main context (fits in context window)
class MainContext:
    system: str
    user_message: str
    assistant_message: str
    recall_memory: List[Memory]      # Recent conversation
    working_memory: WorkingMemory    # Scratchpad for current task

# External memory (persistent)
class ArchivalMemory:
    def insert(text: str, metadata: dict) -> str
    def search(query: str, top_k: int) -> List[Memory]

class RecallMemory:
    def append(message: Message)
    def get_recent(k: int) -> List[Message]
```

### Persistence
- **Main context:** Rebuilt each turn from components
- **Recall memory:** FIFO queue (last N messages)
- **Archival memory:** Vector DB (pgvector/Chroma) + metadata index

### Integration Pattern
- **Function calling** for memory operations (`core_memory_append`, `archival_memory_insert`, `archival_memory_search`)
- Agent decides when to read/write memory via tool calls
- Single LLM call per turn with full context assembled

### Strengths for PAD+
- ✅ Explicit memory hierarchy (working vs archival vs recall)
- ✅ Token budget awareness — forces summarization
- ✅ Tool-based memory ops = interpretable, debuggable
- ✅ Persistent across sessions (archival)

### Weaknesses for PAD+
- ❌ No cross-turn "workspace" — working memory reset each turn
- ❌ No explicit goal/task tracking
- ❌ Single-threaded reasoning (no sub-task decomposition)
- ❌ Memory ops via function calling = extra LLM calls

---

## 2. LangGraph (LangChain, 2024)

**Source:** `https://github.com/langchain-ai/langgraph`

### Core Abstraction: **StateGraph + Checkpointer**

```
StateGraph(Nodes) → Compile → Runnable
                    ↓
Checkpointer.save(state, config)  # After each node
Checkpointer.load(config)         # Before execution
```

### Key Data Structures

```python
# User-defined state (TypedDict / Pydantic)
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    # Custom fields:
    user_intent: Optional[str]
    current_plan: Optional[Plan]
    working_memory: Dict[str, Any]
    citations: List[Citation]

# Checkpointer interface
class BaseCheckpointSaver:
    def put(config: RunnableConfig, checkpoint: Checkpoint) -> None
    def get(config: RunnableConfig) -> Optional[Checkpoint]
    def list(config: RunnableConfig) -> List[CheckpointTuple]
```

### Persistence
- **PostgreSQL checkpointer** (production)
- **Sqlite checkpointer** (dev)
- **In-memory** (testing)
- Full state serialized after each node

### Integration Pattern
- Define state schema → Build graph → Compile with checkpointer
- State automatically persisted at each step
- Time-travel: `graph.get_state(config)` → resume from any checkpoint

### Strengths for PAD+
- ✅ First-class state management with versioning
- ✅ Time-travel debugging (critical for X-Ray)
- ✅ Typed state schema (Pydantic/TypedDict)
- ✅ Multiple checkpointer backends
- ✅ Human-in-the-loop via interrupts

### Weaknesses for PAD+
- ❌ State = entire conversation history (grows unbounded)
- ❌ No built-in "working memory" vs "long-term" distinction
- ❌ No semantic memory / vector search built-in
- ❌ Graph compilation overhead for dynamic pipelines

---

## 3. ACT-R / Soar (Cognitive Architectures, 1990s-present)

**Source:** `https://act-r.psy.cmu.edu/` | `https://soar.eecs.umich.edu/`

### Core Abstraction: **Production System + Working Memory**

```
┌────────────────────────────────────────┐
│           Working Memory               │
│  (Chunks: declarative knowledge)       │
└────────────────────────────────────────┘
                    ↓ match
┌────────────────────────────────────────┐
│         Production Memory              │
│  IF condition THEN action              │
│  (Procedural knowledge)                │
└────────────────────────────────────────┘
                    ↓ fire
┌────────────────────────────────────────┐
│         Goal Stack                     │
│  (Hierarchical goals/subgoals)         │
└────────────────────────────────────────┘
```

### Key Data Structures

```lisp
; ACT-R Chunk (declarative)
(chunk-type fact 
  slot1 slot2 slot3 ...)

; Production Rule (procedural)
(p rule-name
  =goal> 
    isa task
    state start
  ==>
  =goal>
    state retrieving
  +retrieval>
    isa fact
    slot1 =value)

; Goal Stack
(goal-focus goal1 goal2 goal3)  ; LIFO stack
```

### Persistence
- **Working memory:** In-memory, cleared between runs (unless saved)
- **Declarative memory:** Saved to disk (ACT-R format)
- **Procedural memory:** Compiled productions saved

### Integration Pattern
- **Model tracing** — every production fire logged
- **Parameter tuning** — subsymbolic parameters (activation, latency)
- **Model comparison** — fit to human data

### Strengths for PAD+
- ✅ Theoretically grounded (30+ years cognitive science)
- ✅ Explicit goal hierarchy (subgoals, suspend/resume)
- ✅ Activation-based retrieval (forgetting = low activation)
- ✅ Learning mechanisms (production compilation, base-level learning)

### Weaknesses for PAD+
- ❌ Not designed for LLM integration
- ❌ Symbolic only — no vector/embedding support
- ❌ Steep learning curve, Lisp/CLI-based
- ❌ No conversation/turn management

---

## 4. AutoGPT / BabyAGI (2023)

**Source:** `https://github.com/Significant-Gravitas/AutoGPT` | `https://github.com/yoheinakajima/babyagi`

### Core Abstraction: **Task List + Recursive Decomposition**

```
User Goal → Task List → [Execute → Subtasks → ...] → Result
                    ↓
            Memory (Vector DB)
```

### Key Data Structures

```python
# BabyAGI
class Task:
    task_id: str
    task_name: str
    priority: int
    status: "pending" | "in_progress" | "complete"

# AutoGPT
class Agent:
    goals: List[str]
    memory: VectorMemory
    task_list: List[Task]
    current_task: Optional[Task]
```

### Persistence
- **Vector memory** (Pinecone/Chroma/Weaviate) for long-term
- **Task list** in JSON/file
- **Conversation history** in memory or file

### Integration Pattern
- **Loop:** Select task → Execute → Generate subtasks → Update memory → Repeat
- **Single LLM call per step** with context = goals + memory + current task

### Strengths for PAD+
- ✅ Explicit task decomposition
- ✅ Persistent goal tracking
- ✅ Memory + reasoning separation

### Weaknesses for PAD+
- ❌ No conversation/turn model (single-shot goal)
- ❌ No session isolation
- ❌ Brittle — error in one step breaks chain
- ❌ No observability / debugging built-in

---

## 5. ReAct / Reflexion (Reasoning Patterns, 2022-2023)

**Source:** "ReAct: Synergizing Reasoning and Acting in LLMs" (Yao et al., 2022) | "Reflexion: Language Agents with Verbal Reinforcement Learning" (Shinn et al., 2023)

### Core Abstraction: **Scratchpad + Verbal Reflection**

```
ReAct:  Thought → Action → Observation → Thought → ...
Reflexion: Experience → Verbal Reflection → Updated Policy → Retry
```

### Key Data Structures

```python
# ReAct trajectory
trajectory = [
    {"thought": "I need to search for X", "action": "search", "observation": "..."},
    {"thought": "Now I have enough info", "action": "answer", "observation": "final"}
]

# Reflexion
reflection = "I failed because I didn't verify the source. Next time I'll..."
updated_prompt = base_prompt + "\n\n" + reflection
```

### Persistence
- **Trajectory:** In-context (lost after context window)
- **Reflexion memory:** Text file / DB with reflections per task type

### Strengths for PAD+
- ✅ Explicit reasoning trace (matches X-Ray needs)
- ✅ Self-improvement via verbal reflection
- ✅ Minimal infrastructure

### Weaknesses for PAD+
- ❌ No persistent workspace across turns
- ❌ Scratchpad = context window pressure
- ❌ No goal/task decomposition

---

## 6. Cognitive Architectures for LLM Agents: Generative Agents (Park et al., 2023)

**Source:** "Generative Agents: Interactive Simulacra of Human Behavior" (Park et al., 2023) | `https://github.com/joonspk-research/generative_agents`

### Core Abstraction: **Memory Stream + Reflection + Planning**

```
┌────────────────────────────────────────────────────────────┐
│                    Memory Stream (append-only)             │
│  [Observation] [Observation] [Observation] ...             │
└────────────────────────────────────────────────────────────┘
                           ↓ retrieve (recency + importance + relevance)
┌────────────────────────────────────────────────────────────┐
│                    Working Memory (Context)                │
└────────────────────────────────────────────────────────────┘
                           ↓ reflect (periodically)
┌────────────────────────────────────────────────────────────┐
│                    Reflections (higher-level)              │
│  "Klaus is passionate about research"                      │
└────────────────────────────────────────────────────────────┘
                           ↓ plan
┌────────────────────────────────────────────────────────────┐
│                    Daily Plan (hourly schedule)            │
└────────────────────────────────────────────────────────────┘
```

### Key Data Structures

```python
class MemoryObject:
    created: datetime
    content: str          # "Klaus is reading a book"
    importance: float     # 0-10
    embedding: List[float]
    last_accessed: datetime

class Reflection:
    content: str          # "Klaus is a researcher"
    importance: float
    related_memories: List[MemoryObject]

class Plan:
    hourly_schedule: List[Tuple[time, str]]
```

### Persistence
- **Memory stream:** JSONL file (append-only)
- **Reflections:** Separate JSONL
- **Plans:** JSON file (overwritten daily)
- **Embeddings:** Computed on-the-fly or cached

### Strengths for PAD+
- ✅ Rich memory model (recency + importance + relevance)
- ✅ Explicit reflection mechanism
- ✅ Planning from memory
- ✅ Emergent social behavior

### Weaknesses for PAD+
- ❌ Simulation-focused, not conversation-focused
- ❌ No session/turn model
- ❌ Heavy LLM usage for reflection (costly)
- ❌ No explicit goal/task hierarchy

---

## 7. Semantic Kernel (Microsoft, 2023-2024)

**Source:** `https://github.com/microsoft/semantic-kernel`

### Core Abstraction: **Kernel + Planners + Memory**

```
Kernel → Planner → Function Calling → Memory
```

### Key Data Structures

```python
# Semantic Memory
class SemanticMemory:
    async def save_information(collection: str, id: str, text: str, description: str)
    async def search(collection: str, query: str, limit: int, min_relevance: float)

# Planner
class Planner:
    async def create_plan(goal: str, available_functions: List[Function]) -> Plan

class Plan:
    steps: List[PlanStep]
    
class PlanStep:
    function: str
    parameters: Dict[str, Any]
    output_variable: str
```

### Persistence
- **Semantic memory:** Vector DB (Qdrant, Pinecone, etc.)
- **Chat history:** In-memory or custom store
- **Plans:** Transient (per goal)

### Strengths for PAD+
- ✅ Built-in planners (sequential, step-wise, handlebars)
- ✅ Semantic memory with vector search
- ✅ Function calling abstraction

### Weaknesses for PAD+
- ❌ No conversation workspace
- ❌ Planner output = static plan (no dynamic replanning)
- ❌ Enterprise-focused, heavy abstraction

---

## 8. LlamaIndex (GPT Index) — Data Agents (2023-2024)

**Source:** `https://github.com/run-llama/llama_index`

### Core Abstraction: **Query Engine + Agent + Memory**

```
User Query → Agent → [Tools: QueryEngine, Memory, ...] → Response
```

### Key Data Structures

```python
# Memory
class ChatMemoryBuffer:
    token_limit: int
    chat_history: List[ChatMessage]
    def put(message: ChatMessage)
    def get(input: str) -> List[ChatMessage]

# Agent
class OpenAIAgent:
    tools: List[BaseTool]
    memory: ChatMemoryBuffer
    system_prompt: str
```

### Persistence
- **Chat memory:** Token-limited buffer (FIFO)
- **Vector indices:** Persistent (Chroma, Pinecone, etc.)
- **Agent state:** Not persisted by default

### Strengths for PAD+
- ✅ Mature RAG + agent integration
- ✅ Multiple memory types (buffer, vector, kg)
- ✅ Composability

### Weaknesses for PAD+
- ❌ No cross-turn workspace
- ❌ Memory = chat history only
- ❌ No goal/task tracking

---

## 9. DSPy (Stanford, 2023-2024)

**Source:** `https://github.com/stanfordnlp/dspy`

### Core Abstraction: **Declarative Programming + Optimizers**

```
Signature → Module → Optimizer → Compiled Program
```

### Key Data Structures

```python
# Signature (IO specification)
class QA(dspy.Signature):
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

# Module (reasoning pattern)
class ChainOfThought(dspy.Module):
    def __init__(self, signature):
        self.prog = dspy.ChainOfThought(signature)
    
    def forward(self, question):
        return self.prog(question=question)

# Optimizer
optimizer = dspy.BootstrapFewShot(metric=accuracy)
compiled = optimizer.compile(program, trainset=...)
```

### Persistence
- **Compiled programs:** Serialized (pickle/JSON)
- **Traces:** For optimization, not runtime

### Strengths for PAD+
- ✅ Systematic prompt optimization
- ✅ Declarative reasoning patterns
- ✅ Evaluation-driven

### Weaknesses for PAD+
- ❌ No conversation/memory model
- ❌ Single-turn focused
- ❌ Optimization = offline, not online learning

---

## 10. OpenAI Assistants API (2024)

**Source:** `https://platform.openai.com/docs/assistants/overview`

### Core Abstraction: **Thread + Assistant + Tools**

```
Assistant (instructions + tools) 
    ↓
Thread (messages + state)
    ↓
Run (execution)
```

### Key Data Structures

```python
# Thread = conversation + state
class Thread:
    messages: List[Message]
    metadata: Dict
    tool_resources: ToolResources

# Run = execution
class Run:
    status: "queued" | "in_progress" | "completed" | "failed"
    required_action: Optional[RequiredAction]
    usage: Usage

# Assistant = config
class Assistant:
    instructions: str
    tools: List[Tool]
    model: str
```

### Persistence
- **Threads:** Server-side, persistent (OpenAI managed)
- **Messages:** Append-only
- **Files:** Vector store (file search tool)

### Strengths for PAD+
- ✅ Built-in conversation persistence
- ✅ Tool use (code interpreter, file search, function calling)
- ✅ Managed infrastructure

### Weaknesses for PAD+
- ❌ Vendor lock-in (OpenAI only)
- ❌ No custom memory/working memory
- ❌ No goal/task decomposition
- ❌ Black box execution (no X-Ray equivalent)

---

## Summary Comparison Matrix

| System | Workspace Type | Cross-turn | Goals/Tasks | Memory Hierarchy | Persistence | LLM-Agnostic |
|--------|---------------|------------|-------------|------------------|-------------|--------------|
| **MemGPT** | Working + Archival | ❌ | ❌ | ✅ (3-tier) | Vector DB + JSON | ✅ |
| **LangGraph** | Full State | ✅ (checkpoint) | ❌ | ❌ | Postgres/SQLite | ✅ |
| **ACT-R/Soar** | WM + Goal Stack | ❌ | ✅ (hierarchical) | ✅ (decl/proc) | File | ❌ |
| **AutoGPT/BabyAGI** | Task List | ❌ | ✅ (flat) | Vector only | Vector DB + JSON | ✅ |
| **ReAct/Reflexion** | Scratchpad | ❌ | ❌ | ❌ | Text file | ✅ |
| **Generative Agents** | Memory Stream | ✅ | ✅ (daily plan) | ✅ (stream + reflection) | JSONL | ✅ |
| **Semantic Kernel** | Planner + Memory | ❌ | ✅ (plan) | Vector only | Vector DB | ✅ |
| **LlamaIndex** | Chat Buffer + Tools | ❌ | ❌ | Vector + Chat | Vector DB | ✅ |
| **DSPy** | Program State | ❌ | ❌ | ❌ | Pickle/JSON | ✅ |
| **OpenAI Assistants** | Thread | ✅ (server) | ❌ | Vector only | Managed | ❌ |

---

## Key Insights for PAD+

| Insight | Implication for Our Design |
|---------|----------------------------|
| **No system has it all** | We need hybrid: LangGraph-style state + MemGPT memory hierarchy + Generative Agents reflection |
| **Working memory ≠ Chat history** | Must separate scratchpad (per-turn) from conversation memory (cross-turn) |
| **Goals need hierarchy** | Flat task lists (AutoGPT) fail on complex tasks; need goal stack (ACT-R) |
| **Reflection ≠ Post-hoc** | Generative Agents reflect periodically; Reflexion reflects on failure; both useful |
| **State persistence = Time travel** | LangGraph checkpointer = debugging gold; must have |
| **Memory hierarchy = Token budget** | MemGPT's 3-tier = practical for context window limits |

---

## Recommended Hybrid for PAD+

| Layer | Inspiration | Our Adaptation |
|-------|-------------|----------------|
| **Turn Workspace** | LangGraph state + ReAct scratchpad | Typed `TurnWorkspace` per turn, auto-saved |
| **Conversation Workspace** | Generative Agents memory stream | `ConversationWorkspace` with topic stack + goals |
| **Working Memory** | MemGPT working memory | Scratchpad for current reasoning (evidence, hypotheses) |
| **Long-term Memory** | MemGPT archival + Generative Agents stream | Vector DB + Reflection stream |
| **Goal Stack** | ACT-R goal stack | Hierarchical goals with suspend/resume |
| **Reflection Engine** | Generative Agents + Reflexion | Periodic + failure-triggered |
| **State Persistence** | LangGraph checkpointer | PostgreSQL checkpointer with full history |
| **Observability** | X-Ray + LangGraph time-travel | Unified trace + time-travel |

---

## Next: 003_requirements.md

Formalize requirements from Problem (001) + Examples (002) → structured requirements for 004_design_options.md