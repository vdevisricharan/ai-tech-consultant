import sqlite3
import struct
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    from ingestion.models import ArticleChunk
except ImportError:
    from ..ingestion.models import ArticleChunk

logger = logging.getLogger("store")

class HybridKnowledgeStore:
    def __init__(self, db_path: str = "data/knowledge_brain.db", embedding_dim: int = 128):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = embedding_dim
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Structured table for chunks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    article_url TEXT,
                    article_title TEXT,
                    category TEXT,
                    folder TEXT,
                    heading TEXT,
                    content TEXT,
                    image_refs TEXT,
                    embedding_blob BLOB
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_url ON chunks(article_url)")

            # Full-text search FTS5 table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    article_url UNINDEXED,
                    article_title,
                    heading,
                    content
                )
            """)

            # Escalations table for unanswered questions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    context TEXT,
                    reason TEXT,
                    status TEXT DEFAULT 'PENDING',
                    expert_answer TEXT,
                    created_at TEXT,
                    resolved_at TEXT
                )
            """)
            conn.commit()

    def _generate_fallback_embedding(self, text: str) -> np.ndarray:
        """Deterministic hashing embedding vector for offline testing."""
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec
        for w in words:
            idx = abs(hash(w)) % self.embedding_dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def insert_chunk(self, chunk: ArticleChunk):
        vec = chunk.embedding if chunk.embedding is not None else self._generate_fallback_embedding(chunk.content)
        vec_np = np.array(vec, dtype=np.float32)
        blob = vec_np.tobytes()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO chunks (
                    chunk_id, article_url, article_title, category, folder,
                    heading, content, image_refs, embedding_blob
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.chunk_id,
                chunk.article_url,
                chunk.article_title,
                chunk.category,
                chunk.folder,
                chunk.heading,
                chunk.content,
                json.dumps(chunk.image_refs),
                blob
            ))

            # Update FTS5
            cursor.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (chunk.chunk_id,))
            cursor.execute("""
                INSERT INTO chunks_fts (chunk_id, article_url, article_title, heading, content)
                VALUES (?, ?, ?, ?, ?)
            """, (chunk.chunk_id, chunk.article_url, chunk.article_title, chunk.heading, chunk.content))
            conn.commit()

    def delete_article_chunks(self, article_url: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE article_url = ?", (article_url,))
            cursor.execute("DELETE FROM chunks_fts WHERE article_url = ?", (article_url,))
            conn.commit()

    def search_keyword(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Performs BM25 search using SQLite FTS5."""
        clean_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query)
        terms = [t for t in clean_query.split() if len(t) > 2]
        if not terms:
            return []
        
        fts_query = " OR ".join(f'"{t}"' for t in terms)
        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT c.chunk_id, c.article_url, c.article_title, c.category, c.folder,
                           c.heading, c.content, c.image_refs, bm25(chunks_fts) as score
                    FROM chunks_fts
                    JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
                    WHERE chunks_fts MATCH ?
                    ORDER BY score ASC
                    LIMIT ?
                """, (fts_query, limit))
                for row in cursor.fetchall():
                    results.append({
                        "chunk_id": row["chunk_id"],
                        "article_url": row["article_url"],
                        "article_title": row["article_title"],
                        "category": row["category"],
                        "folder": row["folder"],
                        "heading": row["heading"],
                        "content": row["content"],
                        "image_refs": json.loads(row["image_refs"] or "[]"),
                        "fts_score": float(row["score"])
                    })
            except Exception as e:
                logger.warning(f"FTS search error for query '{query}': {e}")
        return results

    def search_vector(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Performs cosine vector search across all indexed chunks."""
        query_vec = self._generate_fallback_embedding(query)
        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id, article_url, article_title, category, folder,
                       heading, content, image_refs, embedding_blob
                FROM chunks
            """)
            rows = cursor.fetchall()
            for row in rows:
                blob = row["embedding_blob"]
                if blob:
                    chunk_vec = np.frombuffer(blob, dtype=np.float32)
                    sim = float(np.dot(query_vec, chunk_vec))
                    results.append({
                        "chunk_id": row["chunk_id"],
                        "article_url": row["article_url"],
                        "article_title": row["article_title"],
                        "category": row["category"],
                        "folder": row["folder"],
                        "heading": row["heading"],
                        "content": row["content"],
                        "image_refs": json.loads(row["image_refs"] or "[]"),
                        "vector_sim": sim
                    })
        results.sort(key=lambda x: x["vector_sim"], reverse=True)
        return results[:limit]

    def hybrid_search(self, query: str, top_k: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion (RRF) combining keyword BM25 and vector semantic search."""
        keyword_hits = self.search_keyword(query, limit=top_k * 3)
        vector_hits = self.search_vector(query, limit=top_k * 3)

        rrf_scores: Dict[str, float] = {}
        items_map: Dict[str, Dict[str, Any]] = {}

        for rank, hit in enumerate(keyword_hits, 1):
            cid = hit["chunk_id"]
            items_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        for rank, hit in enumerate(vector_hits, 1):
            cid = hit["chunk_id"]
            if cid not in items_map:
                items_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        
        final_results = []
        for cid in sorted_cids[:top_k]:
            item = items_map[cid].copy()
            item["rrf_score"] = round(rrf_scores[cid], 4)
            final_results.append(item)
        return final_results

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as chunk_count FROM chunks")
            chunk_count = cursor.fetchone()["chunk_count"]
            cursor.execute("SELECT count(DISTINCT article_url) as article_count FROM chunks")
            article_count = cursor.fetchone()["article_count"]
            cursor.execute("SELECT count(*) as escalation_count FROM escalations WHERE status = 'PENDING'")
            escalation_count = cursor.fetchone()["escalation_count"]
            return {
                "total_chunks": chunk_count,
                "indexed_articles": article_count,
                "pending_escalations": escalation_count
            }
