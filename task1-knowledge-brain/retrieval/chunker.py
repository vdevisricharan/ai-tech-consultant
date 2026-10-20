import re
from typing import List, Dict, Any

try:
    from ingestion.models import ArticleContent, ArticleChunk
except ImportError:
    from ..ingestion.models import ArticleContent, ArticleChunk

class SectionChunker:
    def __init__(self, max_words_per_chunk: int = 350, overlap_words: int = 50):
        self.max_words = max_words_per_chunk
        self.overlap = overlap_words

    def chunk_article(self, article: ArticleContent) -> List[ArticleChunk]:
        chunks: List[ArticleChunk] = []
        body = article.body_markdown
        title = article.metadata.title
        category = article.metadata.category
        folder = article.metadata.folder
        url = article.metadata.url

        # Extract image references in the article
        all_image_urls = [img.image_url for img in article.images]

        # Split markdown into sections based on headers (#, ##, ###)
        sections = re.split(r"\n(?=#{1,4}\s+)", body)
        chunk_idx = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Identify section heading
            heading_match = re.match(r"^(#{1,4}\s+([^\n]+))", section)
            if heading_match:
                heading = heading_match.group(2).strip()
            else:
                heading = "Overview"

            # Check for images referenced in this section
            section_images = [img_url for img_url in all_image_urls if img_url in section]

            words = section.split()
            if len(words) <= self.max_words:
                chunk_id = f"{abs(hash(url)) % 100000}_{chunk_idx}"
                formatted_content = f"Article: {title}\nSection: {heading}\nCategory: {category} > {folder}\n\n{section}"
                chunks.append(ArticleChunk(
                    chunk_id=chunk_id,
                    article_url=url,
                    article_title=title,
                    category=category,
                    folder=folder,
                    heading=heading,
                    content=formatted_content,
                    token_count=len(words),
                    image_refs=section_images
                ))
                chunk_idx += 1
            else:
                # Sliding window split for long sections
                start = 0
                while start < len(words):
                    end = min(start + self.max_words, len(words))
                    sub_words = words[start:end]
                    sub_text = " ".join(sub_words)
                    chunk_id = f"{abs(hash(url)) % 100000}_{chunk_idx}"
                    formatted_content = f"Article: {title}\nSection: {heading} (Part {chunk_idx + 1})\nCategory: {category} > {folder}\n\n{sub_text}"
                    chunks.append(ArticleChunk(
                        chunk_id=chunk_id,
                        article_url=url,
                        article_title=title,
                        category=category,
                        folder=folder,
                        heading=heading,
                        content=formatted_content,
                        token_count=len(sub_words),
                        image_refs=section_images
                    ))
                    chunk_idx += 1
                    if end >= len(words):
                        break
                    start += self.max_words - self.overlap

        article.chunks = chunks
        return chunks
