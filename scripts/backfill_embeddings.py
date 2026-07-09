"""Бэкфилл эмбеддингов для существующих концепций."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
backend_path = str(project_root / "backend")
sys.path.insert(0, backend_path)

from knowledge.graph import get_knowledge_graph
from core.config_manager import get_openrouter_key
import httpx
import struct


def generate_embedding(text: str) -> list[float] | None:
    """Генерирует embedding через OpenRouter."""
    api_key = get_openrouter_key()
    if not api_key:
        return None
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "text-embedding-3-small", "input": text},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        print(f"  ❌ Embedding failed for '{text}': {e}")
        return None


def backfill_sqlite(db_path: str):
    """Обновляет эмбеддинги в локальной SQLite."""
    import sqlite3
    import json

    if not os.path.exists(db_path):
        print(f"SQLite не найден: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, metadata FROM concepts WHERE embedding IS NULL OR embedding = ''")
    rows = cursor.fetchall()

    print(f"Найдено концепций без эмбеддингов в SQLite: {len(rows)}")

    updated = 0
    for row in rows:
        emb = generate_embedding(row["name"])
        if emb:
            emb_bytes = struct.pack(f"{len(emb)}f", *emb)
            cursor.execute("UPDATE concepts SET embedding = ? WHERE id = ?", (emb_bytes, row["id"]))
            updated += 1
            print(f"  ✅ {row['name']} ({row['id']})")

    conn.commit()
    conn.close()
    print(f"Обновлено в SQLite: {updated}")


def backfill_supabase():
    """Обновляет эмбеддинги в Supabase через REST API."""
    from core.supabase_client import get_supabase_service

    client = get_supabase_service()
    if not client:
        print("Supabase client недоступен")
        return

    # Получаем все концепции
    resp = client.table("knowledge_concepts").select("id,name,embedding").execute()
    concepts = resp.data or []

    no_emb = [c for c in concepts if not c.get("embedding")]
    print(f"Найдено концепций без эмбеддингов в Supabase: {len(no_emb)}")

    updated = 0
    for c in no_emb:
        emb = generate_embedding(c["name"])
        if emb:
            try:
                client.table("knowledge_concepts").update({"embedding": emb}).eq("id", c["id"]).execute()
                updated += 1
                print(f"  ✅ {c['name']} ({c['id']})")
            except Exception as e:
                print(f"  ❌ {c['name']}: {e}")

    print(f"Обновлено в Supabase: {updated}")


if __name__ == "__main__":
    print("=== Backfill embeddings ===")
    print()

    # SQLite
    db_path = project_root / "data" / "knowledge.db"
    if os.path.exists(db_path):
        backfill_sqlite(str(db_path))
    else:
        print("SQLite не найден, пропускаю")

    print()

    # Supabase
    backfill_supabase()

    print()
    print("=== Done ===")