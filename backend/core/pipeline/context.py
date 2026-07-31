"""
PipelineContext — контекст выполнения пайплайна.

Содержит все входные данные для одной итерации pipeline.execute():
- user_message, context, session_id
- api_key, provider (из Фазы 1)

Typed sections (B1):
- StrategyContext — стратегия и метаданные вызова
- ExecutionContext — результаты выполнения и тайминги
- SessionContext — сессионные данные
- MemoryContext — данные памяти (RAG, эпизодическая, процедуры)
- EmotionContext — эмоциональное состояние
- ImpulseContext — импульсы/смещения
- ExperienceContext — данные для обучения
- PersonaContext — контекст личности
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TypedDict


class StrategyContext(TypedDict, total=False):
    """Стратегия и метаданные вызова."""
    strategy: str
    intent: str
    pipeline: List[str]
    call_count: int


class ExecutionContext(TypedDict, total=False):
    """Результаты выполнения и тайминги."""
    response: str
    confidence: float
    provider: str
    model: str
    execution_time_ms: float
    start_time: float
    xray_request_id: str
    pipeline_result: Any
    pipeline_success: bool


class SessionContext(TypedDict, total=False):
    """Сессионные данные."""
    user_id: Optional[str]
    session_id: Optional[str]
    key_id: Optional[str]


class MemoryContext(TypedDict, total=False):
    """Данные памяти."""
    rag_used: bool
    rag_context: str
    facts_used: int
    episodic_context: str
    procedure_name: Optional[str]
    procedure_id: Optional[str]
    procedure_context: str
    graph_context: str
    sources: Dict[str, Any]
    episode_id: Optional[str]


class EmotionContext(TypedDict, total=False):
    """Эмоциональное состояние."""
    emotion_style: Dict[str, Any]
    emotion_state: Dict[str, Any]
    emotion_shift: Dict[str, Any]
    pad_vector: Dict[str, Any]


class ImpulseContext(TypedDict, total=False):
    """Импульсы и когнитивные смещения."""
    impulse_primary: str
    impulse_state: Dict[str, Any]
    impulse_bias: str
    impulse_updated: bool
    impulse_active: List[str]
    impulse_prompt_line: str


class ExperienceContext(TypedDict, total=False):
    """Данные для обучения и рефлексии."""
    experience_interaction_type: str
    experience_significance: float


class PersonaContext(TypedDict, total=False):
    """Контекст личности."""
    roots_context: str
    persona_context: str
    persona_adjustments: Dict[str, Any]


class PipelineContextData(TypedDict, total=False):
    """
    Полный типизированный словарь контекста пайплайна.
    
    Объединяет все секции. Используется как тип для ctx.context.
    total=False означает что все ключи опциональны (backward-compatible).
    """
    # Session
    user_message: str
    user_id: Optional[str]
    session_id: Optional[str]
    key_id: Optional[str]

    # Strategy
    strategy: str
    intent: str
    pipeline: List[str]
    call_count: int

    # Execution
    response: str
    confidence: float
    provider: str
    model: str
    execution_time_ms: float
    start_time: float
    xray_request_id: str
    pipeline_result: Any
    pipeline_success: bool

    # Memory
    rag_used: bool
    rag_context: str
    facts_used: int
    episodic_context: str
    procedure_name: Optional[str]
    procedure_id: Optional[str]
    procedure_context: str
    graph_context: str
    sources: Dict[str, Any]
    episode_id: Optional[str]

    # Emotion
    emotion_style: Dict[str, Any]
    emotion_state: Dict[str, Any]
    emotion_shift: Dict[str, Any]
    pad_vector: Dict[str, Any]

    # Impulse
    impulse_primary: str
    impulse_state: Dict[str, Any]
    impulse_bias: str
    impulse_updated: bool
    impulse_active: List[str]
    impulse_prompt_line: str

    # Experience
    experience_interaction_type: str
    experience_significance: float

    # Persona
    roots_context: str
    persona_context: str
    persona_adjustments: Dict[str, Any]

    # Other
    truth_confidence: float
    claims_verified: int
    evaluation: Dict[str, Any]
    memory_maintenance: Dict[str, Any]
    health_score: float
    blocked: bool
    warning: Optional[str]
    safety_passed: bool
    sanitized_message: str


@dataclass
class PipelineContext:
    user_message: str
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = None
