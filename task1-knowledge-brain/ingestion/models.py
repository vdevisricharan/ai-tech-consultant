from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IngestionStatusEnum(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    INDEXED = "INDEXED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    FAILED = "FAILED"

class SitemapEntry(BaseModel):
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None

class ExtractedImage(BaseModel):
    image_url: str
    alt_text: str = ""
    surrounding_text: str = ""
    ui_description: Optional[str] = None
    detected_labels: List[str] = Field(default_factory=list)
    local_cache_path: Optional[str] = None

class ArticleMetadata(BaseModel):
    url: str
    title: str
    category: str = "General"
    folder: str = "General"
    last_modified: Optional[str] = None
    content_hash: str = ""
    status: IngestionStatusEnum = IngestionStatusEnum.NEW
    crawled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class ArticleChunk(BaseModel):
    chunk_id: str
    article_url: str
    article_title: str
    category: str
    folder: str
    heading: str
    content: str
    token_count: int = 0
    image_refs: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None

class ArticleContent(BaseModel):
    metadata: ArticleMetadata
    body_markdown: str
    headings: List[str] = Field(default_factory=list)
    images: List[ExtractedImage] = Field(default_factory=list)
    chunks: List[ArticleChunk] = Field(default_factory=list)
