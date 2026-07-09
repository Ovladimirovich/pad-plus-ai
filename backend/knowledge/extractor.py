"""
Извлечение концепций и связей из текста.
"""

import re
import logging
from typing import Dict, List, Set, Tuple
from collections import Counter

logger = logging.getLogger("padplus.knowledge.extractor")

STOPWORDS = {
    "это", "что", "как", "для", "все", "еще", "при", "или",
    "the", "and", "for", "are", "but", "not", "you", "all",
    "can", "had", "her", "was", "one", "our", "out", "has",
    "have", "been", "some", "with", "from", "that", "this",
    "they", "will", "more", "than", "also", "very", "just",
    "such", "each", "well", "even", "down", "back", "may",
    "into", "over", "then", "many", "them", "these", "much",
    "about", "other", "after", "first", "would", "could",
    "which", "their", "there", "should", "between",
    "такие", "также", "кроме", "поэто", "может", "котор",
    "через", "чтобы", "когда", "всего", "самое", "тогда",
    "часто", "вместе", "похожи", "потом", "почти",
    "является", "называется", "используется", "связан",
    "представляет", "содержит", "включает", "состоит",
}

RELATION_PATTERNS = [
    (re.compile(r"\b(?:это|является|представляет\s+собой)\s+(\w+)\b"), "is_a"),
    (re.compile(r"\b(\w+)\s+(?:это|является|представляет\s+собой)\b"), "is_a"),
    (re.compile(r"\b(?:использует|применяет|применяется)\s+(\w+)\b"), "uses"),
    (re.compile(r"\b(\w+)\s+(?:используется|применяется)\b"), "used_by"),
    (re.compile(r"\b(?:содержит|включает|состоит\s+из)\s+(\w+)\b"), "contains"),
    (re.compile(r"\b(?:входит\s+в|часть)\s+(\w+)\b"), "part_of"),
    (re.compile(r"\b(?:основан|базируется)\s+на\s+(\w+)\b"), "based_on"),
    (re.compile(r"\b(?:отличается|отличие)\s+от\s+(\w+)\b"), "differs_from"),
    (re.compile(r"\b(?:похож|аналогичен|схож)\s+(?:на\s+)?(\w+)\b"), "similar_to"),
    (re.compile(r"\b(?:лучше|быстрее|эффективнее)\s+(?:чем\s+)?(\w+)\b"), "better_than"),
]

TECH_SUFFIXES = ("ция", "ние", "тие", "сть", "тор", "тер", "ор", "ер", "изм", "ика")


def extract_keywords(text: str, min_freq: int = 2, max_keywords: int = 20) -> List[Tuple[str, int, str]]:
    """Извлекает ключевые слова из текста"""
    words = re.findall(r'[А-Яа-яA-Za-z]{3,}', text)
    counter = Counter()
    for w in words:
        wl = w.lower()
        if wl in STOPWORDS or len(wl) < 3:
            continue
        counter[wl] += 1

    results = []
    for word, count in counter.most_common(max_keywords * 2):
        if count < min_freq:
            continue
        ctype = _guess_type(word)
        results.append((word, count, ctype))
        if len(results) >= max_keywords:
            break
    return results


def _guess_type(word: str) -> str:
    """Определяет тип концепции по слову"""
    if word[0].isupper():
        return "entity"
    for suffix in TECH_SUFFIXES:
        if word.endswith(suffix) and len(word) > 5:
            return "concept"
    return "concept"


def extract_relations(text: str, concepts: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Извлекает связи между концепциями на основе шаблонов"""
    found = []
    text_lower = text.lower()
    concept_names = sorted(concepts.keys(), key=len, reverse=True)

    for i, name_a in enumerate(concept_names):
        if name_a not in text_lower:
            continue
        for name_b in concept_names[i + 1:]:
            if name_b not in text_lower:
                continue
            # Check if they co-occur in the same sentence
            sentences = re.split(r'[.!?]+', text_lower)
            for sent in sentences:
                if name_a in sent and name_b in sent:
                    # Try to determine relation type from context
                    rtype = _find_relation_type(sent, name_a, name_b)
                    found.append((concepts[name_a], concepts[name_b], rtype))
                    break
    # Deduplicate
    seen = set()
    unique = []
    for s, t, r in found:
        key = (s, t, r)
        if key not in seen:
            seen.add(key)
            unique.append((s, t, r))
    return unique


def _find_relation_type(sentence: str, name_a: str, name_b: str) -> str:
    """Определяет тип связи по контексту предложения"""
    for pattern, rel_type in RELATION_PATTERNS:
        if pattern.search(sentence):
            return rel_type
    return "related"


def extract_and_add(text: str, graph) -> dict:
    """Извлекает концепции и связи из текста и добавляет в граф"""
    from knowledge.graph import Concept

    min_freq = 1 if len(text) < 500 else 2
    keywords = extract_keywords(text, min_freq=min_freq)
    concepts_added = 0
    name_to_id = {}

    for word, count, ctype in keywords:
        confidence = min(0.3 + count * 0.05, 0.9)
        existing = graph.find_concepts(word, limit=1)
        if existing and existing[0].name.lower() == word.lower():
            name_to_id[word] = existing[0].id
            continue
        c = graph.add_concept(
            name=word,
            concept_type=ctype,
            confidence=confidence,
            source="extraction",
        )
        name_to_id[word] = c.id
        concepts_added += 1

    relations_found = extract_relations(text, name_to_id)
    relations_added = 0
    for src_id, tgt_id, rtype in relations_found:
        r = graph.add_relation(src_id, tgt_id, relation_type=rtype, confidence=0.4)
        if r:
            relations_added += 1

    return {
        "concepts_added": concepts_added,
        "relations_added": relations_added,
        "total_concepts": len(name_to_id),
        "total_relations": len(relations_found),
    }
