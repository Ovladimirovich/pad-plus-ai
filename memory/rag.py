"""
RAG Memory с поддержкой PostgreSQL + pgvector

Использует только PostgreSQL для векторного поиска.
ChromaDB удалён для экономии памяти на Render.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RAGMemory:
    """Реализация RAG памяти с PostgreSQL + pgvector"""
    
    def __init__(self):
        logger.info("🔄 RAG: Используем PostgreSQL + pgvector")
        self._init_postgres()
    
    def _init_postgres(self):
        """Инициализация PostgreSQL + pgvector"""
        try:
            import psycopg2
            from psycopg2.extras import Json
            
            self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            self.cursor = self.conn.cursor()
            
            # Проверка наличия расширения vector
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = 'vector'
                )
            """)
            
            if not self.cursor.fetchone()[0]:
                raise RuntimeError("❌ pgvector расширение не найдено в PostgreSQL! Выполните: CREATE EXTENSION IF NOT EXISTS vector;")
            
            logger.info("✅ PostgreSQL + pgvector инициализирован")
            
        except ImportError:
            logger.error("❌ psycopg2 не установлен! Добавьте в requirements.txt: psycopg2-binary>=2.9.0")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации PostgreSQL: {e}")
            raise
    
    def add_embedding(self, text: str, embedding: List[float], 
                     user_id: Optional[str] = None,
                     collection_name: str = "default",
                     metadata: Optional[Dict] = None) -> str:
        """Добавить embedding в память"""
        return self._postgres_add(text, embedding, user_id, collection_name, metadata)
        
    def _postgres_add(self, text: str, embedding: List[float],
                     user_id: Optional[str],
                     collection_name: str,
                     metadata: Optional[Dict]) -> str:
        """Добавление через Supabase"""
        try:
            from psycopg2.extras import execute_values
            
            query = """
                INSERT INTO rag_embeddings (text, embedding, user_id, collection_name, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            
            self.cursor.execute(query, (
                text,
                json.dumps(embedding),
                user_id,
                collection_name,
                Json(metadata) if metadata else None
            ))
            
            self.conn.commit()
            result = self.cursor.fetchone()
            embed_id = str(result[0]) if result else None
            
            logger.debug(f"✅ Добавлен embedding в PostgreSQL: {embed_id}")
            return embed_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в PostgreSQL: {e}")
            raise
    
    def search(self, query_embedding: List[float], 
              user_id: Optional[str] = None,
              collection_name: str = "default",
              top_k: int = 5) -> List[Dict]:
        """Поиск по embedding"""
        return self._postgres_search(query_embedding, user_id, collection_name, top_k)
        
    def _postgres_search(self, query_embedding: List[float],
                        user_id: Optional[str],
                        collection_name: str,
                        top_k: int) -> List[Dict]:
        """Поиск через Supabase с pgvector"""
        try:
            # Построение запроса с фильтрацией по user_id
            filter_clause = ""
            params = [json.dumps(query_embedding), top_k]
            
            if user_id:
                filter_clause = "WHERE user_id = %s AND collection_name = %s"
                params.extend([user_id, collection_name])
            
            query = f"""
                SELECT id, text, embedding, user_id, collection_name, metadata, created_at,
                       (embedding <=> %s) AS distance
                FROM rag_embeddings
                {filter_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
            """
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": str(row[0]),
                    "text": row[1],
                    "embedding": row[2],
                    "user_id": str(row[3]) if row[3] else None,
                    "collection_name": row[4],
                    "metadata": row[5] if row[5] else {},
                    "created_at": str(row[6]) if row[6] else None,
                    "distance": float(row[7])
                })
            
            logger.debug(f"✅ Найдено {len(results)} результатов в PostgreSQL")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска в PostgreSQL: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Получить статистику памяти"""
        return self._postgres_stats()
    
    def _postgres_stats(self) -> Dict:
        """Статистика PostgreSQL"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM rag_embeddings")
            total = self.cursor.fetchone()[0]
            
            self.cursor.execute("""
                SELECT COUNT(DISTINCT user_id) FROM rag_embeddings WHERE user_id IS NOT NULL
            """)
            users = self.cursor.fetchone()[0]
            
            return {
                "total_embeddings": total,
                "unique_users": users,
                "backend": "postgresql_pgvector"
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики PostgreSQL: {e}")
            return {"error": str(e), "backend": "postgresql_pgvector"}
    
    def close(self):
        """Закрытие соединения"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("✅ PostgreSQL соединение закрыто")
    
    def __del__(self):
        """Очистка при удалении"""
        try:
            self.close()
        except:
            pass


# Singleton instance
_rag_instance = None


def get_rag() -> RAGMemory:
    """Получить экземпляр RAG памяти"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGMemory()
    return _rag_instance


def reset_rag():
    """Сброс экземпляра (для тестирования)"""
    global _rag_instance
    if _rag_instance:
        _rag_instance.close()
    _rag_instance = None