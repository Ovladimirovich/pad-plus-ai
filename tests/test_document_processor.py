import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from core.document_processor import (
    extract_text_from_txt,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_pptx,
    chunk_text,
    get_extractor,
    DocumentChunk,
)


class TestTextExtraction:
    def test_extract_txt(self):
        text = extract_text_from_txt(b"Hello World")
        assert text == "Hello World"

    def test_extract_txt_unicode(self):
        text = extract_text_from_txt("Привет мир".encode("utf-8"))
        assert "Привет мир" in text

    def test_extract_txt_corrupt_bytes(self):
        text = extract_text_from_txt(b"\xff\xfe\x00\x01")
        assert isinstance(text, str)

    def test_get_extractor_supported(self):
        extractor = get_extractor(".pdf")
        assert callable(extractor)

    def test_get_extractor_unsupported(self):
        with pytest.raises(ValueError, match="Неподдерживаемый формат"):
            get_extractor(".xyz")

    def test_get_extractor_case_insensitive(self):
        extractor = get_extractor(".PDF")
        assert callable(extractor)


class TestChunking:
    def test_chunk_small_text(self):
        text = "hello world"
        chunks = chunk_text(text, chunk_size=10, overlap=2)
        assert len(chunks) == 1
        assert chunks[0].content == "hello world"

    def test_chunk_large_text(self):
        words = ["word"] * 50
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=10, overlap=2)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c.content.split()) <= 10

    def test_chunk_overlap(self):
        words = [str(i) for i in range(20)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=10, overlap=3)
        assert len(chunks) >= 2
        last_chunk_words = chunks[-1].content.split()
        assert all(w in words for w in last_chunk_words)

    def test_chunk_empty_text(self):
        chunks = chunk_text("")
        assert chunks == []

    def test_chunk_whitespace_only(self):
        chunks = chunk_text("   \n\n   ")
        assert chunks == []

    def test_chunk_exact_fit(self):
        words = ["word"] * 10
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=10, overlap=0)
        assert len(chunks) == 1

    def test_chunk_index_sequential(self):
        text = "word " * 30
        chunks = chunk_text(text.strip(), chunk_size=10, overlap=2)
        for i, c in enumerate(chunks):
            assert c.index == i


class TestDocumentChunkModel:
    def test_dataclass_fields(self):
        chunk = DocumentChunk(index=0, content="test")
        assert chunk.index == 0
        assert chunk.content == "test"

    def test_dataclass_immutable_like(self):
        chunk = DocumentChunk(index=1, content="hello")
        assert repr(chunk) == "DocumentChunk(index=1, content='hello')"
