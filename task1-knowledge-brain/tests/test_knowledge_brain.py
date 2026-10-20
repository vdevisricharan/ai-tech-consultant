import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from datetime import datetime
from ingestion.models import ArticleMetadata, IngestionStatusEnum, ExtractedImage, ArticleChunk
from ingestion.parser import ArticleParser
from ingestion.manifest import ManifestManager
from retrieval.chunker import SectionChunker
from retrieval.store import HybridKnowledgeStore
from app.rag import RAGService

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>How to Set Up Custom Domains - Brilliant Directories</title></head>
<body>
    <nav><a href="/home">Home</a></nav>
    <div class="breadcrumb">
        <span>Solution home</span> &gt; <span>Domains & Email</span>
    </div>
    <main>
        <h1>How to Set Up Custom Domains</h1>
        <p>Connecting a custom domain allows you to brand your directory website.</p>
        <h2>Step 1: Point DNS Records</h2>
        <p>Log in to your domain registrar (GoDaddy, Namecheap) and create an A Record pointing to 54.208.192.173.</p>
        <img src="https://cdn.example.com/dns_screenshot.png" alt="DNS Records A Record Configuration" />
        <h2>Step 2: Update Domain in Admin Portal</h2>
        <p>Navigate to Settings &gt; General Settings &gt; Domain Name tab and paste your live URL.</p>
    </main>
    <footer>Copyright 2026 Brilliant Directories</footer>
</body>
</html>
"""

def test_article_parser():
    content = ArticleParser.parse_html(SAMPLE_HTML, "https://support.brilliantdirectories.com/articles/custom-domain")
    assert content.metadata.title == "How to Set Up Custom Domains"
    assert "Connecting a custom domain" in content.body_markdown
    assert "Step 1: Point DNS Records" in content.headings
    assert "Step 2: Update Domain in Admin Portal" in content.headings
    assert len(content.images) == 1
    assert content.images[0].image_url == "https://cdn.example.com/dns_screenshot.png"
    assert "DNS Records" in content.images[0].alt_text
    assert len(content.metadata.content_hash) == 64

def test_manifest_manager(tmp_path):
    db_file = str(tmp_path / "test_manifest.db")
    m = ManifestManager(db_file)
    
    # Sync URLs
    urls = [
        "https://example.com/a1",
        "https://example.com/a2",
        "https://example.com/a3"
    ]
    stats = m.sync_sitemap_urls(urls)
    assert stats["new"] == 3
    assert stats["deleted"] == 0

    pending = m.get_pending_urls(limit=10)
    assert len(pending) == 3

    # Update record
    rec = ArticleMetadata(
        url="https://example.com/a1",
        title="Article 1",
        content_hash="abc123hash",
        status=IngestionStatusEnum.INDEXED,
        crawled_at=datetime.utcnow()
    )
    m.update_record(rec)

    fetched = m.get_record("https://example.com/a1")
    assert fetched is not None
    assert fetched.status == IngestionStatusEnum.INDEXED
    assert fetched.content_hash == "abc123hash"

    # Sync again with a1 removed -> should detect deleted
    m.sync_sitemap_urls(["https://example.com/a2", "https://example.com/a3"])
    after_sync = m.get_record("https://example.com/a1")
    assert after_sync.status == IngestionStatusEnum.DELETED

def test_section_chunker():
    content = ArticleParser.parse_html(SAMPLE_HTML, "https://support.brilliantdirectories.com/articles/custom-domain")
    chunker = SectionChunker(max_words_per_chunk=100)
    chunks = chunker.chunk_article(content)
    
    assert len(chunks) >= 2
    assert chunks[0].article_title == "How to Set Up Custom Domains"
    assert "How to Set Up Custom Domains" in chunks[0].content
    # Check that image reference was attached to the DNS step chunk
    dns_chunk = [c for c in chunks if "Point DNS Records" in c.heading][0]
    assert "https://cdn.example.com/dns_screenshot.png" in dns_chunk.image_refs

def test_hybrid_search_and_rag(tmp_path):
    db_file = str(tmp_path / "test_rag.db")
    store = HybridKnowledgeStore(db_file)
    content = ArticleParser.parse_html(SAMPLE_HTML, "https://support.brilliantdirectories.com/articles/custom-domain")
    chunker = SectionChunker()
    chunks = chunker.chunk_article(content)
    for c in chunks:
        store.insert_chunk(c)

    # Keyword search test
    hits = store.search_keyword("DNS registrar")
    assert len(hits) > 0
    assert "54.208.192.173" in hits[0]["content"]

    # Hybrid search test
    hybrid_hits = store.hybrid_search("how do I point my domain to Brilliant Directories?")
    assert len(hybrid_hits) > 0
    assert hybrid_hits[0]["article_url"] == "https://support.brilliantdirectories.com/articles/custom-domain"

    # RAG answering test
    rag = RAGService(store=store, api_key="")
    response = asyncio.run(rag.answer("What IP address should I point my A record to?"))
    assert response.status == "answered"
    assert len(response.sources) > 0
    assert "54.208.192.173" in response.answer

    # Unanswerable query test
    unanswerable = asyncio.run(rag.answer("What is the recipe for chocolate cake?"))
    # Either insufficient evidence or no relevant hits
    assert unanswerable.confidence < 0.35 or unanswerable.status == "insufficient_evidence"

def test_human_escalation_lifecycle(tmp_path):
    db_file = str(tmp_path / "test_escalation.db")
    store = HybridKnowledgeStore(db_file)
    rag = RAGService(store=store, api_key="")

    # Initially unanswerable
    res1 = store.search_keyword("Quantum teleportation widget")
    assert len(res1) == 0

    # Ingest expert resolution chunk
    expert_chunk = ArticleChunk(
        chunk_id="esc_99_test",
        article_url="internal://escalation/99",
        article_title="Expert Resolution: Quantum teleportation widget",
        category="Expert Resolutions",
        folder="Verified Knowledge",
        heading="Resolution",
        content="Question: How to enable Quantum teleportation widget?\nExpert Answer: Navigate to Developer Tools > Experimental Modules > Toggle Quantum Teleportation ON.",
        token_count=20
    )
    store.insert_chunk(expert_chunk)

    # Now retrieval should find it immediately
    hits = store.hybrid_search("Quantum teleportation widget")
    assert len(hits) > 0
    assert "Toggle Quantum Teleportation ON" in hits[0]["content"]
