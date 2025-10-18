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
    VECTARA_CUSTOMER_ID: str = os.getenv("VECTARA_CUSTOMER_ID", "")
    VECTARA_API_KEY: str = os.getenv("VECTARA_API_KEY", "")
    VECTARA_CORPUS_ID: str = os.getenv("VECTARA_CORPUS_ID", "")
    FETCHAI_AGENT_SEED: str = os.getenv("FETCHAI_AGENT_SEED", "")
    FETCHAI_AGENT_MAILBOX_KEY: str = os.getenv("FETCHAI_AGENT_MAILBOX_KEY", "")
    OPENALEX_EMAIL: Optional[str] = os.getenv("OPENALEX_EMAIL")

    # Model Settings
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    REPO_CLONE_DIR: Path = Path(os.getenv("REPO_CLONE_DIR", PROJECT_ROOT / "cloned_repos"))

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    MAX_CONTEXT_LENGTH: int = 1_000_000  # Gemini 2.0 Flash supports up to 2M

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        if not cls.VECTARA_CUSTOMER_ID:
            errors.append("VECTARA_CUSTOMER_ID is required")
        if not cls.VECTARA_API_KEY:
            errors.append("VECTARA_API_KEY is required")
        if not cls.VECTARA_CORPUS_ID:
            errors.append("VECTARA_CORPUS_ID is required")

        return errors

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.REPO_CLONE_DIR.mkdir(parents=True, exist_ok=True)


# Validate on import
_errors = Config.validate()
if _errors and not os.getenv("SKIP_CONFIG_VALIDATION"):
    import warnings
    for error in _errors:
        warnings.warn(f"Configuration error: {error}")
