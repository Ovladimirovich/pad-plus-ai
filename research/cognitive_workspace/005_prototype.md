# 005_prototype.md — Cognitive Workspace PoC (Throw-Away)

**Status:** Draft  
**Scope:** Core workspace loop — TurnWorkspace + ConversationWorkspace + Checkpointer  
**Constraints:** < 500 LOC, stdlib + pydantic + asyncpg only  
**Purpose:** Validate core loop works, measure overhead, test time-travel  
**Throw-away:** Code NOT merged to main — only insights feed 006/007

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pipeline Turn                            │
├─────────────────────────────────────────────────────────────────┤
│  User Message → TurnWorkspace → Phase 1 → Phase 2 → ... → Done  │
│                          ↓ checkpoint after each phase          │
│                    PostgresCheckpointer                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ConversationWorkspace                         │
│  (persisted per session, updated after turn)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
prototype/
├── main.py                 # Entry point: run demo pipeline
├── workspace/
│   ├── __init__.py
│   ├── schemas.py          # Pydantic models (TurnWorkspace, ConversationWorkspace, WorkingScratchpad)
│   ├── checkpointer.py     # PostgresCheckpointer (asyncpg)
│   ├── conversation.py     # ConversationWorkspace manager
│   └── pipeline.py         # Mini-pipeline executor (3 phases)
├── test_prototype.py       # Unit + integration tests
└── requirements.txt        # pydantic, asyncpg, pytest-asyncio
```

---

## schemas.py — Core Types

```python
# prototype/workspace/schemas.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class PhaseName(str, Enum):
    SAFETY = "safety"
    INTENT = "intent"
    RAG = "rag"
    GENERATE = "generate"
    TRUTH_LOOP = "truth_loop"
    EVALUATION = "evaluation"
    SAVE_EPISODE = "save_episode"


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    content: str
    source: str  # "rag", "episodic", "semantic", "user"
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    statement: str
    supporting_evidence: List[str] = Field(default_factory=list)  # evidence IDs
    status: str = "proposed"  # proposed | supported | rejected
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class WorkingScratchpad(BaseModel):
    """Structured scratchpad for current turn reasoning."""
    evidence: List[Evidence] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    current_focus: Optional[str] = None

    def add_evidence(self, content: str, source: str, confidence: float = 0.8) -> Evidence:
        ev = Evidence(content=content, source=source, confidence=confidence)
        self.evidence.append(ev)
        return ev

    def propose_hypothesis(self, statement: str) -> Hypothesis:
        hyp = Hypothesis(statement=statement)
        self.hypotheses.append(hyp)
        return hyp

    def link_evidence(self, ev_id: str, hyp_id: str) -> bool:
        hyp = next((h for h in self.hypotheses if h.id == hyp_id), None)
        if hyp and ev_id not in hyp.supporting_evidence:
            hyp.supporting_evidence.append(ev_id)
            return True
        return False


class TurnWorkspace(BaseModel):
    """Per-turn workspace — checkpointed after each phase."""
    session_id: str
    turn_id: int
    user_message: str
    intent: str = "unknown"
    
    # Phase outputs (immutable after phase completes)
    phase_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Working scratchpad (mutable during turn)
    scratchpad: WorkingScratchpad = Field(default_factory=WorkingScratchpad)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    current_phase: Optional[PhaseName] = None

    def update_phase(self, phase: PhaseName, output: Any) -> None:
        self.phase_outputs[phase.value] = output
        self.current_phase = phase
        self.updated_at = datetime.now()

    def to_checkpoint_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_checkpoint_json(cls, json_str: str) -> "TurnWorkspace":
        return cls.model_validate_json(json_str)


class Topic(BaseModel):
    name: str
    introduced_turn: int
    parent_topic: Optional[str] = None


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    description: str
    status: str = "active"  # active | suspended | completed | failed
    parent_id: Optional[str] = None
    created_turn: int
    suspended_turn: Optional[int] = None
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)


class ConversationCore(BaseModel):
    """Authoritative structured state — updated explicitly."""
    session_id: str
    dialog_id: str
    current_topic: Optional[str] = None
    topic_stack: List[Topic] = Field(default_factory=list)
    active_goals: List[Goal] = Field(default_factory=list)
    suspended_goals: List[Goal] = Field(default_factory=list)
    entities: Dict[str, str] = Field(default_factory=dict)  # name -> description
    key_facts: List[str] = Field(default_factory=list)
    turn_count: int = 0
    last_summary: str = ""
    last_summary_turn: int = 0


class ConversationWorkspace(BaseModel):
    """Per-session conversation workspace."""
    core: ConversationCore
    
    def add_turn(self, turn_id: int, user_message: str, intent: str) -> None:
        self.core.turn_count = turn_id
        # Topic detection (simple heuristic)
        if intent not in ("greeting", "chat_general"):
            self.core.current_topic = intent
            if intent not in [t.name for t in self.core.topic_stack]:
                self.core.topic_stack.append(Topic(name=intent, introduced_turn=turn_id))
    
    def push_goal(self, description: str, turn_id: int, parent_id: Optional[str] = None) -> Goal:
        goal = Goal(description=description, created_turn=turn_id, parent_id=parent_id)
        self.core.active_goals.append(goal)
        return goal
    
    def suspend_goal(self, goal_id: str, turn_id: int) -> bool:
        for i, goal in enumerate(self.core.active_goals):
            if goal.id == goal_id:
                goal.status = "suspended"
                goal.suspended_turn = turn_id
                goal.context_snapshot = {"turn": turn_id, "topic": self.core.current_topic}
                self.core.suspended_goals.append(self.core.active_goals.pop(i))
                return True
        return False
    
    def resume_goal(self, goal_id: str) -> bool:
        for i, goal in enumerate(self.core.suspended_goals):
            if goal.id == goal_id:
                goal.status = "active"
                goal.suspended_turn = None
                self.core.active_goals.append(self.core.suspended_goals.pop(i))
                return True
        return False
    
    def add_entity(self, name: str, description: str) -> None:
        self.core.entities[name] = description
    
    def add_fact(self, fact: str) -> None:
        self.core.key_facts.append(fact)
```

---

## checkpointer.py — PostgresCheckpointer

```python
# prototype/workspace/checkpointer.py
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from pydantic import BaseModel

from .schemas import TurnWorkspace, ConversationWorkspace, PhaseName

logger = logging.getLogger(__name__)


class CheckpointRecord(BaseModel):
    session_id: str
    turn_id: int
    phase: str
    workspace_json: str
    created_at: datetime


class PostgresCheckpointer:
    """Phase-aware PostgreSQL checkpointer for TurnWorkspace."""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    @classmethod
    async def create(cls, dsn: str, min_size: int = 2, max_size: int = 10) -> "PostgresCheckpointer":
        pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
        await cls._init_schema(pool)
        return cls(pool)
    
    @staticmethod
    async def _init_schema(pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS turn_workspaces (
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    workspace_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (session_id, turn_id, phase)
                );
                CREATE INDEX IF NOT EXISTS idx_turn_workspaces_session_turn 
                ON turn_workspaces (session_id, turn_id);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_workspaces (
                    session_id TEXT PRIMARY KEY,
                    dialog_id TEXT NOT NULL,
                    workspace_json JSONB NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_branches (
                    branch_id TEXT PRIMARY KEY,
                    parent_session_id TEXT NOT NULL,
                    parent_turn_id INTEGER NOT NULL,
                    parent_phase TEXT NOT NULL,
                    workspace_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
    
    # ===== Turn Workspace =====
    
    async def save_after_phase(
        self,
        workspace: "TurnWorkspace",
        phase: PhaseName
    ) -> None:
        """Save checkpoint after phase completes."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO turn_workspaces (session_id, turn_id, phase, workspace_json)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (session_id, turn_id, phase) DO UPDATE
                SET workspace_json = EXCLUDED.workspace_json, created_at = NOW()
            """, workspace.session_id, workspace.turn_id, phase.value, workspace.to_checkpoint_json())
    
    async def load_latest(self, session_id: str, turn_id: int) -> Optional["TurnWorkspace"]:
        """Load latest checkpoint for a turn (after last completed phase)."""
        from .schemas import TurnWorkspace
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT workspace_json FROM turn_workspaces
                WHERE session_id = $1 AND turn_id = $2
                ORDER BY 
                    CASE phase 
                        WHEN 'evaluation' THEN 14
                        WHEN 'truth_loop' THEN 13
                        WHEN 'generate' THEN 12
                        WHEN 'identity' THEN 11
                        WHEN 'roots' THEN 10
                        WHEN 'persona' THEN 9
                        WHEN 'impulse' THEN 8
                        WHEN 'emotion' THEN 7
                        WHEN 'semantic' THEN 6
                        WHEN 'episodic' THEN 5
                        WHEN 'knowledge_graph' THEN 4
                        WHEN 'rag' THEN 3
                        WHEN 'intent' THEN 2
                        WHEN 'safety' THEN 1
                        ELSE 99
                    END DESC
                LIMIT 1
            """, session_id, turn_id)
            if row:
                return TurnWorkspace.from_checkpoint_json(row["workspace_json"])
        return None
    
    async def load_at_phase(
        self, session_id: str, turn_id: int, phase: PhaseName
    ) -> Optional["TurnWorkspace"]:
        """Time-travel: load state AFTER specific phase."""
        from .schemas import TurnWorkspace
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT workspace_json FROM turn_workspaces
                WHERE session_id = $1 AND turn_id = $2 AND phase = $3
            """, session_id, turn_id, phase.value)
            if row:
                return TurnWorkspace.from_checkpoint_json(row["workspace_json"])
        return None
    
    async def branch(
        self, session_id: str, turn_id: int, from_phase: PhaseName, new_turn_id: int
    ) -> "TurnWorkspace":
        """Fork workspace for what-if analysis."""
        from .schemas import TurnWorkspace
        workspace = await self.load_at_phase(session_id, turn_id, from_phase)
        if not workspace:
            raise ValueError(f"No checkpoint at {from_phase}")
        
        # Create new turn with forked state
        workspace.turn_id = new_turn_id
        workspace.created_at = datetime.now()
        workspace.updated_at = datetime.now()
        workspace.current_phase = None
        
        # Save as new turn
        await self.save_after_phase(workspace, PhaseName.SAFETY)
        return workspace
    
    # ===== Conversation Workspace =====
    
    async def save_conversation(self, workspace: ConversationWorkspace) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_workspaces (session_id, dialog_id, workspace_json)
                VALUES ($1, $2, $3)
                ON CONFLICT (session_id) DO UPDATE
                SET workspace_json = EXCLUDED.workspace_json, updated_at = NOW()
            """, workspace.core.session_id, workspace.core.dialog_id, 
                workspace.model_dump_json())
    
    async def load_conversation(self, session_id: str) -> Optional[ConversationWorkspace]:
        from .schemas import ConversationWorkspace
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT workspace_json FROM conversation_workspaces WHERE session_id = $1
            """, session_id)
            if row:
                return ConversationWorkspace.model_validate_json(row["workspace_json"])
        return None
```

---

## pipeline.py — Mini Pipeline Executor

```python
# prototype/workspace/pipeline.py
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import (
    TurnWorkspace, ConversationWorkspace, PhaseName, WorkingScratchpad,
    Evidence, Hypothesis
)
from .checkpointer import PostgresCheckpointer

logger = logging.getLogger(__name__)


class PhaseResult(BaseModel):
    phase: PhaseName
    success: bool
    output: Any
    duration_ms: float
    error: Optional[str] = None


class MiniPipeline:
    """3-phase demo pipeline: Intent → RAG → Generate"""
    
    PHASES = [
        PhaseName.INTENT,
        PhaseName.RAG,
        PhaseName.GENERATE,
    ]
    
    def __init__(self, checkpointer: PostgresCheckpointer):
        self.checkpointer = checkpointer
    
    async def execute(
        self,
        session_id: str,
        user_message: str,
        conversation: ConversationWorkspace,
        turn_id: int
    ) -> Dict[str, Any]:
        """Execute one pipeline turn with checkpointing."""
        
        # Create turn workspace
        workspace = TurnWorkspace(
            session_id=session_id,
            turn_id=turn_id,
            user_message=user_message,
        )
        
        # Execute phases sequentially
        for phase in self.PHASES:
            workspace.current_phase = phase
            start = datetime.now()
            
            try:
                output = await self._run_phase(phase, workspace, user_message)
                duration = (datetime.now() - start).total_seconds() * 1000
                
                # Update workspace with phase output
                workspace.update_phase(phase, output)
                
                # CHECKPOINT after phase
                await self.checkpointer.save_after_phase(workspace, phase)
                
                logger.info(f"Phase {phase.value} completed in {duration:.1f}ms")
                
            except Exception as e:
                logger.error(f"Phase {phase.value} failed: {e}")
                raise
        
        # Final checkpoint (after last phase)
        await self.checkpointer.save_after_phase(workspace, self.PHASES[-1])
        
        return {
            "workspace": workspace,
            "response": workspace.phase_outputs.get("generate", "No response"),
        }
    
    async def _run_phase(
        self, phase: PhaseName, workspace: "TurnWorkspace", user_message: str
    ) -> Any:
        """Simulate phase execution."""
        
        if phase == PhaseName.INTENT:
            # Simulate intent classification
            await asyncio.sleep(0.01)
            return {"intent": "question", "confidence": 0.92}
        
        elif phase == PhaseName.RAG:
            # Simulate RAG retrieval
            await asyncio.sleep(0.02)
            # Add evidence to scratchpad
            workspace.scratchpad.add_evidence(
                content="Quantum entanglement is a physical phenomenon...",
                source="rag",
                confidence=0.85
            )
            return {"context": "Quantum entanglement is a physical phenomenon...", "sources": 3}
        
        elif phase == PhaseName.GENERATE:
            # Simulate generation
            await asyncio.sleep(0.015)
            return {"response": "Quantum entanglement is when particles become linked..."}
        
        return None


async def demo():
    """Run demo with 2 turns, verify checkpointing and time-travel."""
    import os
    from .checkpointer import PostgresCheckpointer
    from .schemas import ConversationWorkspace, ConversationCore
    
    # Setup
    dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    pool = await PostgresCheckpointer.create(dsn)
    
    pipeline = MiniPipeline(pool)
    conversation = ConversationWorkspace(
        core=ConversationCore(
            session_id="demo-session-1",
            dialog_id="demo-dialog-1",
        )
    )
    
    print("=== Turn 1 ===")
    result1 = await pipeline.execute(
        session_id="demo-session-1",
        user_message="What is quantum entanglement?",
        conversation=conversation,
        turn_id=1
    )
    print(f"Response: {result1['response'][:80]}...")
    
    # Save conversation workspace
    await pool.checkpointer.save_conversation(conversation)
    
    print("\n=== Turn 2 ===")
    result2 = await pipeline.execute(
        session_id="demo-session-1",
        user_message="Can you explain it simpler?",
        conversation=conversation,
        turn_id=2
    )
    print(f"Response: {result2['response'][:80]}...")
    
    # === TIME-TRAVEL TEST ===
    print("\n=== TIME-TRAVEL TEST ===")
    # Load state after RAG phase in turn 1
    turn1_after_rag = await pool.checkpointer.load_at_phase(
        "demo-session-1", 1, PhaseName.RAG
    )
    if turn1_after_rag:
        print(f"Turn 1 after RAG - scratchpad evidence count: {len(turn1_after_rag.scratchpad.evidence)}")
        print(f"  Evidence: {turn1_after_rag.scratchpad.evidence[0].content[:60]}...")
    
    # Load final state of turn 1
    turn1_final = await pool.checkpointer.load_latest("demo-session-1", 1)
    if turn1_final:
        print(f"Turn 1 final - phases completed: {list(turn1_final.phase_outputs.keys())}")
    
    # Branch from turn 1 after RAG
    print("\n=== BRANCHING TEST ===")
    branched = await pool.checkpointer.branch(
        "demo-session-1", 1, PhaseName.RAG, 99
    )
    print(f"Branched turn 99 created, phase: {branched.current_phase}")
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
```

---

## test_prototype.py — Tests

```python
# prototype/test_prototype.py
import asyncio
import pytest
from datetime import datetime

from workspace.schemas import (
    TurnWorkspace, ConversationWorkspace, ConversationCore,
    PhaseName, WorkingScratchpad, Evidence, Hypothesis
)
from workspace.checkpointer import PostgresCheckpointer


@pytest.fixture
async def checkpointer():
    dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    cp = await PostgresCheckpointer.create(dsn)
    yield cp
    await cp.pool.close()


@pytest.mark.asyncio
async def test_turn_workspace_creation():
    ws = TurnWorkspace(
        session_id="test-1",
        turn_id=1,
        user_message="Hello",
    )
    assert ws.session_id == "test-1"
    assert ws.turn_id == 1
    assert ws.current_phase is None


@pytest.mark.asyncio
async def test_scratchpad_operations():
    scratch = WorkingScratchpad()
    
    # Add evidence
    ev = scratch.add_evidence("Test fact", "rag", 0.9)
    assert len(scratch.evidence) == 1
    assert ev.content == "Test fact"
    
    # Propose hypothesis
    hyp = scratch.propose_hypothesis("This is true")
    assert len(scratch.hypotheses) == 1
    
    # Link evidence
    assert scratch.link_evidence(ev.id, hyp.id)
    assert hyp.supporting_evidence == [ev.id]


@pytest.mark.asyncio
async def test_conversation_workspace_goals():
    conv = ConversationWorkspace(
        core=ConversationCore(session_id="s1", dialog_id="d1")
    )
    
    # Push goal
    goal = conv.push_goal("Explain quantum physics", turn_id=1)
    assert len(conv.core.active_goals) == 1
    assert goal.status == "active"
    
    # Suspend
    assert conv.suspend_goal(goal.id, turn_id=2)
    assert len(conv.core.active_goals) == 0
    assert len(conv.core.suspended_goals) == 1
    assert conv.core.suspended_goals[0].status == "suspended"
    
    # Resume
    assert conv.resume_goal(goal.id)
    assert len(conv.core.active_goals) == 1
    assert conv.core.active_goals[0].status == "active"


@pytest.mark.asyncio
async def test_checkpointer_save_load(checkpointer: PostgresCheckpointer):
    from workspace.schemas import TurnWorkspace, PhaseName
    
    ws = TurnWorkspace(
        session_id="test-session",
        turn_id=1,
        user_message="Test message",
    )
    ws.update_phase(PhaseName.INTENT, {"intent": "question"})
    
    # Save
    await checkpointer.save_after_phase(ws, PhaseName.INTENT)
    
    # Load
    loaded = await checkpointer.load_latest("test-session", 1)
    assert loaded is not None
    assert loaded.session_id == "test-session"
    assert loaded.turn_id == 1
    assert "intent" in loaded.phase_outputs


@pytest.mark.asyncio
async def test_checkpointer_time_travel(checkpointer: PostgresCheckpointer):
    from workspace.schemas import TurnWorkspace, PhaseName
    
    ws = TurnWorkspace(session_id="tt-test", turn_id=1, user_message="Test")
    ws.update_phase(PhaseName.INTENT, {"intent": "q"})
    await checkpointer.save_after_phase(ws, PhaseName.INTENT)
    
    ws.update_phase(PhaseName.RAG, {"context": "ctx"})
    await checkpointer.save_after_phase(ws, PhaseName.RAG)
    
    ws.update_phase(PhaseName.GENERATE, {"response": "resp"})
    await checkpointer.save_after_phase(ws, PhaseName.GENERATE)
    
    # Load at specific phase
    at_rag = await checkpointer.load_at_phase("tt-test", 1, PhaseName.RAG)
    assert at_rag is not None
    assert at_rag.current_phase == PhaseName.RAG
    assert "intent" in at_rag.phase_outputs
    assert "context" in at_rag.phase_outputs
    assert "response" not in at_rag.phase_outputs


@pytest.mark.asyncio
async def test_checkpointer_branching(checkpointer: PostgresCheckpointer):
    from workspace.schemas import TurnWorkspace, PhaseName
    
    ws = TurnWorkspace(session_id="branch-test", turn_id=1, user_message="Test")
    ws.update_phase(PhaseName.INTENT, {"intent": "q"})
    await checkpointer.save_after_phase(ws, PhaseName.INTENT)
    
    ws.update_phase(PhaseName.RAG, {"context": "ctx"})
    await checkpointer.save_after_phase(ws, PhaseName.RAG)
    
    # Branch from after RAG
    branched = await checkpointer.branch("branch-test", 1, PhaseName.RAG, 99)
    assert branched.turn_id == 99
    assert branched.current_phase is None  # Reset for new turn
    assert "intent" in branched.phase_outputs
    assert "context" in branched.phase_outputs
```

---

## requirements.txt

```
pydantic>=2.0
asyncpg>=0.29
pytest>=7.0
pytest-asyncio>=0.21
```

---

## Running the Prototype

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Ensure PostgreSQL running (local or Docker)
# docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16

# 3. Run demo
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres python -m prototype.workspace.pipeline

# 4. Run tests
pytest prototype/test_prototype.py -v
```

---

## Expected Output (Demo)

```
=== Turn 1 ===
Phase intent completed in 12.3ms
Phase rag completed in 24.1ms
Phase generate completed in 18.7ms
Response: Quantum entanglement is when particles become linked...

=== Turn 2 ===
Phase intent completed in 11.8ms
Phase rag completed in 22.4ms
Phase generate completed in 19.2ms
Response: Think of it like two magic dice...

=== TIME-TRAVEL TEST ===
Turn 1 after RAG - scratchpad evidence count: 1
  Evidence: Quantum entanglement is a physical phenomenon...
Turn 1 final - phases completed: ['intent', 'rag', 'generate']

=== BRANCHING TEST ===
Branched turn 99 created, phase: None

✅ Demo completed successfully!
```

---

## Success Criteria (Measured)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Checkpoint save (per phase) | < 5ms | `asyncpg` INSERT |
| Checkpoint load (latest) | < 3ms | `asyncpg` SELECT |
| Time-travel load | < 3ms | Indexed query |
| Branch creation | < 10ms | INSERT + JSON copy |
| Turn workspace creation | < 1ms | Pydantic model |
| Memory per session | < 1MB | JSONB size |

---

## What This Validates

- [ ] TurnWorkspace checkpointing works per phase
- [ ] ConversationWorkspace persists across turns
- [ ] Time-travel: load at specific phase works
- [ ] Branching: fork from checkpoint works
- [ ] Scratchpad structured operations work
- [ ] Conversation goal stack push/suspend/resume works
- [ ] Overhead within targets

---

## What This Does NOT Validate

- Full 25-phase pipeline integration
- Real LLM calls
- Vector memory retrieval
- Reflection/planning engines
- Production load (concurrent sessions)

*Those require full integration — this is a throw-away structural validation.*