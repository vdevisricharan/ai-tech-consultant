import asyncio
import logging
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from ingestion.manifest import ManifestManager
from ingestion.crawler import PoliteSitemapCrawler
from retrieval.chunker import SectionChunker
from retrieval.store import HybridKnowledgeStore
from multimodal.image_understanding import ImageUnderstandingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

# Core representative articles across Brilliant Directories categories
SEED_ARTICLE_URLS = [
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558357-can-i-send-a-mass-email-campaign-using-brilliant-directories-",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558363-emails-email-accounts",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558373-email-forwarders",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558389-settings-general-settings-social-media-tab",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558401-how-to-import-categories-via-csv-file",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558416-how-to-setup-payment-gateways-stripe-paypal-etc-",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558425-how-to-manage-leads-and-lead-matching",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558434-how-to-setup-google-maps-api-keys",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558440-how-to-connect-a-custom-domain-name",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558448-how-to-configure-membership-plans-and-pricing",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558452-how-to-refund-or-cancel-a-member-subscription",
    "https://support.brilliantdirectories.com/support/solutions/articles/5000558460-search-settings-location-search-and-radius",
]

async def seed_knowledge_base():
    manifest = ManifestManager(settings.task1_db_path)
    store = HybridKnowledgeStore(settings.task1_db_path)
    chunker = SectionChunker()
    crawler = PoliteSitemapCrawler(manifest=manifest, concurrency=3, delay_ms=300)
    vision = ImageUnderstandingService(api_key=settings.anthropic_api_key)

    logger.info("Syncing seed URLs into manifest...")
    manifest.sync_sitemap_urls(SEED_ARTICLE_URLS)

    logger.info(f"Crawling {len(SEED_ARTICLE_URLS)} core knowledge articles...")
    articles = await crawler.crawl_batch(SEED_ARTICLE_URLS)
    logger.info(f"Successfully crawled {len(articles)} articles.")

    total_chunks = 0
    total_images = 0

    for art in articles:
        # Multimodal image analysis
        for img in art.images:
            analysis = await vision.analyze_screenshot(
                img.image_url,
                art.metadata.title,
                img.surrounding_text
            )
            img.ui_description = analysis.get("ui_description")
            img.detected_labels = analysis.get("detected_labels", [])
            total_images += 1

        chunks = chunker.chunk_article(art)
        store.delete_article_chunks(art.metadata.url)
        for c in chunks:
            store.insert_chunk(c)
            total_chunks += 1

    stats = store.get_stats()
    logger.info("=== Knowledge Base Seeding Complete ===")
    logger.info(f"Indexed Articles: {stats['indexed_articles']}")
    logger.info(f"Total Chunks: {stats['total_chunks']}")
    logger.info(f"Analyzed Screenshots: {total_images}")

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
