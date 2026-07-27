"""
Production system configuration for $0-marginal-cost YouTube video pipeline.

This module centralizes all configuration, API credentials, and production parameters.
All tools import from here to maintain consistency.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import json

# Load environment variables from .env
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

# ============================================================================
# API CREDENTIALS (loaded from .env, never hardcoded)
# ============================================================================

class APICredentials:
    """Centralized API credential management."""
    
    # Gemini API (free tier: 60 req/min = ~$0 per week for your use case)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Grok API (free tier available)
    GROK_API_KEY = os.getenv("GROK_API_KEY", "")
    
    # TMDB API (free tier: 40 requests/10s)
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    
    # TVMaze API (free, no key needed)
    TVMAZE_API_KEY = None  # No key required
    
    # YouTube API (for publishing)
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    
    # Google Cloud TTS (service account JSON path)
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    
    # Pixabay API (free tier: 100 req/day)
    PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
    
    # Pexels API (free tier: 200 req/hour)
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
    
    # Internet Archive API (free, no key needed)
    INTERNETARCHIVE_API_KEY = None  # No key required
    
    @classmethod
    def validate(cls) -> Dict[str, bool]:
        """Check which APIs are configured."""
        return {
            "gemini": bool(cls.GEMINI_API_KEY),
            "grok": bool(cls.GROK_API_KEY),
            "tmdb": bool(cls.TMDB_API_KEY),
            "youtube": bool(cls.YOUTUBE_API_KEY),
            "google_cloud_tts": bool(cls.GOOGLE_SERVICE_ACCOUNT_JSON),
            "pixabay": bool(cls.PIXABAY_API_KEY),
            "pexels": bool(cls.PEXELS_API_KEY),
        }


# ============================================================================
# PRODUCTION PARAMETERS
# ============================================================================

@dataclass
class ProductionConfig:
    """Core production configuration."""
    
    # Output directory structure
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "production_output"
    CACHE_DIR: Path = OUTPUT_DIR / "cache"
    ASSETS_DIR: Path = OUTPUT_DIR / "assets"
    SCRIPTS_DIR: Path = OUTPUT_DIR / "scripts"
    STORYBOARDS_DIR: Path = OUTPUT_DIR / "storyboards"
    COMPOSITIONS_DIR: Path = OUTPUT_DIR / "compositions"
    RENDERS_DIR: Path = OUTPUT_DIR / "renders"
    METADATA_DIR: Path = OUTPUT_DIR / "metadata"
    
    # Production parameters
    TARGET_VIDEO_LENGTH_SECONDS: int = 600  # 10 minutes
    TARGET_BITRATE: str = "5000k"  # 5 Mbps (YouTube recommendation)
    TARGET_RESOLUTION: str = "1920x1080"  # 1080p
    TARGET_FPS: int = 30
    
    # Cost budget (warning/capping)
    MONTHLY_BUDGET_USD: float = 0.0  # $0 budget (free tier only)
    WARN_THRESHOLD_USD: float = 0.10  # Warn if approaching $0.10
    
    # Batch processing
    PARALLEL_RESEARCH_WORKERS: int = 4
    PARALLEL_ASSET_FETCHES: int = 6
    PARALLEL_TTS_JOBS: int = 2
    PARALLEL_RENDERS: int = 1  # Usually 1 (CPU bound)
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 2
    
    # Pipeline settings
    SKIP_HUMAN_APPROVAL: bool = False  # Require manual review before publish
    AUTO_PUBLISH: bool = False  # Never auto-publish (always manual)
    ARCHIVE_RAW_ASSETS: bool = True  # Keep all downloaded assets for reuse
    
    # Quality settings
    MIN_SCRIPT_LENGTH_WORDS: int = 800
    MAX_SCRIPT_LENGTH_WORDS: int = 3000
    CAPTION_LANGUAGE: str = "en"
    MUSIC_PREFERENCE: str = "instrumental"  # background, instrumental, ambient
    
    def __post_init__(self):
        """Create necessary directories."""
        for dir_path in [
            self.OUTPUT_DIR,
            self.CACHE_DIR,
            self.ASSETS_DIR,
            self.SCRIPTS_DIR,
            self.STORYBOARDS_DIR,
            self.COMPOSITIONS_DIR,
            self.RENDERS_DIR,
            self.METADATA_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export config as dict."""
        return {
            "target_video_length_seconds": self.TARGET_VIDEO_LENGTH_SECONDS,
            "target_resolution": self.TARGET_RESOLUTION,
            "target_fps": self.TARGET_FPS,
            "monthly_budget_usd": self.MONTHLY_BUDGET_USD,
            "parallel_workers": {
                "research": self.PARALLEL_RESEARCH_WORKERS,
                "assets": self.PARALLEL_ASSET_FETCHES,
                "tts": self.PARALLEL_TTS_JOBS,
                "renders": self.PARALLEL_RENDERS,
            },
            "auto_publish": self.AUTO_PUBLISH,
        }


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

config = ProductionConfig()
credentials = APICredentials()

# Validate on import
api_status = credentials.validate()
missing = [k for k, v in api_status.items() if not v]
if missing:
    print(f"WARNING: Missing API keys: {', '.join(missing)}")
    print(f"   Add them to .env file for full functionality")
