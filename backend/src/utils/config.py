"""
Configuration management for Repo Rover
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class"""

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # GCP OAuth Credentials (for paid tier / higher limits)
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID")
    GCP_CLIENT_ID: Optional[str] = os.getenv("GCP_CLIENT_ID")
    GCP_CLIENT_SECRET: Optional[str] = os.getenv("GCP_CLIENT_SECRET")

    FETCHAI_AGENT_SEED: str = os.getenv("FETCHAI_AGENT_SEED", "")
    FETCHAI_AGENT_MAILBOX_KEY: str = os.getenv("FETCHAI_AGENT_MAILBOX_KEY", "")
    OPENALEX_EMAIL: Optional[str] = os.getenv("OPENALEX_EMAIL")

    # Model Settings
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    REPO_CLONE_DIR: Path = Path(os.getenv("REPO_CLONE_DIR", PROJECT_ROOT / "cloned_repos"))
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", str(PROJECT_ROOT / "chroma_db"))
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", PROJECT_ROOT / "cache"))
    PAPERS_DIR: Path = Path(os.getenv("PAPERS_DIR", PROJECT_ROOT / "papers"))
    CONCEPT_MAPS_DIR: Path = CACHE_DIR / "concept_maps"

    # ChromaDB Cloud (optional - leave empty for local mode)
    CHROMA_CLOUD_API_KEY: Optional[str] = os.getenv("CHROMA_CLOUD_API_KEY")
    CHROMA_CLOUD_HOST: Optional[str] = os.getenv("CHROMA_CLOUD_HOST")  # defaults to api.trychroma.com

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    MAX_CONTEXT_LENGTH: int = 1_000_000  # Gemini 2.0 Flash supports up to 2M

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        errors = []

        # Either API key OR GCP credentials required
        if not cls.GEMINI_API_KEY and not (cls.GCP_PROJECT_ID and cls.GCP_CLIENT_ID and cls.GCP_CLIENT_SECRET):
            errors.append("Either GEMINI_API_KEY or GCP credentials (GCP_PROJECT_ID, GCP_CLIENT_ID, GCP_CLIENT_SECRET) are required")

        return errors

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.REPO_CLONE_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONCEPT_MAPS_DIR.mkdir(parents=True, exist_ok=True)
        # Only create local ChromaDB directory if not using cloud
        if not cls.CHROMA_CLOUD_API_KEY:
            Path(cls.CHROMA_PATH).mkdir(parents=True, exist_ok=True)


# Validate on import
_errors = Config.validate()
if _errors and not os.getenv("SKIP_CONFIG_VALIDATION"):
    import warnings
    for error in _errors:
        warnings.warn(f"Configuration error: {error}")
