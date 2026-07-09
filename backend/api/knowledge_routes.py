"""
Knowledge Graph API — доступ к графу знаний.
"""

from fastapi import APIRouter, Query, Body, HTTPException, Depends
from typing import Optional, Dict, Any, List
import logging
import os
import struct
import httpx

logger = logging.getLogger("padplus.knowledge")

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Graph"])

from core.auth_manager import get_current_user


def get_graph():
    from knowledge.graph import get_knowledge_graph
    return get_knowledge_graph()


@router.post("/concepts")
async def create_concept(body: dict = Body(...)):
    """Добавить концепцию в граф знаний.
    Принимает JSON: {"name": "...", "type": "concept", "confidence": 0.5, "source": "user"}"""
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Поле 'name' обязательно")
    # Фронтенд шлёт "type", API хранит как "concept_type"
    concept_type = body.get("type") or body.get("concept_type", "concept")
    confidence = body.get("confidence", 0.5)
    source = body.get("source", "user")
    metadata = body.get("metadata") or {}
    graph = get_graph()
    existing = graph.find_concepts(name, limit=1)
    if existing and existing[0].name.lower() == name.lower():
        c = existing[0]
        return {"concept": c.to_dict(), "message": "Концепция уже существует"}
    try:
        c = graph.add_concept(name, concept_type=concept_type, confidence=confidence, source=source, metadata=metadata)
        return {"concept": c.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concepts/batch")
async def create_concepts_batch(
    concepts: List[dict] = Body(...),
):
    """Добавить несколько концепций сразу"""
    graph = get_graph()
    results = []
    for item in concepts:
        name = item.get("name", "")
        if not name:
            continue
        existing = graph.find_concepts(name, limit=1)
        if existing and existing[0].name.lower() == name.lower():
            results.append({"concept": existing[0].to_dict(), "skipped": True})
            continue
        c = graph.add_concept(
            name=name,
            concept_type=item.get("type", "concept"),
            confidence=item.get("confidence", 0.5),
            source=item.get("source", "user"),
            metadata=item.get("metadata", {}),
        )
        results.append({"concept": c.to_dict(), "skipped": False})
    return {"concepts": results, "total": len(results)}


@router.post("/relations")
async def create_relation(
    source_id: str = Body(...),
    target_id: str = Body(...),
    relation_type: str = Body(default="related"),
    weight: float = Body(default=1.0, ge=0, le=5),
    confidence: float = Body(default=0.5, ge=0, le=1),
):
    """Добавить связь между концепциями"""
    graph = get_graph()
    r = graph.add_relation(source_id, target_id, relation_type=relation_type, weight=weight, confidence=confidence)
    if r is None:
        raise HTTPException(status_code=400, detail="Одна из концепций не найдена")
    return {"relation": r.to_dict()}


@router.post("/extract")
async def extract_from_text(text: str = Body(..., embed=True)):
    """Извлечь концепции и связи из текста"""
    graph = get_graph()
    try:
        from knowledge.extractor import extract_and_add
        result = extract_and_add(text, graph)
        return result
    except ImportError:
        pass
    # Fallback: simple extraction
    concepts_added = _simple_extract(text, graph)
    stats = graph.get_stats()
    return {"concepts_added": concepts_added, "stats": stats, "method": "simple"}


def _simple_extract(text: str, graph) -> int:
    """Простое извлечение: ключевые слова из текста"""
    import re, uuid
    # Tokenize by non-alpha separators, filter short words
    words = re.findall(r'[А-Яа-яA-Za-z]{3,}', text)
    # Frequency
    freq = {}
    for w in words:
        w_l = w.lower()
        if w_l in ("это", "что", "как", "для", "все", "еще", "при", "или",
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
                     "часто", "вместе", "похожи", "потом", "почти"):
            continue
        if len(w_l) < 3:
            continue
        freq[w_l] = freq.get(w_l, 0) + 1

    # Add top frequent words as concepts
    added = 0
    for word, count in sorted(freq.items(), key=lambda x: -x[1])[:15]:
        if count < 2:
            continue
        existing = graph.find_concepts(word, limit=1)
        if existing and existing[0].name.lower() == word.lower():
            continue
        # Determine type based on casing
        ctype = "entity" if word[0].isupper() else "concept"
        graph.add_concept(
            name=word,
            concept_type=ctype,
            confidence=min(0.3 + count * 0.05, 0.9),
            source="extraction",
        )
        added += 1
    return added


@router.get("/search")
async def search_concepts(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Поиск концепций в графе знаний"""
    try:
        from knowledge.graph import get_knowledge_graph
        graph = get_knowledge_graph()
        concepts = graph.find_concepts(q, limit=limit)
        return {
            "query": q,
            "concepts": [c.to_dict() for c in concepts],
            "total": len(concepts),
        }
    except Exception as e:
        logger.error(f"Knowledge graph search error: {e}")
        return {"query": q, "concepts": [], "total": 0, "error": str(e)}


@router.get("/related/{concept_id}")
async def get_related_concepts(
    concept_id: str,
    depth: int = Query(default=1, ge=1, le=3)
):
    """Связанные концепции"""
    try:
        from knowledge.graph import get_knowledge_graph
        graph = get_knowledge_graph()
        related = graph.get_related(concept_id, depth=depth)
        concept = graph.get_concept(concept_id)
        return {
            "concept": concept.to_dict() if concept else None,
            "related": [r.to_dict() for r in related],
            "total": len(related),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/stats")
async def get_knowledge_stats():
    """Статистика графа знаний"""
    try:
        from knowledge.graph import get_knowledge_graph
        graph = get_knowledge_graph()
        stats = graph.get_stats()
        return stats
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.get("/graph")
async def get_full_graph(limit: int = Query(default=50, ge=1, le=200)):
    """Полный граф для визуализации"""
    try:
        from knowledge.graph import get_knowledge_graph
        graph = get_knowledge_graph()
        full = graph.to_dict()
        nodes = full.get("nodes", [])[:limit]
        edges = full.get("links", [])
        edge_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e.get("source") in edge_ids and e.get("target") in edge_ids][:limit * 2]
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}


@router.get("/semantic-search")
async def semantic_search(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(default=10, ge=1, le=50, description="Макс. результатов"),
    threshold: float = Query(default=0.3, ge=0.0, le=1.0, description="Порог сходства (cosine)"),
):
    """Семантический поиск концепций по смыслу (vector similarity)"""
    try:
        from knowledge.graph import get_knowledge_graph
        graph = get_knowledge_graph()
        results = graph.semantic_search(query=q, limit=limit, similarity_threshold=threshold)
        return {
            "query": q,
            "concepts": results,
            "total": len(results),
            "method": "vector_similarity" if results else "fallback",
        }
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return {"query": q, "concepts": [], "total": 0, "error": str(e)}


@router.post("/recompute-embeddings")
async def recompute_embeddings(
    limit: int = Query(default=100, ge=1, le=500, description="Макс. концепций для обработки"),
    current_user: dict = Depends(get_current_user)
):
    """Перегенерация эмбеддингов для всех концепций (если их нет или устарели).
    Использует OpenRouter ключ текущего пользователя из его сохранённых провайдеров."""
    try:
        from knowledge.graph import get_knowledge_graph
        from core.supabase_client import get_supabase
        from core.encryption import get_encryptor
        import httpx
        import struct

        # Получаем пользователя и его ключи
        supabase = get_supabase()
        encryptor = get_encryptor()
        user_id = current_user["id"]

        # Ищем OpenRouter ключ пользователя
        api_key = None
        result = supabase.table("user_api_keys")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("provider", "openrouter")\
            .eq("is_active", True)\
            .execute()

        if not result.data:
            return {"status": "error", "message": "OpenRouter ключ не найден. Добавьте ключ в настройках (⚡)."}

        key_data = result.data[0]
        raw_key = encryptor.decrypt(key_data["api_key_encrypted"])
        api_key = raw_key.strip().encode("ascii", errors="ignore").decode("ascii")

        graph = get_knowledge_graph()
        concepts = list(graph._concepts.values())
        if not concepts:
            return {"status": "ok", "message": "Граф пуст", "updated": 0}

        updated = 0
        failed = 0

        for concept in concepts[:limit]:
            if concept.metadata.get("embedding"):
                continue  # уже есть

            try:
                response = httpx.post(
                    "https://openrouter.ai/api/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": "text-embedding-3-small", "input": concept.name},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                emb = data["data"][0]["embedding"]

                # Обновляем в памяти
                concept.metadata["embedding"] = emb

                # Обновляем в Supabase
                if graph._use_supabase:
                    try:
                        graph._supabase_table("knowledge_concepts").update({"embedding": emb}).eq("id", concept.id).execute()
                    except Exception as e:
                        logger.warning(f"Supabase update embedding failed for {concept.id}: {e}")

                # Обновляем в SQLite
                if not graph._use_supabase and os.path.exists(graph.db_path):
                    import sqlite3
                    import json
                    emb_bytes = struct.pack(f"{len(emb)}f", *emb)
                    conn = sqlite3.connect(graph.db_path)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE concepts SET embedding = ? WHERE id = ?", (emb_bytes, concept.id))
                    conn.commit()
                    conn.close()

                updated += 1

            except Exception as e:
                logger.warning(f"Embedding generation failed for {concept.name}: {e}")
                failed += 1

        return {"status": "ok", "updated": updated, "failed": failed, "total_checked": min(len(concepts), limit)}

    except Exception as e:
        logger.error(f"Recompute embeddings error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/concepts/{concept_id}/merge")
async def merge_concepts(
    concept_id: str,
    target_id: str = Body(..., embed=True),
):
    """Объединить две концепции: concept_id вливается в target_id.
    Все связи concept_id переносятся на target_id, затем concept_id удаляется."""
    graph = get_graph()
    source = graph.get_concept(concept_id)
    target = graph.get_concept(target_id)

    if not source or not target:
        raise HTTPException(status_code=404, detail="Одна из концепций не найдена")
    if concept_id == target_id:
        raise HTTPException(status_code=400, detail="Нельзя объединить концепцию саму с собой")

    try:
        # Переносим все связи source -> target
        for rel in list(graph._relations):
            if rel.source_id == concept_id:
                # source -> X  ==>  target -> X
                if rel.target_id != target_id:  # не создавать петлю
                    graph.add_relation(target_id, rel.target_id, rel.relation_type, rel.weight, rel.confidence)
            elif rel.target_id == concept_id:
                # X -> source  ==>  X -> target
                if rel.source_id != target_id:
                    graph.add_relation(rel.source_id, target_id, rel.relation_type, rel.weight, rel.confidence)

        # Удаляем source
        if graph._use_supabase:
            try:
                graph._supabase_table("knowledge_concepts").delete().eq("id", concept_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete concept error: {e}")

        # Удаляем из SQLite (relations удалятся каскадно через FK, концепцию)
        if not graph._use_supabase:
            import sqlite3
            conn = sqlite3.connect(graph.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM concepts WHERE id = ?", (concept_id,))
            conn.commit()
            conn.close()

        # Удаляем из памяти
        if concept_id in graph._concepts:
            del graph._concepts[concept_id]
        if graph.graph and graph.graph.has_node(concept_id):
            graph.graph.remove_node(concept_id)

        return {"status": "ok", "merged": concept_id, "into": target_id, "target": target.to_dict()}
    except Exception as e:
        logger.error(f"Merge concepts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/concepts/{concept_id}")
async def delete_concept(concept_id: str):
    """Удалить концепцию и все её связи."""
    graph = get_graph()
    concept = graph.get_concept(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Концепция не найдена")

    try:
        # Удаляем связи
        graph._relations = [r for r in graph._relations if r.source_id != concept_id and r.target_id != concept_id]

        if graph._use_supabase:
            try:
                graph._supabase_table("knowledge_relations").delete().or_(f"source_id.eq.{concept_id},target_id.eq.{concept_id}").execute()
                graph._supabase_table("knowledge_concepts").delete().eq("id", concept_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete error: {e}")

        if not graph._use_supabase:
            import sqlite3
            conn = sqlite3.connect(graph.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM relations WHERE source_id = ? OR target_id = ?", (concept_id, concept_id))
            cursor.execute("DELETE FROM concepts WHERE id = ?", (concept_id,))
            conn.commit()
            conn.close()

        if concept_id in graph._concepts:
            del graph._concepts[concept_id]
        if graph.graph and graph.graph.has_node(concept_id):
            graph.graph.remove_node(concept_id)

        return {"status": "ok", "deleted": concept_id}
    except Exception as e:
        logger.error(f"Delete concept error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/relations")
async def update_relation(
    source_id: str = Body(...),
    target_id: str = Body(...),
    relation_type: str = Body(...),
    weight: float = Body(default=1.0, ge=0, le=5),
    confidence: float = Body(default=0.5, ge=0, le=1),
):
    """Обновить/создать связь между концепциями."""
    graph = get_graph()

    try:
        # Удаляем старую связь если есть
        graph._relations = [r for r in graph._relations if not (r.source_id == source_id and r.target_id == target_id)]

        # Добавляем новую
        r = graph.add_relation(source_id, target_id, relation_type, weight, confidence)
        if not r:
            raise HTTPException(status_code=400, detail="Одна из концепций не найдена")

        return {"relation": r.to_dict()}
    except Exception as e:
        logger.error(f"Update relation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
