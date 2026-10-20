import base64
import logging
import io
from typing import Optional, List, Dict, Any
from pathlib import Path
import httpx
from PIL import Image

logger = logging.getLogger("vision")

class ImageUnderstandingService:
    def __init__(self, api_key: str = "", cache_dir: str = "data/image_cache"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(self, image_url: str) -> Optional[bytes]:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(image_url)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.warning(f"Failed to download image {image_url}: {e}")
        return None

    async def analyze_screenshot(
        self,
        image_url: str,
        article_title: str,
        surrounding_text: str
    ) -> Dict[str, Any]:
        """Analyzes a software screenshot using Claude Vision or intelligent context fallback."""
        image_bytes = await self.download_image(image_url)
        if not image_bytes:
            return {
                "ui_description": f"Screenshot from {article_title}: related to {surrounding_text[:100]}",
                "detected_labels": [],
                "cached": False
            }

        # Cache image locally
        try:
            filename = f"img_{abs(hash(image_url)) % 1000000}.png"
            local_path = self.cache_dir / filename
            with open(local_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            logger.warning(f"Could not cache image locally: {e}")

        # If Anthropic API Key is present, call Claude 3.5 Sonnet
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.api_key)
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # Check image format with PIL
                img = Image.open(io.BytesIO(image_bytes))
                media_type = f"image/{img.format.lower() if img.format else 'png'}"
                if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                    media_type = "image/png"

                prompt = (
                    f"Analyze this software UI screenshot from the help article '{article_title}'. "
                    f"Surrounding article text: '{surrounding_text}'.\n"
                    "Identify specific UI settings, menu paths, field names, buttons, and procedural steps. "
                    "Output a concise 2-4 sentence description and a comma-separated list of visible labels."
                )

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": b64_image
                                    }
                                },
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ]
                )
                text = response.content[0].text
                return {
                    "ui_description": text,
                    "detected_labels": [l.strip() for l in text.split("\n")[-1].replace("Labels:", "").split(",") if l.strip()],
                    "cached": True
                }
            except Exception as e:
                logger.warning(f"Claude Vision call failed ({e}), falling back to context analysis")

        # Deterministic context fallback
        return {
            "ui_description": f"Interface screenshot in '{article_title}' illustrating: {surrounding_text or 'configuration options'}",
            "detected_labels": [word for word in surrounding_text.split() if len(word) > 4][:5],
            "cached": True
        }
