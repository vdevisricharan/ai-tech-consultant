from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    task1_port: int = Field(default=8000, alias="TASK1_PORT")
    task1_host: str = Field(default="0.0.0.0", alias="TASK1_HOST")
    task1_db_path: str = Field(default="data/knowledge_brain.db", alias="TASK1_DB_PATH")
    sitemap_url: str = Field(
        default="https://support.brilliantdirectories.com/support/sitemap.xml",
        alias="SITEMAP_URL"
    )
    
    # Crawler safeguards
    crawler_max_concurrency: int = 3
    crawler_delay_ms: int = 350
    crawler_max_retries: int = 3
    crawler_timeout_sec: float = 15.0
    
    # Retrieval & RAG
    hybrid_top_k: int = 5
    rrf_k: int = 60
    min_relevance_score: float = 0.40
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
