"""Поиск по графу знаний: концепции + связи → контекст для LLM."""

from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("padplus.knowledge.search")


def find_related_triples(
    query: str,
    concept_limit: int = 5,
    relation_limit: int = 8,
    graph=None,
) -> Tuple[List[str], str]:
    """Найти концепции по запросу, собрать связи, вернуть (список имён, форматированный контекст).

    Args:
        query: поисковый запрос (сообщение пользователя)
        concept_limit: макс. концепций для поиска
        relation_limit: макс. triples для контекста
        graph: экземпляр KnowledgeGraph (если None — берётся глобальный)

    Returns:
        (список имён найденных концепций, строка вида "Концепция → тип_связи → Другая")
    """
    if graph is None:
        from knowledge.graph import get_knowledge_graph

        graph = get_knowledge_graph()
    concepts = graph.find_concepts(query, limit=concept_limit)
    if not concepts:
        return [], ""

    concept_ids = {c.id for c in concepts}
    concept_names = [c.name for c in concepts]

    all_concepts = graph.get_all_concepts()
    all_relations = graph.get_all_relations()

    triples: List[Tuple[str, str, str]] = []
    seen: set = set()

    for rel in all_relations:
        src = all_concepts.get(rel.source_id)
        tgt = all_concepts.get(rel.target_id)
        if not src or not tgt:
            continue
        src_name = src.name
        tgt_name = tgt.name

        # Нужна хотя бы одна концепция из найденных
        if rel.source_id in concept_ids or rel.target_id in concept_ids:
            key = (src_name, rel.relation_type, tgt_name)
            if key not in seen:
                seen.add(key)
                triples.append(key)
                if len(triples) >= relation_limit:
                    break

    if not triples:
        return concept_names, ""

    lines = ["Знания из графа:"]
    for src, rel_type, tgt in triples:
        lines.append(f"- {src} → {rel_type} → {tgt}")

    context = "\n".join(lines)
    return concept_names, context


def search_concepts(query: str, limit: int = 10, graph=None) -> List[str]:
    """Простой поиск имён концепций по запросу."""
    if graph is None:
        from knowledge.graph import get_knowledge_graph

        graph = get_knowledge_graph()
    return [c.name for c in graph.find_concepts(query, limit=limit)]
