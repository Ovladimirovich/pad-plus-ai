"""
Memory Trace — X-Ray Extension for Memory Observability

MemoryEvent — новый тип события в X-Ray для полной наблюдаемости памяти.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class MemoryOperation(str, Enum):
    """Тип операции над памятью"""
    READ = "READ"
    WRITE = "WRITE"
    SEARCH = "SEARCH"
    DELETE = "DELETE"
    DECAY = "DECAY"
    CONSOLIDATE = "CONSOLIDATE"
    MERGE = "MERGE"
    VERIFY = "VERIFY"
    SUMMARIZE = "SUMMARIZE"
    RECALL = "RECALL"
    REINDEX = "REINDEX"
    RESTORE = "RESTORE"
    CONFLICT = "CONFLICT"
    INVALIDATE = "INVALIDATE"
    EVICT = "EVICT"
    BACKUP = "BACKUP"
    SNAPSHOT = "SNAPSHOT"


class MemoryResult(str, Enum):
    """Результат операции"""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    MERGED = "MERGED"
    CONSOLIDATED = "CONSOLIDATED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    PARTIAL = "PARTIAL"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    EVICTED = "EVICTED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"
    INVALIDATED = "INVALIDATED"


class MemoryComponent(str, Enum):
    """Компонент памяти (Owner)"""
    EPISODIC_MEMORY = "EpisodicMemory"
    SEMANTIC_MEMORY = "SemanticMemory"
    RAG_MEMORY = "RAGMemory"
    ROOTS_MEMORY = "RootsMemory"
    EMOTION_ENGINE = "EmotionEngine"
    IMPULSE_CORE = "ImpulseCore"
    PERSONA_MEMORY = "PersonaMemory"
    USER_PERSONA = "UserPersonaManager"
    WORKING_MEMORY = "WorkingMemory"
    XRAY_TRACE = "XRayTrace"
    META_LEARNER = "MetaLearner"
    CONSOLIDATION = "Consolidation"
    SESSION_MANAGER = "SessionManager"
    UNKNOWN = "Unknown"


class MemoryObjectType(str, Enum):
    """Тип объекта памяти"""
    EPISODE = "Episode"
    FACT = "Fact"
    PROCEDURE = "Procedure"
    ROOT = "Root"
    EMOTION_STATE = "EmotionState"
    IMPULSE_STATE = "ImpulseState"
    PERSONA_TRAITS = "PersonaTraits"
    USER_PERSONA = "UserPersona"
    DIALOG = "Dialog"
    SESSION = "Session"
    WORKING_MEMORY = "WorkingMemory"
    CONTEXT = "Context"
    UNKNOWN = "Unknown"


@dataclass
class MemoryEvent:
    """Событие памяти для X-Ray"""
    
    # Identity
    event_id: str = field(default_factory=lambda: uuid4().hex[:16])
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Context
    session_id: Optional[str] = None
    dialog_id: Optional[str] = None
    turn_id: Optional[int] = None
    phase: Optional[str] = None
    request_id: Optional[str] = None
    
    # Operation
    operation: MemoryOperation = MemoryOperation.READ
    component: MemoryComponent = MemoryComponent.UNKNOWN
    object_type: MemoryObjectType = MemoryObjectType.UNKNOWN
    object_id: Optional[str] = None
    
    # Result
    result: MemoryResult = MemoryResult.FOUND
    error: Optional[str] = None
    
    # Timing
    duration_ms: float = 0.0
    queue_time_ms: float = 0.0
    lock_wait_ms: float = 0.0
    
    # Payload
    payload_size_bytes: int = 0
    payload_preview: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Trace context
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    
    def to_xray_dict(self) -> Dict[str, Any]:
        """Serialize for X-Ray ingestion"""
        return {
            "event_type": "memory_event",
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "dialog_id": self.dialog_id,
            "turn_id": self.turn_id,
            "phase": self.phase,
            "request_id": self.request_id,
            "operation": self.operation.value,
            "component": self.component.value,
            "object_type": self.object_type.value,
            "object_id": self.object_id,
            "result": self.result.value,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "queue_time_ms": self.queue_time_ms,
            "lock_wait_ms": self.lock_wait_ms,
            "payload_size_bytes": self.payload_size_bytes,
            "payload_preview": self.payload_preview,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }


class MemoryTraceService:
    """Сервис сбора и анализа MemoryEvent"""
    
    def __init__(self, xray_client=None):
        self.xray = xray_client
        self._buffer: list = []
        self._flush_interval = 100  # events
    
    def emit(self, event: MemoryEvent) -> None:
        self._buffer.append(event)
        if len(self._buffer) >= self._flush_interval:
            self.flush()
    
    def flush(self) -> None:
        if not self._buffer:
            return
        events = self._buffer
        self._buffer = []
        # Batch send to X-Ray
        if self.xray:
            self.xray.send_batch([e.to_xray_dict() for e in events])
    
    async def aemit(self, event: MemoryEvent) -> None:
        self.emit(event)


# Global instance
_memory_trace_service: Optional["MemoryTraceService"] = None


def get_memory_tracer() -> "MemoryTraceService":
    global _memory_trace_service
    if _memory_trace_service is None:
        _memory_trace_service = MemoryTraceService()
    return _memory_trace_service


# Convenience function for emitting memory events
def emit_memory_event(
    operation: MemoryOperation,
    component: MemoryComponent,
    object_type: MemoryObjectType,
    object_id: Optional[str] = None,
    result: MemoryResult = MemoryResult.FOUND,
    duration_ms: float = 0.0,
    payload_size_bytes: int = 0,
    payload_preview: Optional[str] = None,
    session_id: Optional[str] = None,
    dialog_id: Optional[str] = None,
    turn_id: Optional[int] = None,
    phase: Optional[str] = None,
    request_id: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function for emitting memory events"""
    tracer = get_memory_tracer()
    event = MemoryEvent(
        operation=operation,
        component=component,
        object_type=object_type,
        object_id=object_id,
        result=result,
        duration_ms=duration_ms,
        payload_size_bytes=payload_size_bytes,
        payload_preview=payload_preview,
        session_id=session_id,
        dialog_id=dialog_id,
        turn_id=turn_id,
        phase=phase,
        request_id=request_id,
        error=error,
        metadata=metadata or {},
    )
    tracer.emit(event)