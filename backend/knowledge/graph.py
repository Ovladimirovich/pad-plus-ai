"""
Граф знаний PAD+ AI

NetworkX-based граф для хранения связей между концепциями.
Поддерживает два хранилища:
  - Supabase (PostgreSQL) — продакшн, данные сохраняются на Render
  - SQLite — локальная разработка, fallback

Авто-определение: если есть SUPABASE_URL + SUPABASE_KEY → Supabase, иначе SQLite.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
import json
import os
import sqlite3
import logging

logger = logging.getLogger("padplus.knowledge.graph")

# NetworkX для графа
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

# Supabase клиент (опционально)
_supabase_client = None
SUPABASE_AVAILABLE = False


def _init_supabase():
    global _supabase_client, SUPABASE_AVAILABLE
    if SUPABASE_AVAILABLE or _supabase_client is not None:
        return

    # На Render автоматически устанавливается RENDER=true.
    # Локально всегда используем SQLite, даже если Supabase credentials есть в .env.
    if not os.getenv("RENDER"):
        logger.info("Knowledge Graph: локальный режим (RENDER не задан), использую SQLite")
        return

    try:
        from core.supabase_client import get_supabase_service, get_supabase
        client = get_supabase_service() or get_supabase()
        if client is not None:
            _supabase_client = client
            SUPABASE_AVAILABLE = True
            logger.info("Knowledge Graph: Supabase подключён")
            _ensure_supabase_tables()
        else:
            logger.info("Knowledge Graph: Supabase недоступен, использую SQLite")
    except Exception as e:
        logger.warning(f"Knowledge Graph: ошибка подключения Supabase: {e}")


def _ensure_supabase_tables():
    """Создаёт таблицы и колонку embedding в Supabase (если есть прямой SQL доступ)."""
    import os
    database_url = os.getenv("DATABASE_URL")

    # Прямое подключение через psycopg2 (если есть DATABASE_URL)
    if database_url:
        try:
            import psycopg2
            conn = psycopg2.connect(database_url, connect_timeout=5)
            cur = conn.cursor()
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_concepts (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    type TEXT DEFAULT 'concept', confidence REAL DEFAULT 0.5,
                    source TEXT DEFAULT 'user', created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}',
                    embedding VECTOR(384)
                )
            """)
            cur.execute("ALTER TABLE knowledge_concepts ADD COLUMN IF NOT EXISTS embedding VECTOR(384)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_concepts_name ON knowledge_concepts USING gin (to_tsvector('simple', name))")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_concepts_embedding ON knowledge_concepts USING hnsw (embedding vector_cosine_ops)")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relations (
                    id BIGSERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
                    target_id TEXT NOT NULL REFERENCES knowledge_concepts(id) ON DELETE CASCADE,
                    type TEXT DEFAULT 'related', weight REAL DEFAULT 1.0,
                    confidence REAL DEFAULT 0.5, created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source ON knowledge_relations(source_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target ON knowledge_relations(target_id)")
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Knowledge Graph: таблицы созданы/проверены (psycopg2)")
            return
        except ImportError:
            logger.warning("Knowledge Graph: psycopg2 не установлен — пропускаю миграцию")
        except Exception as e:
            logger.warning(f"Knowledge Graph: psycopg2 ошибка: {e}")

    # На Render без DATABASE_URL — таблицы должны быть созданы заранее
    if os.getenv("RENDER"):
        logger.info("Knowledge Graph: SQL миграция недоступна на Render без DATABASE_URL")
        logger.info("Knowledge Graph: таблицы должны существовать заранее (созданы в Supabase Dashboard)")


@dataclass
class Concept:
    """Концепция в графе знаний"""
    id: str
    name: str
    concept_type: str = "concept"
    confidence: float = 0.5
    source: str = "user"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.concept_type,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Relation:
    """Связь между концепциями"""
    source_id: str
    target_id: str
    relation_type: str = "related"
    weight: float = 1.0
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type,
            "weight": self.weight,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeGraph:
    """
    Граф знаний с поддержкой Supabase (продакшн) и SQLite (локально).

    При инициализации проверяет доступность Supabase.
    Если Supabase доступен — все операции идут через него, SQLite игнорируется.
    Если нет — используется SQLite как раньше.
    """

    def __init__(self, db_path: str = None):
        _init_supabase()
        self._use_supabase = SUPABASE_AVAILABLE

        # Всегда инициализируем db_path и создаем таблицы для синхронизации
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "knowledge.db"
            )
        self.db_path = db_path
        self._ensure_tables()

        if NETWORKX_AVAILABLE:
            self.graph = nx.DiGraph()
        else:
            self.graph = None

        self._concepts: Dict[str, Concept] = {}
        self._relations: List[Relation] = []
        self._load_from_db()

        # Авто-синхронизация с Supabase при старте (только если Supabase доступен)
        if self._use_supabase:
            self.sync_with_supabase()

    def _supabase_table(self, table: str):
        return _supabase_client.table(table)

    # ─── ЗАГРУЗКА ──────────────────────────────────────────────

    def _load_from_db(self):
        if self._use_supabase:
            self._load_from_supabase()
        else:
            self._load_from_sqlite()

    def sync_with_supabase(self) -> dict:
        """Двусторонняя синхронизация: пуллить Supabase → SQLite, пушить SQLite → Supabase.
        Конфликты решаются по updated_at (побеждает свежее)."""
        if not self._use_supabase:
            return {"status": "skipped", "reason": "Supabase не используется"}

        stats = {"concepts_pulled": 0, "concepts_pushed": 0, 
                 "relations_pulled": 0, "relations_pushed": 0,
                 "conflicts_resolved": 0}

        try:
            # 1. Пуллим из Supabase (новые/обновлённые)
            from datetime import datetime, timezone
            
            # Получаем max updated_at из локальной БД для концепций
            local_max_updated = None
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT MAX(updated_at) FROM concepts WHERE updated_at IS NOT NULL AND updated_at != ''")
                row = cur.fetchone()
                local_max_updated = row[0] if row and row[0] else None
                conn.close()

            # Пуллим концепции из Supabase
            query = self._supabase_table("knowledge_concepts").select("*")
            if local_max_updated:
                query = query.gt("updated_at", local_max_updated)
            resp = query.execute()
            for row in (resp.data or []):
                concept = Concept(
                    id=row["id"],
                    name=row["name"],
                    concept_type=row.get("type", "concept"),
                    confidence=row.get("confidence", 0.5),
                    source=row.get("source", "user"),
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(),
                    metadata=row.get("metadata", {}) or {},
                )
                # Проверяем конфликт: есть ли локально?
                existing = self._concepts.get(concept.id)
                if existing:
                    remote_updated = row.get("updated_at", "")
                    local_updated = existing.metadata.get("updated_at", "") if isinstance(existing.metadata, dict) else ""
                    if remote_updated and local_updated and remote_updated > local_updated:
                        # Удалённая свежее — обновляем
                        self._concepts[concept.id] = concept
                        if self.graph is not None:
                            self.graph.add_node(concept.id, **concept.to_dict())
                        self._save_concept_sqlite(concept, row.get("updated_at", datetime.now().isoformat()))
                        stats["conflicts_resolved"] += 1
                else:
                    self._concepts[concept.id] = concept
                    if self.graph is not None:
                        self.graph.add_node(concept.id, **concept.to_dict())
                    self._save_concept_sqlite(concept, row.get("updated_at", datetime.now().isoformat()))
                    stats["concepts_pulled"] += 1

            # Пуллим связи из Supabase
            local_max_rel_updated = None
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT MAX(updated_at) FROM relations WHERE updated_at IS NOT NULL AND updated_at != ''")
                row = cur.fetchone()
                local_max_rel_updated = row[0] if row and row[0] else None
                conn.close()

            rel_query = self._supabase_table("knowledge_relations").select("*")
            if local_max_rel_updated:
                rel_query = rel_query.gt("updated_at", local_max_rel_updated)
            resp2 = rel_query.execute()
            for row in (resp2.data or []):
                rel = Relation(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relation_type=row.get("type", "related"),
                    weight=row.get("weight", 1.0),
                    confidence=row.get("confidence", 0.5),
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(),
                )
                # Проверяем, есть ли уже такая связь
                exists = any(r.source_id == rel.source_id and r.target_id == rel.target_id for r in self._relations)
                if not exists:
                    self._relations.append(rel)
                    if self.graph is not None:
                        self.graph.add_edge(rel.source_id, rel.target_id,
                                            type=rel.relation_type, weight=rel.weight, confidence=rel.confidence)
                    self._save_relation_sqlite(rel, row.get("updated_at", datetime.now().isoformat()))
                    stats["relations_pulled"] += 1

            # 2. Пушим локальные изменения в Supabase (если есть новые, которых нет в Supabase)
            # Концепции
            supabase_concept_ids = set()
            resp = self._supabase_table("knowledge_concepts").select("id").execute()
            for row in (resp.data or []):
                supabase_concept_ids.add(row["id"])

            for concept in self._concepts.values():
                if concept.id not in supabase_concept_ids:
                    try:
                        self._supabase_table("knowledge_concepts").insert({
                            "id": concept.id, "name": concept.name,
                            "type": concept.concept_type, "confidence": concept.confidence,
                            "source": concept.source,
                            "created_at": concept.created_at.isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "metadata": concept.metadata,
                        }).execute()
                        stats["concepts_pushed"] += 1
                    except Exception as e:
                        logger.warning(f"Supabase push concept error: {e}")

            # Связи
            supabase_rel_ids = set()
            resp = self._supabase_table("knowledge_relations").select("source_id,target_id").execute()
            for row in (resp.data or []):
                supabase_rel_ids.add((row["source_id"], row["target_id"]))

            for rel in self._relations:
                if (rel.source_id, rel.target_id) not in supabase_rel_ids:
                    try:
                        self._supabase_table("knowledge_relations").insert({
                            "source_id": rel.source_id,
                            "target_id": rel.target_id,
                            "type": rel.relation_type,
                            "weight": rel.weight,
                            "confidence": rel.confidence,
                            "created_at": rel.created_at.isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }).execute()
                        stats["relations_pushed"] += 1
                    except Exception as e:
                        logger.warning(f"Supabase push relation error: {e}")

            logger.info(f"Sync done: {stats}")
            return {"status": "ok", **stats}

        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {"status": "error", "error": str(e), **stats}

    def _load_from_supabase(self):
        try:
            resp = self._supabase_table("knowledge_concepts").select("*").execute()
            for row in (resp.data or []):
                metadata = row.get("metadata", {}) or {}
                if row.get("embedding"):
                    metadata["embedding"] = row["embedding"]
                concept = Concept(
                    id=row["id"],
                    name=row["name"],
                    concept_type=row.get("type", "concept"),
                    confidence=row.get("confidence", 0.5),
                    source=row.get("source", "user"),
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(),
                    metadata=metadata,
                )
                self._concepts[concept.id] = concept
                if self.graph is not None:
                    self.graph.add_node(concept.id, **concept.to_dict())

            resp2 = self._supabase_table("knowledge_relations").select("*").execute()
            for row in (resp2.data or []):
                rel = Relation(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relation_type=row.get("type", "related"),
                    weight=row.get("weight", 1.0),
                    confidence=row.get("confidence", 0.5),
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(),
                )
                self._relations.append(rel)
                if self.graph is not None:
                    self.graph.add_edge(rel.source_id, rel.target_id,
                                        type=rel.relation_type, weight=rel.weight, confidence=rel.confidence)

            logger.info(f"Загружено из Supabase: {len(self._concepts)} концепций, {len(self._relations)} связей")
        except Exception as e:
            logger.error(f"Ошибка загрузки из Supabase: {e}")

    def _load_from_sqlite(self):
        if not os.path.exists(self.db_path):
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM concepts")
        for row in cursor.fetchall():
            metadata = json.loads(row["metadata"])
            # Загружаем embedding из BLOB
            if row["embedding"]:
                import struct
                emb_bytes = row["embedding"]
                dim = len(emb_bytes) // 4
                metadata["embedding"] = list(struct.unpack(f"{dim}f", emb_bytes))
            concept = Concept(
                id=row["id"], name=row["name"], concept_type=row["type"],
                confidence=row["confidence"], source=row["source"],
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=metadata,
            )
            self._concepts[concept.id] = concept
            if self.graph is not None:
                self.graph.add_node(concept.id, **concept.to_dict())

        cursor.execute("SELECT * FROM relations")
        for row in cursor.fetchall():
            rel = Relation(
                source_id=row["source_id"], target_id=row["target_id"],
                relation_type=row["type"], weight=row["weight"],
                confidence=row["confidence"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            self._relations.append(rel)
            if self.graph is not None:
                self.graph.add_edge(rel.source_id, rel.target_id,
                                    type=rel.relation_type, weight=rel.weight, confidence=rel.confidence)

        conn.close()

    # ─── ТАБЛИЦЫ ───────────────────────────────────────────────

    def _ensure_tables(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not self.db_path.startswith(":memory:") and not self.db_path.startswith("file:"):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                type TEXT DEFAULT 'concept', confidence REAL DEFAULT 0.5,
                source TEXT DEFAULT 'user', created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                embedding BLOB DEFAULT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL, target_id TEXT NOT NULL,
                type TEXT DEFAULT 'related', weight REAL DEFAULT 1.0,
                confidence REAL DEFAULT 0.5, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES concepts(id),
                FOREIGN KEY (target_id) REFERENCES concepts(id)
            )
        """)
        # Миграция: добавить updated_at если его нет
        cursor.execute("PRAGMA table_info(concepts)")
        cols = [r[1] for r in cursor.fetchall()]
        if "updated_at" not in cols:
            cursor.execute("ALTER TABLE concepts ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        if "embedding" not in cols:
            cursor.execute("ALTER TABLE concepts ADD COLUMN embedding BLOB DEFAULT NULL")
        cursor.execute("PRAGMA table_info(relations)")
        cols = [r[1] for r in cursor.fetchall()]
        if "updated_at" not in cols:
            cursor.execute("ALTER TABLE relations ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)")
        conn.commit()
        conn.close()

    # ─── ДОБАВЛЕНИЕ ────────────────────────────────────────────

    def add_concept(self, name: str, concept_type: str = "concept",
                        confidence: float = 0.5, source: str = "user",
                        metadata: dict = None) -> "Concept":
            import uuid
            concept_id = str(uuid.uuid4())[:8]
            now = datetime.now().isoformat()
            concept = Concept(
                id=concept_id, name=name, concept_type=concept_type,
                confidence=confidence, source=source,
                created_at=datetime.fromisoformat(now),
                metadata=metadata or {},
            )

            # Генерируем embedding для семантического поиска
            embedding = self._generate_embedding(name)
            if embedding is not None:
                concept.metadata["embedding"] = embedding

            if self._use_supabase:
                # Пробуем вставить с максимальным набором полей,
                # при PGRST204 последовательно убираем "лишние" колонки
                data_variants = [
                    # 0: все поля (если таблица полная) — с embedding
                    {
                        "id": concept.id, "name": concept.name,
                        "type": concept.concept_type, "confidence": concept.confidence,
                        "source": concept.source,
                        "created_at": concept.created_at.isoformat(),
                        "updated_at": now,
                        "metadata": concept.metadata,
                        "embedding": embedding,
                    },
                    # 1: без embedding
                    {
                        "id": concept.id, "name": concept.name,
                        "type": concept.concept_type, "confidence": concept.confidence,
                        "source": concept.source,
                        "created_at": concept.created_at.isoformat(),
                        "updated_at": now,
                        "metadata": concept.metadata,
                    },
                    # 2: без updated_at
                    {
                        "id": concept.id, "name": concept.name,
                        "type": concept.concept_type, "confidence": concept.confidence,
                        "source": concept.source,
                        "created_at": concept.created_at.isoformat(),
                        "metadata": concept.metadata,
                    },
                    # 3: без updated_at, metadata
                    {
                        "id": concept.id, "name": concept.name,
                        "type": concept.concept_type, "confidence": concept.confidence,
                        "source": concept.source,
                        "created_at": concept.created_at.isoformat(),
                    },
                    # 4: минимальное
                    {
                        "id": concept.id, "name": concept.name,
                        "type": concept.concept_type,
                    },
                    # 5: только id + name
                    {
                        "id": concept.id, "name": concept.name,
                    },
                ]

                inserted = False
                for data in data_variants:
                    try:
                        self._supabase_table("knowledge_concepts").insert(data).execute()
                        inserted = True
                        logger.debug(f"Supabase insert success with {len(data)} fields")
                        break
                    except Exception as e:
                        if "PGRST204" not in str(e):
                            # Не PGRST204 — пробуем следующий вариант
                            continue
                if not inserted:
                    logger.error(f"Supabase insert concept failed after all fallbacks")

            self._save_concept_sqlite(concept, now)
            self._concepts[concept.id] = concept
            if self.graph is not None:
                self.graph.add_node(concept.id, **concept.to_dict())
            return concept

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Генерирует embedding через OpenRouter (text-embedding-3-small, 384 dim)."""
        try:
            from core.config_manager import get_openrouter_key
            import httpx
            api_key = get_openrouter_key()
            if not api_key:
                return None
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
            logger.debug(f"Embedding generation failed: {e}")
            return None

    def _save_concept_sqlite(self, concept: Concept, updated_at: str = None):
        if self._use_supabase:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = updated_at or datetime.now().isoformat()
            # Сериализуем embedding в байты для BLOB
            embedding_bytes = None
            if isinstance(concept.metadata, dict):
                emb = concept.metadata.get("embedding")
                if isinstance(emb, list):
                    import struct
                    embedding_bytes = struct.pack(f"{len(emb)}f", *emb)
            cursor.execute("""
                INSERT INTO concepts (id, name, type, confidence, source, created_at, updated_at, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (concept.id, concept.name, concept.concept_type,
                  concept.confidence, concept.source,
                  concept.created_at.isoformat(),
                  now,
                  json.dumps(concept.metadata, ensure_ascii=False),
                  embedding_bytes))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite insert concept error: {e}")

    def add_relation(self, source_id: str, target_id: str,
                     relation_type: str = "related",
                     weight: float = 1.0,
                     confidence: float = 0.5) -> Optional["Relation"]:
        if source_id not in self._concepts or target_id not in self._concepts:
            return None

        now = datetime.now().isoformat()
        relation = Relation(
            source_id=source_id, target_id=target_id,
            relation_type=relation_type, weight=weight,
            confidence=confidence,
            created_at=datetime.fromisoformat(now),
        )

        if self._use_supabase:
            try:
                self._supabase_table("knowledge_relations").insert({
                    "source_id": relation.source_id,
                    "target_id": relation.target_id,
                    "type": relation.relation_type,
                    "weight": relation.weight,
                    "confidence": relation.confidence,
                    "created_at": relation.created_at.isoformat(),
                    "updated_at": now,
                }).execute()
            except Exception as e:
                logger.error(f"Supabase insert relation error: {e}")

        self._save_relation_sqlite(relation, now)
        self._relations.append(relation)
        if self.graph is not None:
            self.graph.add_edge(source_id, target_id,
                                type=relation_type, weight=weight, confidence=confidence)
        return relation

    def _save_relation_sqlite(self, relation: Relation, now: str = None):
        if self._use_supabase:
            return
        if now is None:
            now = datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO relations (source_id, target_id, type, weight, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (relation.source_id, relation.target_id,
                  relation.relation_type, relation.weight,
                  relation.confidence, relation.created_at.isoformat(), now))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite insert relation error: {e}")

    # ─── ЧТЕНИЕ ────────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        return self._concepts.get(concept_id)

    def find_concepts(self, query: str, limit: int = 10) -> List[Concept]:
        query_lower = query.lower()
        results = []
        for concept in self._concepts.values():
            if query_lower in concept.name.lower():
                results.append(concept)
                if len(results) >= limit:
                    break
        return results[:limit]

    def get_related(self, concept_id: str, depth: int = 1) -> List[Concept]:
        if not self.graph or concept_id not in self._concepts:
            return []
        seen = set()
        related = []
        if self.graph.has_node(concept_id):
            for neighbor in self.graph.neighbors(concept_id):
                if neighbor in self._concepts and neighbor not in seen:
                    seen.add(neighbor)
                    related.append(self._concepts[neighbor])
            for predecessor in self.graph.predecessors(concept_id):
                if predecessor in self._concepts and predecessor not in seen:
                    seen.add(predecessor)
                    related.append(self._concepts[predecessor])
        return related

    def find_path(self, source_id: str, target_id: str) -> List[str]:
        if not self.graph:
            return []
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_stats(self) -> dict:
        avg_confidence = 0.0
        if self._concepts:
            avg_confidence = sum(c.confidence for c in self._concepts.values()) / len(self._concepts)
        if self.graph is not None:
            return {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
                "avg_confidence": round(avg_confidence, 3),
                "networkx_available": True,
            }
        return {
            "nodes": len(self._concepts),
            "edges": 0,
            "density": 0,
            "avg_confidence": round(avg_confidence, 3),
            "networkx_available": False,
        }

    def semantic_search(self, query: str, limit: int = 10, similarity_threshold: float = 0.3) -> List[dict]:
        """Семантический поиск концепций по эмбеддингам (vector similarity).
        Работает через Supabase (pgvector) или локально через cosine similarity."""
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return []

        results = []

        if self._use_supabase:
            try:
                # Cosine similarity через pgvector
                resp = self._supabase_table("knowledge_concepts").select("*").execute()
                for row in (resp.data or []):
                    emb = row.get("embedding")
                    if emb:
                        sim = self._cosine_similarity(query_embedding, emb)
                        if sim >= similarity_threshold:
                            results.append({
                                "id": row["id"],
                                "name": row["name"],
                                "type": row.get("type", "concept"),
                                "confidence": row.get("confidence", 0.5),
                                "similarity": round(sim, 3),
                            })
            except Exception as e:
                logger.debug(f"Supabase semantic search failed: {e}")
        else:
            # Локальный поиск через SQLite + cosine similarity
            import struct
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, type, confidence, embedding FROM concepts WHERE embedding IS NOT NULL")
            for row in cursor.fetchall():
                emb_bytes = row["embedding"]
                if emb_bytes:
                    dim = len(emb_bytes) // 4
                    emb = list(struct.unpack(f"{dim}f", emb_bytes))
                    sim = self._cosine_similarity(query_embedding, emb)
                    if sim >= similarity_threshold:
                        results.append({
                            "id": row["id"],
                            "name": row["name"],
                            "type": row["type"],
                            "confidence": row["confidence"],
                            "similarity": round(sim, 3),
                        })
            conn.close()

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Cosine similarity между двумя векторами."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def to_dict(self) -> dict:
        nodes = [c.to_dict() for c in self._concepts.values()]
        links = [r.to_dict() for r in self._relations]
        return {"nodes": nodes, "links": links, "stats": self.get_stats()}


# Глобальный экземпляр
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph
