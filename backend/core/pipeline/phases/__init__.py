"""
Pipeline phases registry.
"""

from .anti_loop import AntiLoopPhase
from .safety import SafetyPhase
from .intent import IntentPhase
from .rag import RagPhase
from .knowledge_graph import KnowledgeGraphPhase
from .episodic import EpisodicPhase
from .semantic import SemanticPhase
from .emotion import EmotionPhase
from .impulse import ImpulsePhase
from .persona import PersonaPhase
from .roots import RootsPhase
from .identity import IdentityPhase
from .generate import GeneratePhase
from .truth_loop import TruthLoopPhase
from .save_episode import SaveEpisodePhase
from .extraction import ExtractionPhase
from .emotion_update import EmotionUpdatePhase
from .impulse_update import ImpulseUpdatePhase
from .persona_evolution import PersonaEvolutionPhase
from .events import EventsBroadcastPhase
from .health import HealthMonitorPhase
from .reflection import ReflectionPhase
from .dreams import DreamsPhase
from .metrics import MetricsPhase
from .response_guard import ResponseGuardPhase
from .evaluation import EvaluationPhase

__all__ = [
    "AntiLoopPhase",
    "SafetyPhase",
    "IntentPhase",
    "RagPhase",
    "KnowledgeGraphPhase",
    "EpisodicPhase",
    "SemanticPhase",
    "EmotionPhase",
    "ImpulsePhase",
    "PersonaPhase",
    "RootsPhase",
    "IdentityPhase",
    "GeneratePhase",
    "TruthLoopPhase",
    "SaveEpisodePhase",
    "ExtractionPhase",
    "EmotionUpdatePhase",
    "ImpulseUpdatePhase",
    "PersonaEvolutionPhase",
    "EventsBroadcastPhase",
    "HealthMonitorPhase",
    "ReflectionPhase",
    "DreamsPhase",
    "MetricsPhase",
    "ResponseGuardPhase",
    "EvaluationPhase",
]
