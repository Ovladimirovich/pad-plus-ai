"""
Тесты для функции маскирования API-ключей `mask_api_key`.
"""

import pytest
from core.encryption import mask_api_key


class TestMaskApiKey:
    """Проверка безопасного маскирования API-ключей для логирования."""

    def test_long_key_masked(self):
        """Длинный ключ показывается только головой и хвостом, середина скрыта."""
        key = "sk-or-v1-0123456789abcdef0123456789abcdef"
        masked = mask_api_key(key)
        assert masked.startswith("sk-or-")
        assert masked.endswith("cdef")
        assert "0123456789" not in masked

    def test_short_key_fully_masked(self):
        """Ключ короче видимых частей скрывается целиком звёздочками."""
        masked = mask_api_key("abc")
        assert masked == "*" * 3
        assert "abc" not in masked

    def test_empty_key(self):
        """Пустой ключ возвращает специальную метку."""
        assert mask_api_key("") == "(пусто)"
        assert mask_api_key(None) == "(пусто)"

    def test_result_not_contain_full_key(self):
        """Полный ключ никогда не присутствует в выводе."""
        full = "sk-or-v1-abcdef1234567890"
        masked = mask_api_key(full)
        assert full not in masked

    def test_custom_visible_parts(self):
        """Уважается кастомный размер видимых частей."""
        masked = mask_api_key("abcdefghijkl", visible_head=2, visible_tail=2)
        assert masked == "ab…kl"