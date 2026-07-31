"""
ContractValidator — проверка контрактов фаз pipeline.

Каждая фаза декларирует:
- requires: ключи, которые обязаны быть в ctx.context перед execute
- produces: ключи, которые фаза гарантированно записывает
- optional_produces: ключи, которые фаза может записать (conditional)

Pre-hook: проверяет requires ⊆ ctx.keys (fail fast если нарушено)
Post-hook: проверяет что все produced ключи соответствуют контракту
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional
import logging

logger = logging.getLogger("padplus.pipeline.contracts")


@dataclass
class PhaseContract:
    name: str
    requires: Set[str] = field(default_factory=set)
    produces: Set[str] = field(default_factory=set)
    optional_produces: Set[str] = field(default_factory=set)


# Контракты foreground-фаз (background-фазы проверяются отдельно)
FOREGROUND_CONTRACTS: Dict[str, PhaseContract] = {
    "safety": PhaseContract(
        name="safety",
        requires={"user_message"},
        produces={"blocked", "warning", "safety_passed"},
        optional_produces={"sanitized_message"},
    ),
    "intent": PhaseContract(
        name="intent",
        requires={"user_message"},
        produces={"intent"},
        optional_produces={"pipeline_meta"},
    ),
    "rag": PhaseContract(
        name="rag",
        requires={"user_message", "user_id"},
        produces={"rag_context", "rag_used"},
        optional_produces={"sources"},
    ),
    "knowledge_graph": PhaseContract(
        name="knowledge_graph",
        requires={"user_message"},
        produces={"concepts", "graph_context", "confidence"},
    ),
    "episodic": PhaseContract(
        name="episodic",
        requires={"user_message", "user_id"},
        produces={"episodic_context", "count"},
    ),
    "semantic": PhaseContract(
        name="semantic",
        requires={"user_message"},
        produces={"procedure_context", "procedure_name", "procedure_id"},
    ),
    "emotion": PhaseContract(
        name="emotion",
        produces={"emotion_state", "emotion_style", "pad_vector", "emotional_shift"},
    ),
    "impulse": PhaseContract(
        name="impulse",
        produces={
            "impulse_state", "impulse_bias", "impulse_primary",
            "impulse_prompt_line", "impulse_active",
        },
    ),
    "persona": PhaseContract(
        name="persona",
        requires={"user_id", "intent"},
        produces={"persona_context"},
    ),
    "roots": PhaseContract(
        name="roots",
        produces={"roots_context"},
    ),
    "identity": PhaseContract(
        name="identity",
        requires={"user_message", "emotion_state", "call_count"},
        produces={"is_identity", "response", "provider", "confidence", "model"},
        optional_produces={"skip_generate"},
    ),
    "generate": PhaseContract(
        name="generate",
        requires={
            "user_message", "roots_context", "persona_context",
            "rag_context", "episodic_context", "procedure_context",
            "graph_context", "emotion_style", "emotion_state",
            "strategy", "impulse_bias", "impulse_primary",
        },
        produces={"response", "provider", "confidence", "model"},
        optional_produces={
            "raw_llm_response", "llm_metadata", "impulse_used", "impulse_primary",
        },
    ),
    "truth_loop": PhaseContract(
        name="truth_loop",
        requires={"response"},
        optional_produces={"truth_confidence", "claims_verified", "sources_info", "add_disclaimer"},
    ),
    "evaluation": PhaseContract(
        name="evaluation",
        requires={"response", "confidence", "strategy", "intent", "model", "provider"},
        produces={"evaluation", "evaluation_skipped"},
        optional_produces={"ask_feedback", "feedback_prompt", "reason"},
    ),
    "save_episode": PhaseContract(
        name="save_episode",
        requires={"response", "intent", "rag_used", "procedure_name", "truth_confidence", "emotion_state", "user_id"},
        produces={"episode_id"},
    ),
    "extraction": PhaseContract(
        name="extraction",
        requires={"user_message"},
        produces={"concepts_added", "relations_added"},
    ),
    "emotion_update": PhaseContract(
        name="emotion_update",
        requires={"user_message", "response"},
        produces={"emotion_state", "emotion_style", "pad_vector", "emotional_shift"},
    ),
    "impulse_update": PhaseContract(
        name="impulse_update",
        requires={"user_message"},
        produces={"impulse_updated", "impulse_state", "impulse_primary", "experience_interaction_type", "experience_significance"},
    ),
    "events_broadcast": PhaseContract(
        name="events_broadcast",
        requires={"confidence", "rag_used", "intent"},
    ),
    "response_guard": PhaseContract(
        name="response_guard",
        requires={"response", "call_count", "confidence"},
        produces={"response"},
        optional_produces={"cognition"},
    ),
    "memory_maintenance": PhaseContract(
        name="memory_maintenance",
        produces={"fusion", "forgetting"},
    ),
}


class ContractValidator:
    MODE_SOFT = "soft"
    MODE_STRICT = "strict"

    def __init__(self, mode: str = MODE_SOFT):
        self.mode = mode
        self._violations: list[str] = []

    @property
    def violations(self) -> list[str]:
        return list(self._violations)

    @property
    def has_violations(self) -> bool:
        return len(self._violations) > 0

    def pre_check(self, phase_name: str, ctx_keys: set) -> list[str]:
        contract = FOREGROUND_CONTRACTS.get(phase_name)
        if not contract:
            return []
        missing = contract.requires - ctx_keys
        if not missing:
            return []
        msg = f"[{phase_name}] Missing required keys: {missing}"
        self._violations.append(msg)
        if self.mode == self.MODE_STRICT:
            raise ContractViolationError(msg)
        logger.warning(msg)
        return [msg]

    def post_check(self, phase_name: str, produced: set) -> list[str]:
        contract = FOREGROUND_CONTRACTS.get(phase_name)
        if not contract:
            return []
        expected = contract.requires | contract.produces | contract.optional_produces
        unexpected = produced - expected
        if not unexpected:
            return []
        msg = f"[{phase_name}] Unexpected keys written: {unexpected}"
        self._violations.append(msg)
        if self.mode == self.MODE_STRICT:
            raise ContractViolationError(msg)
        logger.warning(msg)
        return [msg]

    def get_report(self) -> str:
        if not self._violations:
            return "ContractValidator: 0 violations"
        lines = [f"ContractValidator: {len(self._violations)} violation(s):"]
        for v in self._violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


class ContractViolationError(RuntimeError):
    pass
