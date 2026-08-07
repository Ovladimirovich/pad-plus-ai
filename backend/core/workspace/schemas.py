"""
TurnWorkspace, WorkingScratchpad, Evidence, Hypothesis — типизированные структуры
для фазового воркспейса текущего хода (Turn) по архитектуре D'-1.
"""

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
    KNOWLEDGE_GRAPH = "knowledge_graph"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EMOTION = "emotion"
    IMPULSE = "impulse"
    PERSONA = "persona"
    ROOTS = "roots"
    IDENTITY = "identity"
    GENERATE = "generate"
    TRUTH_LOOP = "truth_loop"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"
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
    """Структурированный блок для рассуждений в текущем шаге."""
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
    """Воркспейс текущего хода — сохраняет состояние после каждой фазы."""
    session_id: str
    turn_id: int
    user_message: str
    intent: str = "unknown"
    
    # Результаты выполнения фаз (неизменяемые после завершения фазы)
    phase_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Рабочая область рассуждений
    scratchpad: WorkingScratchpad = Field(default_factory=WorkingScratchpad)
    
    # Метаданные
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
    """Авторитетное структурированное состояние — обновляется явно."""
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
    """Воркспейс сессии — персистируется между ходами."""
    core: ConversationCore
    
    def add_turn(self, turn_id: int, user_message: str, intent: str) -> None:
        self.core.turn_count = turn_id
        # Простое определение топика
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
