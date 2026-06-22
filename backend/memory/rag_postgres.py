"""
🧠 RAG — Retrieval-Augmented Generation v3.0 (PostgreSQL версия)

Использует PostgreSQL + pgvector для векторного поиска.
"""

import os
import re
import json
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
import logging
import math

# Создаём логгер в начале
logger = logging.getLogger("PAD+.rag")

# Инициализация PostgreSQL
postgres_available = False
try:
    import psycopg2
    from psycopg2.extras import Json
    postgres_available = True
    logger.info("✅ PostgreSQL доступен")
except Exception as e:
    logger.warning(f"⚠️ PostgreSQL недоступен ({e})")
    psycopg2 = None
    Json = None

# Константы
CONTEXT_WINDOW = 5
MAX_DIALOG_LENGTH = 500
RECENCY_WEIGHT = 0.3
RELEVANCE_WEIGHT = 0.7


# === КЛАССИФИКАЦИЯ ТЕМ ===
TOPIC_KEYWORDS = {
    "техническое": ["код", "программирование", "алгоритм", "функция", "переменная",
                    "python", "javascript", "api", "база данных", "сервер"],
    "философское": ["смысл", "существование", "сознание", "реальность", "истина",
                    "знание", "вера", "этика", "мораль", "добро", "зло"],
    "личное": ["я", "мой", "мне", "меня", "себя", "чувствую", "думаю",
               "хочу", "могу", "умею", "люблю", "ненавижу", "боюсь"],
    "образовательное": ["объясни", "расскажи", "научи", "как работает", "что такое",
                        "пример", "урок", "курс", "изучить", "понять"],
    "творческое": ["придумай", "создай", "напиши", "сочини", "идея", "концепция",
                   "дизайн", "история", "рассказ", "стих", "картина"],
    "аналитическое": ["проанализируй", "сравни", "оцени", "вывод", "причина",
                      "следствие", "закономерность", "статистика", "данные"],
    "бытовое": ["погода", "еда", "сон", "отдых", "покупки", "деньги",
                "время", "расписание", "планы", "семья", "друзья"]
}


def classify_topic(text: str) -> Tuple[str, float]:
    """Классифицирует тему диалога"""
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score / len(keywords)
    
    if not scores:
        return ("общее", 0.5)
    
    best_topic = max(scores, key=scores.get)
    confidence = min(scores[best_topic] * 5, 1.0)
    return (best_topic, round(confidence, 2))


def classify_dialog(user_message: str, ai_response: str) -> Dict[str, Any]:
    """Полная классификация диалога"""
    combined = f"{user_message} {ai_response}"
    primary_topic, confidence = classify_topic(combined)
    
    all_topics = {}
    text_lower = combined.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if text_lower.find(kw) != -1)
        if score > 0:
            all_topics[topic] = round(score / len(keywords) * 5, 2)
    
    positive_words = ["хорошо", "отлично", "прекрасно", "спасибо", "рад", "люблю"]
    negative_words = ["плохо", "ужасно", "грустно", "злюсь", "ненавижу", "проблема"]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "primary_topic": primary_topic,
        "confidence": confidence,
        "all_topics": all_topics,
        "sentiment": sentiment
    }


# === ИЗВЛЕЧЕНИЕ СУЩНОСТЕЙ ===
ENTITY_PATTERNS = {
    "person": [r'\b([А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+)\b', r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'],
    "technology": [r'\b(Python|JavaScript|TypeScript|React|Vue|Angular|Django|FastAPI|TensorFlow|PyTorch)\b'],
    "concept": [r'\b(нейросеть|искусственный интеллект|машинное обучение)\b'],
    "time": [r'\b(\d{1,2}[:.]\d{2})\b', r'\b(сегодня|завтра|вчера|потом|раньше)\b'],
    "number": [r'\b(\d+(?:[.,]\d+)?)\b']
}


def extract_entities(text: str) -> List[Dict[str, Any]]:
    """Извлекает сущности из текста"""
    entities = []
    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.lastindex else match.group(0)
                if not any(e['value'].lower() == value.lower() for e in entities):
                    entities.append({"type": entity_type, "value": value, "confidence": 0.7})
    return entities[:20]


def extract_relations(user_message: str, ai_response: str) -> List[Dict[str, Any]]:
    """Извлекает связи между сущностями"""
    relations = []
    combined = f"{user_message} {ai_response}"
    
    relation_patterns = [
        (r'(\w+)\s+(?:это|является)\s+(\w+)', "is_a"),
        (r'(\w+)\s+(?:использует|применяет)\s+(\w+)', "uses"),
        (r'(\w+)\s+(?:связан|связано)\s+с\s+(\w+)', "related_to"),
    ]
    
    for pattern, relation_type in relation_patterns:
        matches = re.finditer(pattern, combined, re.IGNORECASE)
        for match in matches:
            source, target = match.group(1), match.group(2)
            if len(source) > 2 and len(target) > 2:
                relations.append({"source": source, "relation": relation_type, "target": target, "confidence": 0.6})
    
    return relations[:10]


# === СУМАРИЗАЦИЯ ===
def extract_keywords(text: str) -> List[str]:
    """Извлекает ключевые слова из текста"""
    stop_words = {'и', 'в', 'на', 'не', 'что', 'как', 'это', 'то', 'а', 'но', 'или',
                  'с', 'по', 'за', 'из', 'от', 'до', 'для', 'к', 'у', 'о', 'об',
                  'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они'}
    words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]
    seen = set()
    result = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result[:10]


def summarize_text_simple(text: str, max_length: int = 200) -> str:
    """Простое суммаризирование (обрезание)"""
    if len(text) <= max_length:
        return text
    shortened = text[:max_length]
    last_dot = shortened.rfind('.')
    last_exclaim = shortened.rfind('!')
    last_question = shortened.rfind('?')
    last_sentence = max(last_dot, last_exclaim, last_question)
    if last_sentence > max_length * 0.5:
        return shortened[:last_sentence + 1] + ' [...]'
    last_space = shortened.rfind(' ')
    if last_space > 0:
        return shortened[:last_space] + ' [...]'
    return shortened + ' [...]'


def calculate_keyword_score(query_keywords: List[str], doc_keywords: List[str]) -> float:
    if not query_keywords or not doc_keywords:
        return 0.0
    query_set = set(query_keywords)
    doc_set = set(doc_keywords)
    intersection = len(query_set & doc_set)
    union = len(query_set | doc_set)
    if union == 0:
        return 0.0
    return intersection / union


def calculate_recency_score(timestamp: str, now: datetime = None) -> float:
    if not timestamp:
        return 0.5
    try:
        doc_time = datetime.fromisoformat(timestamp)
        now = now or datetime.now()
        age_days = (now - doc_time).days
        score = math.exp(-age_days / 7.0)
        return max(0.1, min(1.0, score))
    except Exception:
        return 0.5


def summarize_text_sync(text: str, max_length: int = 200) -> str:
    return summarize_text_simple(text, max_length)


class RAGMemory:
    """
    🧠 RAG Memory v3.0 — продвинутая семантическая память (PostgreSQL)
    """
    
    def __init__(self, persist_dir: str = None, use_llm_summarization: bool = False):
        if not postgres_available or psycopg2 is None:
            raise RuntimeError("❌ PostgreSQL не доступен! Установите psycopg2-binary")
        
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("❌ DATABASE_URL не настроен! Добавьте в .env")
        
        logger.info(f"📁 Инициализация RAG Memory v3.0 (PostgreSQL)")
        
        self.use_llm_summarization = use_llm_summarization
        self._keywords_cache: Dict[str, List[str]] = {}
        
        self._init_db()

    def _get_conn(self):
        from core.pg_pool import get_connection
        return get_connection()

    def _put_conn(self, conn):
        from core.pg_pool import put_connection
        if conn is not None:
            put_connection(conn)

    def _init_db(self):
        """Создаёт таблицы RAG, если их нет."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            
            # Проверка расширения vector
            cur.execute("""
                SELECT EXISTS (SELECT FROM pg_extension WHERE extname = 'vector')
            """)
            if not cur.fetchone()[0]:
                raise RuntimeError("❌ pgvector расширение не найдено! Выполните: CREATE EXTENSION vector;")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rag_dialogs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    summary TEXT,
                    keywords TEXT[],
                    topic TEXT DEFAULT 'общее',
                    topic_confidence FLOAT DEFAULT 0.5,
                    sentiment TEXT DEFAULT 'neutral',
                    entities JSONB DEFAULT '[]',
                    relations JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}',
                    user_id UUID,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            conn.commit()
            cur.close()
            logger.info("✅ RAG Memory PostgreSQL инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации PostgreSQL: {e}")
            raise
        finally:
            self._put_conn(conn)
    
    def add_dialog(
        self,
        user_message: str,
        ai_response: str,
        metadata: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Добавляет диалог в память с анализом"""
        doc_id = str(uuid.uuid4())
        
        user_summary = summarize_text_simple(user_message, MAX_DIALOG_LENGTH)
        ai_summary = summarize_text_simple(ai_response, MAX_DIALOG_LENGTH)
        
        combined_text = f"{user_message} {ai_response}"
        keywords = extract_keywords(combined_text)
        topic_info = classify_dialog(user_message, ai_response)
        entities = extract_entities(combined_text)
        relations = extract_relations(user_message, ai_response)
        
        meta = metadata or {}
        meta.update({
            "user_message": user_summary,
            "ai_response": ai_summary,
            "user_full": user_message[:1000],
            "ai_full": ai_response[:1000],
            "timestamp": datetime.now().isoformat(),
            "type": "dialog",
            "is_summarized": len(user_message) > MAX_DIALOG_LENGTH or len(ai_response) > MAX_DIALOG_LENGTH,
            "topic": topic_info["primary_topic"],
            "topic_confidence": topic_info["confidence"],
            "sentiment": topic_info["sentiment"],
            "entities": json.dumps(entities, ensure_ascii=False),
            "relations": json.dumps(relations, ensure_ascii=False),
            "user_id": user_id
        })
        
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO rag_dialogs 
                (id, user_message, ai_response, summary, keywords, topic, topic_confidence, 
                 sentiment, entities, relations, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                doc_id, user_message, ai_response,
                f"{user_summary}\n{ai_summary}",
                keywords, topic_info["primary_topic"], topic_info["confidence"],
                topic_info["sentiment"],
                json.dumps(entities, ensure_ascii=False),
                json.dumps(relations, ensure_ascii=False),
                Json(meta), user_id
            ))
            conn.commit()
            cur.close()
        finally:
            self._put_conn(conn)
        
        logger.info(f"📝 Диалог добавлен: {doc_id[:8]}... (тема: {topic_info['primary_topic']})")
        return doc_id
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = CONTEXT_WINDOW,
        use_keywords: bool = True,
        use_recency: bool = True,
        topic_filter: str = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Гибридный поиск с фильтрацией"""
        
        filter_clause = ""
        params = []
        
        if topic_filter:
            filter_clause += " AND topic = %s"
            params.append(topic_filter)
        
        if user_id:
            filter_clause += " AND (user_id = %s OR user_id IS NULL)"
            params.append(user_id)
        
        query_keywords = extract_keywords(query) if use_keywords else []
        now = datetime.now(timezone.utc)
        
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT id, user_message, ai_response, summary, keywords, topic, 
                       topic_confidence, sentiment, entities, relations, metadata, created_at
                FROM rag_dialogs
                WHERE TRUE {filter_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """, params + [n_results * 3])
            rows = cur.fetchall()
            cur.close()
        finally:
            self._put_conn(conn)
        
        ranked_results = []
        for row in rows:
            doc_id, user_msg, ai_resp, summary, keywords_db, topic, topic_conf, sentiment, entities, relations, meta, created_at = row
            
            # Semantic score (простая эвристика)
            semantic_score = 0.5
            if query and summary:
                query_words = set(extract_keywords(query))
                doc_words = set(extract_keywords(summary))
                if query_words and doc_words:
                    intersection = len(query_words & doc_words)
                    semantic_score = intersection / max(len(query_words | doc_words), 1)
            
            # Keyword score
            keyword_score = 0.0
            if use_keywords and query_keywords and keywords_db:
                doc_kw = set(keywords_db) if keywords_db else set()
                intersection = len(set(query_keywords) & doc_kw)
                keyword_score = intersection / max(len(set(query_keywords) | doc_kw), 1)
            
            # Recency score
            recency_score = 0.5
            if use_recency and created_at:
                age_days = (now - created_at).days
                recency_score = math.exp(-age_days / 7.0)
            
            relevance = semantic_score * 0.7 + keyword_score * 0.3
            combined_score = relevance * RELEVANCE_WEIGHT + recency_score * RECENCY_WEIGHT
            
            meta_dict = meta if meta else {}
            entities_list = entities if isinstance(entities, list) else (json.loads(entities) if entities else [])
            relations_list = relations if isinstance(relations, list) else (json.loads(relations) if relations else [])
            
            ranked_results.append({
                "id": str(doc_id),
                "document": f"Вопрос: {user_msg}\nОтвет: {ai_resp}",
                "metadata": meta_dict,
                "semantic_score": round(semantic_score, 3),
                "keyword_score": round(keyword_score, 3),
                "recency_score": round(recency_score, 3),
                "combined_score": round(combined_score, 3),
                "similarity": round(combined_score, 3),
                "topic": topic or "общее",
                "topic_confidence": topic_conf or 0.5,
                "sentiment": sentiment or "neutral",
                "entities": entities_list,
                "relations": relations_list
            })
        
        ranked_results.sort(key=lambda x: x['combined_score'], reverse=True)
        return ranked_results[:n_results]
    
    def search(self, query: str, n_results: int = CONTEXT_WINDOW) -> List[Dict[str, Any]]:
        """Базовый поиск"""
        return self.hybrid_search(query, n_results)
    
    def get_context(self, query: str, user_id: Optional[str] = None) -> str:
        """Формирует контекст для RAG"""
        dialogs = self.hybrid_search(query, n_results=CONTEXT_WINDOW, user_id=user_id)
        
        if not dialogs:
            return ""
        
        relevant = [d for d in dialogs if d['combined_score'] > 0.25]
        if not relevant:
            return ""
        
        context_parts = ["📚 Релевантный контекст из памяти:\n"]
        for i, dialog in enumerate(relevant[:3], 1):
            meta = dialog['metadata']
            user_msg = meta.get('user_message', '')
            ai_resp = meta.get('ai_response', '')
            topic = dialog.get('topic', 'общее')
            owner = " (ваши данные)" if meta.get('user_id') == user_id else ""
            
            context_parts.append(
                f"[{i}]{owner} (тема: {topic}, score: {dialog['combined_score']:.2f})\n"
                f"Вопрос: {user_msg}\nОтвет: {ai_resp}\n"
            )
        
        context_parts.append("\nИспользуй этот контекст для ответа.\n")
        return "\n".join(context_parts)
    
    def search_by_topic(self, topic: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.hybrid_search("", n_results=n_results, topic_filter=topic)

    def search_by_keywords(self, keywords: List[str], n_results: int = CONTEXT_WINDOW) -> List[Dict[str, Any]]:
        if not keywords:
            return []
        query = " ".join(keywords)
        return self.hybrid_search(query, n_results, use_keywords=True, use_recency=False)

    def get_recent(self, days: int = 7, n_results: int = 10) -> List[Dict[str, Any]]:
        try:
            cutoff = datetime.now() - timedelta(days=days)
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, user_message, ai_response, metadata, created_at FROM rag_dialogs WHERE created_at >= %s ORDER BY created_at DESC LIMIT %s",
                    (cutoff, n_results),
                )
                rows = cur.fetchall()
                cur.close()
            finally:
                self._put_conn(conn)
            recent = []
            now = datetime.now()
            for row in rows:
                doc_id = row[0]
                user_message = row[1]
                ai_response = row[2]
                meta = row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {}
                created_at = row[4].isoformat() if row[4] else datetime.now().isoformat()
                try:
                    doc_time = datetime.fromisoformat(created_at)
                    age_hours = (now - doc_time).total_seconds() / 3600
                    recent.append({
                        "id": doc_id,
                        "document": f"Вопрос: {user_message}\nОтвет: {ai_response}",
                        "metadata": meta,
                        "timestamp": created_at,
                        "topic": meta.get('topic', 'общее'),
                        "age_hours": round(age_hours, 1),
                    })
                except Exception:
                    continue
            return recent
        except Exception as e:
            logger.error(f"Ошибка получения недавних диалогов: {e}")
            return []

    def get_topic_stats(self) -> Dict[str, int]:
        try:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT topic, COUNT(*) FROM rag_dialogs GROUP BY topic ORDER BY count DESC")
                result = {row[0]: row[1] for row in cur.fetchall()}
                cur.close()
            finally:
                self._put_conn(conn)
            return result
        except Exception as e:
            logger.error(f"Ошибка статистики по темам: {e}")
            return {}

    def get_entity_index(self) -> Dict[str, List[str]]:
        try:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, entities FROM rag_dialogs WHERE entities IS NOT NULL AND entities != '[]'::jsonb")
                rows = cur.fetchall()
                cur.close()
            finally:
                self._put_conn(conn)
            entity_index = {}
            for row in rows:
                doc_id = row[0]
                entities_json = row[1]
                try:
                    entities = json.loads(entities_json) if isinstance(entities_json, str) else entities_json
                    for entity in entities:
                        value = entity.get('value', '')
                        if value:
                            entity_index.setdefault(value, []).append(doc_id)
                except Exception:
                    continue
            return entity_index
        except Exception as e:
            logger.error(f"Ошибка индекса сущностей: {e}")
            return {}

    def clear(self):
        try:
            conn = self._get_conn()
            try:
                cur = conn.cursor()
                cur.execute("TRUNCATE TABLE rag_dialogs RESTART IDENTITY")
                conn.commit()
                cur.close()
            finally:
                self._put_conn(conn)
            self._keywords_cache.clear()
            logger.info("RAG Memory очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки RAG: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Расширенная статистика RAG"""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM rag_dialogs")
            total = cur.fetchone()[0]
            
            cur.execute("""
                SELECT topic, COUNT(*) FROM rag_dialogs GROUP BY topic
            """)
            topic_counts = {row[0]: row[1] for row in cur.fetchall()}
            
            cur.execute("""
                SELECT sentiment, COUNT(*) FROM rag_dialogs GROUP BY sentiment
            """)
            sentiment_counts = {row[0]: row[1] for row in cur.fetchall()}
            
            cur.close()
        finally:
            self._put_conn(conn)
        
        return {
            "total_dialogs": total,
            "topic_distribution": topic_counts,
            "sentiment_distribution": sentiment_counts,
            "backend": "postgresql_pgvector",
            "version": "3.0"
        }
    
    def close(self):
        """Пул управляет соединениями — ничего не делаем."""
    
    def __del__(self):
        try:
            self.close()
        except Exception as e:
            logger.warning(f"{__name__} error: {e}")


# Глобальный экземпляр
_rag_memory: Optional[RAGMemory] = None


def get_rag() -> RAGMemory:
    """Возвращает глобальную RAG память"""
    global _rag_memory
    if _rag_memory is None:
        _rag_memory = RAGMemory()
    return _rag_memory
