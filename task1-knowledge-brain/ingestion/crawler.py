import asyncio
import logging
import random
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
import httpx
from bs4 import BeautifulSoup

from .models import ArticleContent, ArticleMetadata, IngestionStatusEnum
from .manifest import ManifestManager
from .parser import ArticleParser

logger = logging.getLogger("crawler")

class PoliteSitemapCrawler:
    def __init__(
        self,
        manifest: ManifestManager,
        concurrency: int = 3,
        delay_ms: int = 350,
        max_retries: int = 3,
        timeout_sec: float = 15.0
    ):
        self.manifest = manifest
        self.semaphore = asyncio.Semaphore(concurrency)
        self.delay_sec = delay_ms / 1000.0
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec
        self.headers = {
            "User-Agent": "AITechConsultantKnowledgeBot/1.0 (+http://localhost:8000/bot-info)"
        }

    async def fetch_sitemap_urls(self, sitemap_url: str) -> List[str]:
        """Downloads and parses sitemap XML, returning list of article URLs."""
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout_sec) as client:
            resp = await client.get(sitemap_url)
            resp.raise_for_status()
            
            try:
                root = ET.fromstring(resp.content)
                # Handle namespaces in sitemap XML
                namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                loc_elements = root.findall(".//sm:loc", namespaces)
                if not loc_elements:
                    # Try without namespace
                    loc_elements = root.findall(".//loc")
                locs = [el.text.strip() for el in loc_elements if el.text and el.text.strip()]
            except Exception as e:
                logger.warning(f"Standard XML parse failed ({e}), falling back to regex")
                import re
                locs = re.findall(r"<loc>(https?://[^<]+)</loc>", resp.text)
            
            # Clean and deduplicate
            unique_urls = list(dict.fromkeys(locs))
            logger.info(f"Discovered {len(unique_urls)} URLs from sitemap {sitemap_url}")
            return unique_urls

    async def fetch_and_parse_article(
        self,
        client: httpx.AsyncClient,
        url: str
    ) -> Optional[ArticleContent]:
        existing = self.manifest.get_record(url)
        retries = existing.retry_count if existing else 0

        for attempt in range(retries, self.max_retries + 1):
            try:
                async with self.semaphore:
                    # Apply delay with jitter to be polite to the host
                    jitter = random.uniform(0.8, 1.2) * self.delay_sec
                    await asyncio.sleep(jitter)

                    response = await client.get(url)
                    if response.status_code == 404:
                        logger.warning(f"URL 404 Not Found: {url}")
                        self.manifest.update_record(ArticleMetadata(
                            url=url,
                            title="404 Not Found",
                            status=IngestionStatusEnum.DELETED,
                            crawled_at=datetime.utcnow(),
                            error_message="HTTP 404 Not Found",
                            retry_count=attempt
                        ))
                        return None
                    
                    response.raise_for_status()
                    article = ArticleParser.parse_html(response.text, url)
                    article.metadata.crawled_at = datetime.utcnow()
                    article.metadata.retry_count = attempt

                    # Check if modified or unchanged
                    if existing and existing.content_hash == article.metadata.content_hash:
                        article.metadata.status = IngestionStatusEnum.INDEXED
                    elif existing and existing.content_hash != "":
                        article.metadata.status = IngestionStatusEnum.MODIFIED
                    else:
                        article.metadata.status = IngestionStatusEnum.INDEXED

                    self.manifest.update_record(article.metadata)
                    return article

            except (httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError) as err:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {err}")
                if attempt >= self.max_retries:
                    self.manifest.update_record(ArticleMetadata(
                        url=url,
                        title=existing.title if existing else "",
                        status=IngestionStatusEnum.FAILED,
                        crawled_at=datetime.utcnow(),
                        error_message=str(err),
                        retry_count=attempt + 1
                    ))
                    return None
                # Exponential backoff
                await asyncio.sleep((2 ** attempt) + random.uniform(0.5, 1.5))
        return None

    async def crawl_batch(
        self,
        urls: List[str],
        on_article_crawled: Optional[Callable[[ArticleContent], None]] = None
    ) -> List[ArticleContent]:
        results: List[ArticleContent] = []
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout_sec, follow_redirects=True) as client:
            tasks = [self.fetch_and_parse_article(client, url) for url in urls]
            for future in asyncio.as_completed(tasks):
                article = await future
                if article:
                    results.append(article)
                    if on_article_crawled:
                        on_article_crawled(article)
        return results
