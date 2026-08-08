"""Тесты для core/encryption.py — шифрование API ключей"""

import pytest

from core.encryption import (
    KeyEncryptor,
    generate_encryption_key,
    get_encryptor,
    initialize_encryptor,
    mask_api_key,
)


@pytest.fixture
def encryptor():
    """KeyEncryptor с тестовым ключом"""
    return KeyEncryptor("test-encryption-key-32-characters-long")


class TestKeyEncryptor:
    def test_encrypt_decrypt_roundtrip(self, encryptor):
        """Шифрование и дешифрование возвращают оригинальный ключ"""
        api_key = "sk-openrouter-abcdef1234567890"
        encrypted = encryptor.encrypt(api_key)
        assert encrypted != api_key
        assert encryptor.decrypt(encrypted) == api_key

    def test_encrypt_produces_unique_ciphertext(self, encryptor):
        """Fernet использует случайный nonce — два шифрования дают разные ciphertext"""
        api_key = "sk-test-key"
        e1 = encryptor.encrypt(api_key)
        e2 = encryptor.encrypt(api_key)
        assert e1 != e2
        assert encryptor.decrypt(e1) == api_key
        assert encryptor.decrypt(e2) == api_key

    def test_decrypt_empty_returns_empty(self, encryptor):
        """Пустой ключ возвращает пустую строку"""
        assert encryptor.decrypt("") == ""
        assert encryptor.decrypt("None") == ""

    def test_decrypt_invalid_returns_empty(self, encryptor):
        """Мусор в зашифрованном — возвращает пустую строку без исключения"""
        assert encryptor.decrypt("not-a-valid-fernet-token-xxx") == ""

    def test_decrypt_strips_non_ascii(self, encryptor):
        """\xa0 (неразрывный пробел) удаляется из ключа при дешифровке"""
        original = "sk-abc123def456"
        dirty = original.replace("c", "\xa0")  # вносим невидимый символ
        encrypted = encryptor.encrypt(dirty)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == "sk-ab123def456"  # символ 'c' (с \xa0) вырезан

    def test_verify_matches(self, encryptor):
        """verify возвращает True для совпадающего ключа"""
        original = "sk-test-key-123"
        encrypted = encryptor.encrypt(original)
        assert encryptor.verify(encrypted, original) is True

    def test_verify_mismatch(self, encryptor):
        """verify возвращает False для неподошедшего ключа"""
        encrypted = encryptor.encrypt("sk-original-key")
        assert encryptor.verify(encrypted, "sk-other-key") is False

    def test_fallback_mode_on_bad_key(self, monkeypatch):
        """При невалидном ключе шифрования — fallback без сбоя"""
        enc = KeyEncryptor("")  # пустой ключ не должен кидаться
        assert enc is not None


class TestMaskApiKey:
    def test_empty(self):
        assert mask_api_key("") == "(пусто)"
        assert mask_api_key(None) == "(пусто)"

    def test_short_key_masked_completely(self):
        assert mask_api_key("abc1234") == "*******"

    def test_normal_key_visible_head_tail(self):
        assert mask_api_key("sk-abcdefghijklmnop") == "sk-abc…mnop"

    def test_custom_params(self):
        assert mask_api_key("0123456789", visible_head=2, visible_tail=2) == "01…89"


class TestGlobalEncryptor:
    def test_generate_encryption_key(self):
        """generate_encryption_key возвращает валидный Fernet ключ"""
        key = generate_encryption_key()
        assert len(key) > 20

    def test_get_encryptor_requires_env_key(self, monkeypatch):
        """get_encryptor требует ENCRYPTION_KEY из окружения"""
        import core.encryption as enc_mod

        previous = enc_mod._encryptor
        enc_mod._encryptor = None  # сбрасываем синглтон
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        try:
            with pytest.raises(ValueError):
                get_encryptor()
        finally:
            enc_mod._encryptor = previous

    def test_get_encryptor_singleton(self, monkeypatch):
        """get_encryptor возвращает один и тот же инстанс"""
        import core.encryption as enc_mod

        previous = enc_mod._encryptor
        enc_mod._encryptor = None
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key-32-characters-long")
        try:
            e1 = get_encryptor()
            e2 = get_encryptor()
            assert e1 is e2
        finally:
            enc_mod._encryptor = previous

    def test_initialize_encryptor_sets_global(self):
        """initialize_encryptor явно инициализирует синглтон"""
        import core.encryption as enc_mod

        previous = enc_mod._encryptor
        try:
            e = initialize_encryptor("init-key-for-test-32-characters")
            assert enc_mod._encryptor is e
        finally:
            enc_mod._encryptor = previous