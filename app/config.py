"""Configuration for BriefEngine."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "outputs")
DATABASE_PATH = PROJECT_ROOT / os.getenv("DATABASE_PATH", "storage/briefengine.db")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Model Configuration ────────────────────────────────────────────────
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4o")
EDITOR_MODEL = os.getenv("EDITOR_MODEL", "gpt-4o")

AGENT_CONFIGS = {
    "ceo": {
        "model": DEFAULT_MODEL,
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "research": {
        "model": DEFAULT_MODEL,
        "temperature": 0.5,
        "max_tokens": 3000,
    },
    "outline": {
        "model": DEFAULT_MODEL,
        "temperature": 0.4,
        "max_tokens": 2000,
    },
    "writer": {
        "model": WRITER_MODEL,
        "temperature": 0.7,
        "max_tokens": 8000,
    },
    "seo": {
        "model": DEFAULT_MODEL,
        "temperature": 0.2,
        "max_tokens": 2000,
    },
    "editor": {
        "model": EDITOR_MODEL,
        "temperature": 0.3,
        "max_tokens": 8000,
    },
    "quality_fixer": {
        "model": DEFAULT_MODEL,
        "temperature": 0.2,
        "max_tokens": 6000,
    },
    "profile": {
        "model": DEFAULT_MODEL,
        "temperature": 0.3,
        "max_tokens": 2000,
    },
}

# ── Operational Settings ───────────────────────────────────────────────
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Article Defaults ──────────────────────────────────────────────────
DEFAULT_ARTICLE_LENGTH = 1800  # target word count
MIN_ARTICLE_LENGTH = 1200
MAX_ARTICLE_LENGTH = 3000
# ── Web Research Settings ─────────────────────────────────────────────
ENABLE_WEB_RESEARCH = os.getenv("ENABLE_WEB_RESEARCH", "0").lower() in ("1", "true", "yes")
WEB_RESEARCH_MAX_RESULTS = int(os.getenv("WEB_RESEARCH_MAX_RESULTS", "5"))
WEB_RESEARCH_FETCH_TOP_N = int(os.getenv("WEB_RESEARCH_FETCH_TOP_N", "3"))
WEB_RESEARCH_MAX_CHARS_PER_SOURCE = int(os.getenv("WEB_RESEARCH_MAX_CHARS_PER_SOURCE", "8000"))
WEB_RESEARCH_TIMEOUT_SECONDS = int(os.getenv("WEB_RESEARCH_TIMEOUT_SECONDS", "12"))
WEB_RESEARCH_USER_AGENT = os.getenv(
    "WEB_RESEARCH_USER_AGENT",
    "BriefEngineBot/0.2 (+https://example.com; research)",
)

# ── Quality Guardrails ────────────────────────────────────────────────
QUALITY_STRICT_MODE = os.getenv("QUALITY_STRICT_MODE", "0").lower() in ("1", "true", "yes")
QUALITY_AUTO_REPAIR = os.getenv("QUALITY_AUTO_REPAIR", "1").lower() in ("1", "true", "yes")
QUALITY_MIN_CITATIONS = int(os.getenv("QUALITY_MIN_CITATIONS", "2"))
QUALITY_MIN_FAQS = int(os.getenv("QUALITY_MIN_FAQS", "4"))

# ── AI Visibility ─────────────────────────────────────────────────────
AI_VISIBILITY_ENABLE = os.getenv("AI_VISIBILITY_ENABLE", "1").lower() in ("1", "true", "yes")
AI_VISIBILITY_INCLUDE_JSONLD = os.getenv("AI_VISIBILITY_INCLUDE_JSONLD", "1").lower() in ("1", "true", "yes")

