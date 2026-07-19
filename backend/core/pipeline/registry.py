from collections import OrderedDict
from typing import List, Tuple, Optional


PHASE_DESCRIPTIONS: dict[str, str] = {
    "safety": "Проверка входящего сообщения на безопасность (инжекты, токсичность)",
    "intent": "Классификация намерения пользователя: chat_general, deep_reasoning, creative и т.д.",
    "rag": "Поиск релевантных фактов в векторной памяти (Retrieval-Augmented Generation)",
    "knowledge_graph": "Поиск связанных концептов в графе знаний",
    "episodic": "Восстановление похожих прошлых диалогов (эпизодическая память)",
    "semantic": "Проверка готовой процедуры/сценария под задачу (семантическая память)",
    "emotion": "Определение эмоционального стиля ответа через PAD-модель",
    "impulse": "Применение текущего когнитивного искажения (impulse-bias)",
    "persona": "Формирование контекста персоны — текущее состояние личности AI",
    "roots": "Загрузка базовых принципов и ценностей личности AI",
    "identity": "Генерация ответа LLM с учётом identity-контекста",
    "generate": "Основная генерация ответа через OpenRouter / GigaChat",
    "truth_loop": "Верификация фактов в сгенерированном ответе (TruthLoop)",
    "evaluation": "Оценка качества ответа: completeness, consistency, safety, confidence",
    "response_guard": "Финальная проверка ответа перед отправкой пользователю",
    "save_episode": "Сохранение диалога как эпизода в episodic memory",
    "extraction": "Извлечение сущностей из диалога в граф знаний",
    "emotion_update": "Обновление эмоционального состояния AI на основе ответа",
    "impulse_update": "Обновление активных когнитивных искажений",
    "persona_evolution": "Эволюция персоны — обучение на каждом ответе (Meta-Learning)",
    "events_broadcast": "Рассылка событий через WebSocket (live-обновления)",
    "health": "Обновление health score системы",
    "reflection": "Рефлексия: анализ успешности ответа, Meta-Learning",
    "dreams": "Запись 'снов' — консолидация краткосрочной памяти в долгосрочную",
    "metrics": "Запись метрик: latency, токены, ошибки для мониторинга",
}


class PhaseRegistry:
    def __init__(self):
        self._phases: OrderedDict[str, type] = OrderedDict()
        self._orders: dict[str, int] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, phase_class: type, order: Optional[int] = None, description: str = "") -> None:
        self._phases[name] = phase_class
        if order is not None:
            self._orders[name] = order
        if description:
            self._descriptions[name] = description

    def build(self, skip: set | None = None) -> List[Tuple[str, object]]:
        skip = skip or set()
        ordered = sorted(
            self._phases.items(),
            key=lambda kv: self._orders.get(kv[0], 9999),
        )
        result = []
        for name, cls in ordered:
            if name in skip:
                continue
            result.append((name, cls()))
        return result

    def get_class(self, name: str) -> Optional[type]:
        return self._phases.get(name)

    def list_names(self) -> List[str]:
        return list(self._phases.keys())

    def list_details(self) -> list[dict]:
        ordered = sorted(
            self._phases.items(),
            key=lambda kv: self._orders.get(kv[0], 9999),
        )
        result = []
        for name, cls in ordered:
            order = self._orders.get(name)
            desc = self._descriptions.get(name) or PHASE_DESCRIPTIONS.get(name, "")
            is_background = order is not None and order >= 15 if order is not None else False
            result.append({
                "name": name,
                "order": order,
                "description": desc,
                "background": is_background,
                "class_name": cls.__name__,
            })
        return result

    def __contains__(self, name: str) -> bool:
        return name in self._phases


_global_registry: Optional[PhaseRegistry] = None


def get_registry() -> PhaseRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = PhaseRegistry()
    return _global_registry


def register_phase(name: str, order: Optional[int] = None):
    def decorator(cls):
        get_registry().register(name, cls, order=order)
        return cls
    return decorator
