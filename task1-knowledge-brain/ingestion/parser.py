import re
import hashlib
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from .models import ArticleContent, ArticleMetadata, ExtractedImage, IngestionStatusEnum

class ArticleParser:
    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def parse_html(cls, html: str, url: str) -> ArticleContent:
        soup = BeautifulSoup(html, "html.parser")

        # Strip script, style, navigation, header, footer elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()

        # Extract title
        title = ""
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        elif soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True).split("-")[0].strip()
        else:
            title = "Untitled Article"

        # Extract Breadcrumbs (Category / Folder)
        category = "General"
        folder = "General"
        breadcrumbs = soup.find(class_=re.compile(r"breadcrumb|crumbs|navigation-path", re.I))
        if breadcrumbs:
            crumbs = [c.get_text(strip=True) for c in breadcrumbs.find_all(["a", "span", "li"]) if c.get_text(strip=True)]
            # Filter out home / solution center
            crumbs = [c for c in crumbs if c.lower() not in ["home", "solutions", "solution center", "help center", ">", "/"]]
            if len(crumbs) >= 2:
                category = crumbs[0]
                folder = crumbs[1]
            elif len(crumbs) == 1:
                category = crumbs[0]

        # Target main content area
        main_content = (
            soup.find("article") or
            soup.find("main") or
            soup.find(class_=re.compile(r"article-body|content-body|article__body|post-content", re.I)) or
            soup.find(id=re.compile(r"article|content|main", re.I)) or
            soup.body or
            soup
        )

        headings: List[str] = []
        body_lines: List[str] = []
        extracted_images: List[ExtractedImage] = []

        # Iterate over structural children
        for tag in main_content.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table", "img"]):
            if tag.name in ["h1", "h2", "h3", "h4"]:
                h_text = tag.get_text(strip=True)
                if h_text and h_text != title:
                    headings.append(h_text)
                    prefix = "#" * int(tag.name[1])
                    body_lines.append(f"\n{prefix} {h_text}\n")
            elif tag.name == "p":
                p_text = tag.get_text(strip=True)
                if p_text:
                    body_lines.append(p_text)
            elif tag.name in ["ul", "ol"]:
                for idx, li in enumerate(tag.find_all("li", recursive=False), 1):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        bullet = f"{idx}." if tag.name == "ol" else "-"
                        body_lines.append(f"{bullet} {li_text}")
            elif tag.name == "table":
                # Convert table rows
                rows = tag.find_all("tr")
                for r in rows:
                    cols = [c.get_text(strip=True) for c in r.find_all(["th", "td"])]
                    if cols:
                        body_lines.append(" | ".join(cols))
            elif tag.name == "img":
                src = tag.get("src") or tag.get("data-src")
                if src and not src.startswith("data:"):
                    alt = tag.get("alt", "").strip()
                    # Capture surrounding context
                    prev_sib = tag.find_previous(["p", "li", "h2", "h3"])
                    surrounding = prev_sib.get_text(strip=True) if prev_sib else ""
                    # Normalize relative URL
                    if src.startswith("//"):
                        src = f"https:{src}"
                    elif src.startswith("/"):
                        src = f"https://support.brilliantdirectories.com{src}"
                    
                    # Filter out tiny icon / tracking pixels
                    if not re.search(r"icon|avatar|logo|badge|pixel|spinner", src, re.I):
                        extracted_images.append(ExtractedImage(
                            image_url=src,
                            alt_text=alt,
                            surrounding_text=surrounding
                        ))
                        body_lines.append(f"\n[Screenshot: {alt or 'Interface visual'}]({src})\n")

        body_markdown = "\n\n".join(body_lines).strip()
        content_hash = cls.compute_hash(body_markdown)

        metadata = ArticleMetadata(
            url=url,
            title=title,
            category=category,
            folder=folder,
            content_hash=content_hash,
            status=IngestionStatusEnum.NEW
        )

        return ArticleContent(
            metadata=metadata,
            body_markdown=body_markdown,
            headings=headings,
            images=extracted_images
        )
