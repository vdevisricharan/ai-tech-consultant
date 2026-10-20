import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import ArticleMetadata, IngestionStatusEnum

class ManifestManager:
    def __init__(self, db_path: str = "data/knowledge_brain.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manifest (
                    url TEXT PRIMARY KEY,
                    title TEXT DEFAULT '',
                    category TEXT DEFAULT 'General',
                    folder TEXT DEFAULT 'General',
                    last_modified TEXT,
                    content_hash TEXT DEFAULT '',
                    status TEXT DEFAULT 'NEW',
                    crawled_at TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_manifest_status ON manifest(status)
            """)
            conn.commit()

    def sync_sitemap_urls(self, sitemap_urls: List[str]) -> Dict[str, int]:
        """Compares sitemap URLs against existing manifest and marks new/deleted."""
        stats = {"new": 0, "existing": 0, "deleted": 0}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            existing_urls = {row["url"]: row["status"] for row in cursor.execute("SELECT url, status FROM manifest")}
            
            incoming_set = set(sitemap_urls)
            for url in incoming_set:
                if url not in existing_urls:
                    cursor.execute("""
                        INSERT INTO manifest (url, status) VALUES (?, ?)
                    """, (url, IngestionStatusEnum.NEW.value))
                    stats["new"] += 1
                else:
                    stats["existing"] += 1
            
            # Detect removed URLs
            for url, status in existing_urls.items():
                if url not in incoming_set and status != IngestionStatusEnum.DELETED.value:
                    cursor.execute("""
                        UPDATE manifest SET status = ? WHERE url = ?
                    """, (IngestionStatusEnum.DELETED.value, url))
                    stats["deleted"] += 1
            
            conn.commit()
        return stats

    def get_pending_urls(self, limit: int = 50) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url FROM manifest 
                WHERE status IN (?, ?, ?) 
                ORDER BY retry_count ASC 
                LIMIT ?
            """, (
                IngestionStatusEnum.NEW.value, 
                IngestionStatusEnum.MODIFIED.value, 
                IngestionStatusEnum.FAILED.value,
                limit
            ))
            return [row["url"] for row in cursor.fetchall()]

    def update_record(self, record: ArticleMetadata):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO manifest (
                    url, title, category, folder, last_modified, content_hash,
                    status, crawled_at, error_message, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    folder = excluded.folder,
                    last_modified = excluded.last_modified,
                    content_hash = excluded.content_hash,
                    status = excluded.status,
                    crawled_at = excluded.crawled_at,
                    error_message = excluded.error_message,
                    retry_count = excluded.retry_count
            """, (
                record.url,
                record.title,
                record.category,
                record.folder,
                record.last_modified,
                record.content_hash,
                record.status.value,
                record.crawled_at.isoformat() if record.crawled_at else None,
                record.error_message,
                record.retry_count
            ))
            conn.commit()

    def get_record(self, url: str) -> Optional[ArticleMetadata]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM manifest WHERE url = ?", (url,))
            row = cursor.fetchone()
            if not row:
                return None
            return ArticleMetadata(
                url=row["url"],
                title=row["title"] or "",
                category=row["category"] or "General",
                folder=row["folder"] or "General",
                last_modified=row["last_modified"],
                content_hash=row["content_hash"] or "",
                status=IngestionStatusEnum(row["status"]),
                crawled_at=datetime.fromisoformat(row["crawled_at"]) if row["crawled_at"] else None,
                error_message=row["error_message"],
                retry_count=row["retry_count"] or 0
            )

    def get_stats(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, count(*) as count FROM manifest GROUP BY status")
            counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            cursor.execute("SELECT count(*) as total FROM manifest")
            total = cursor.fetchone()["total"]
            return {
                "total": total,
                "indexed": counts.get(IngestionStatusEnum.INDEXED.value, 0),
                "new": counts.get(IngestionStatusEnum.NEW.value, 0),
                "modified": counts.get(IngestionStatusEnum.MODIFIED.value, 0),
                "failed": counts.get(IngestionStatusEnum.FAILED.value, 0),
                "deleted": counts.get(IngestionStatusEnum.DELETED.value, 0),
            }
