"""
PipelinePhase — абстрактный базовый класс для всех фаз пайплайна.
Protocols — формальные контракты для внешних модулей.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from .models import PhaseResult, DegradationInfo
from .context import PipelineContext


class PipelinePhase(ABC):
    name: str = ""

    @abstractmethod
    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        ...

    def _degraded(
        self,
        component: str,
        error: str,
        severity: str = "medium",
        fallback_applied: bool = False,
    ) -> PhaseResult:
        return PhaseResult(
            success=False,
            errors=[error],
            degradation=DegradationInfo(
                component=component,
                error=error,
                severity=severity,
                fallback_applied=fallback_applied,
            ),
        )


class VerificationModule(Protocol):
    async def verify(self, claims: List[str], context: Dict[str, Any]) -> Dict[str, Any]: ...


class EmotionStateProvider(Protocol):
    def get_state(self) -> Dict[str, float]: ...
    def update(self, **deltas: float) -> None: ...


class PersonaProvider(Protocol):
    async def get_context(self, user_id: str) -> Dict[str, Any]: ...
    async def update(self, user_id: str, deltas: Dict[str, Any]) -> None: ...


class TraceCollectorProtocol(Protocol):
    async def record(self, event: str, data: Dict[str, Any]) -> None: ...
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]: ...
