"""
⚖️ Constitution Layer — неизменяемый слой правил PAD+ AI.

Фильтрует все изменения стратегии и поведения перед применением.
Состоит из:
- AntiDirective — ядро, запрет абсолютизма
- Roots — корневые принципы
- Bounds — допустимые границы изменений
"""

from .validator import ConstitutionValidator

__all__ = ["ConstitutionValidator"]
