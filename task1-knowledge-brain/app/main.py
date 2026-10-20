import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

try:
    from app.config import settings
    from app.schemas import (
        QueryRequest, QueryResponse, EscalationCreate, EscalationResolve,
        EscalationRecord, IngestionRunRequest, IngestionStatusResponse
    )
    from ingestion.manifest import ManifestManager
    from ingestion.crawler import PoliteSitemapCrawler
    from ingestion.parser import ArticleParser
    from retrieval.chunker import SectionChunker
    from retrieval.store import HybridKnowledgeStore
    from multimodal.image_understanding import ImageUnderstandingService
    from app.rag import RAGService
except ImportError:
    from .config import settings
    from .schemas import (
        QueryRequest, QueryResponse, EscalationCreate, EscalationResolve,
        EscalationRecord, IngestionRunRequest, IngestionStatusResponse
    )
    from ..ingestion.manifest import ManifestManager
    from ..ingestion.crawler import PoliteSitemapCrawler
    from ..ingestion.parser import ArticleParser
    from ..retrieval.chunker import SectionChunker
    from ..retrieval.store import HybridKnowledgeStore
    from ..multimodal.image_understanding import ImageUnderstandingService
    from .rag import RAGService

# Initialize core services
manifest = ManifestManager(settings.task1_db_path)
store = HybridKnowledgeStore(settings.task1_db_path)
chunker = SectionChunker()
crawler = PoliteSitemapCrawler(
    manifest=manifest,
    concurrency=settings.crawler_max_concurrency,
    delay_ms=settings.crawler_delay_ms,
    max_retries=settings.crawler_max_retries,
    timeout_sec=settings.crawler_timeout_sec
)
vision_service = ImageUnderstandingService(api_key=settings.anthropic_api_key)
rag_service = RAGService(store=store, api_key=settings.anthropic_api_key)

is_ingesting = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup check
    yield
    # Shutdown logic if any

app = FastAPI(
    title="Knowledge Brain API",
    description="Knowledge base service for Brilliant Directories solution center",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_ingestion_background(limit: int = 50, force_rescrape: bool = False):
    global is_ingesting
    if is_ingesting:
        return
    is_ingesting = True
    try:
        urls = await crawler.fetch_sitemap_urls(settings.sitemap_url)
        # Filter for article URLs
        article_urls = [u for u in urls if "/support/solutions/articles/" in u]
        manifest.sync_sitemap_urls(article_urls)

        pending = manifest.get_pending_urls(limit=limit)
        
        async def handle_article(article):
            # Process screenshots if any
            for img in article.images:
                analysis = await vision_service.analyze_screenshot(
                    img.image_url,
                    article.metadata.title,
                    img.surrounding_text
                )
                img.ui_description = analysis.get("ui_description")
                img.detected_labels = analysis.get("detected_labels", [])
            
            # Chunk and insert into store
            chunks = chunker.chunk_article(article)
            # Remove old chunks if article was modified
            store.delete_article_chunks(article.metadata.url)
            for c in chunks:
                store.insert_chunk(c)

        for url in pending:
            async with crawler.semaphore:
                art = await crawler.fetch_and_parse_article(crawler.headers, url) if False else None
        
        # Batch crawling
        articles = await crawler.crawl_batch(pending)
        for art in articles:
            await handle_article(art)
    finally:
        is_ingesting = False

@app.get("/api/v1/health")
async def health_check():
    stats = store.get_stats()
    return {
        "status": "healthy",
        "service": "Knowledge Brain API",
        "timestamp": datetime.utcnow().isoformat(),
        "database": stats
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_knowledge(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return await rag_service.answer(req.question, top_k=req.top_k, model=req.model or "claude-3-5-sonnet-20241022")

@app.post("/api/v1/ingestion/run")
async def trigger_ingestion(req: IngestionRunRequest, bg_tasks: BackgroundTasks):
    global is_ingesting
    if is_ingesting:
        return {"status": "in_progress", "message": "Ingestion job is already running"}
    
    bg_tasks.add_task(run_ingestion_background, limit=req.limit or 50, force_rescrape=req.force_rescrape)
    return {"status": "started", "message": f"Background ingestion scheduled for up to {req.limit} articles"}

@app.get("/api/v1/ingestion/status", response_model=IngestionStatusResponse)
async def get_ingestion_status():
    manifest_stats = manifest.get_stats()
    store_stats = store.get_stats()
    return IngestionStatusResponse(
        total_articles=manifest_stats["total"],
        indexed=manifest_stats["indexed"],
        new=manifest_stats["new"],
        modified=manifest_stats["modified"],
        failed=manifest_stats["failed"],
        deleted=manifest_stats["deleted"],
        total_chunks=store_stats["total_chunks"],
        pending_escalations=store_stats["pending_escalations"]
    )

@app.post("/api/v1/escalations", response_model=Dict[str, Any])
async def create_escalation(esc: EscalationCreate):
    with manifest._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO escalations (question, context, reason, status, created_at)
            VALUES (?, ?, ?, 'PENDING', ?)
        """, (esc.question, esc.context, esc.reason, datetime.utcnow().isoformat()))
        conn.commit()
        esc_id = cursor.lastrowid
    return {"id": esc_id, "status": "created", "message": "Human expert escalation task created"}

@app.get("/api/v1/escalations", response_model=List[EscalationRecord])
async def list_escalations():
    with manifest._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM escalations ORDER BY id DESC")
        rows = cursor.fetchall()
        return [
            EscalationRecord(
                id=r["id"],
                question=r["question"],
                context=r["context"],
                reason=r["reason"],
                status=r["status"],
                expert_answer=r["expert_answer"],
                created_at=r["created_at"],
                resolved_at=r["resolved_at"]
            )
            for r in rows
        ]

@app.post("/api/v1/escalations/{esc_id}/resolve")
async def resolve_escalation(esc_id: int, res: EscalationResolve):
    with manifest._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM escalations WHERE id = ?", (esc_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Escalation record not found")
        
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE escalations 
            SET status = 'RESOLVED', expert_answer = ?, resolved_at = ?
            WHERE id = ?
        """, (res.expert_answer, now, esc_id))
        conn.commit()

        # Ingest expert resolution as high-priority memory chunk
        chunk_id = f"esc_{esc_id}_{int(datetime.utcnow().timestamp())}"
        from ..ingestion.models import ArticleChunk
        expert_chunk = ArticleChunk(
            chunk_id=chunk_id,
            article_url=f"internal://escalation/{esc_id}",
            article_title=f"Expert Answer: {row['question'][:50]}",
            category="Expert Resolutions",
            folder="Human Feedback",
            heading="Verified Solution",
            content=f"Question: {row['question']}\n\nExpert Verified Answer:\n{res.expert_answer}",
            token_count=len(res.expert_answer.split())
        )
        store.insert_chunk(expert_chunk)

    return {
        "id": esc_id,
        "status": "resolved",
        "message": "Expert answer recorded and ingested into Knowledge Brain memory"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.task1_port, reload=True)
