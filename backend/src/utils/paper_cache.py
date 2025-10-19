"""
Paper caching system for Repo Rover
Stores paper metadata, repo URLs, concept maps to avoid redundant API calls
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from .config import Config

logger = logging.getLogger(__name__)


class PaperCache:
    """Manages persistent cache for paper metadata and analysis results"""

    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize PaperCache

        Args:
            cache_file: Path to cache JSON file (defaults to Config.CACHE_DIR/papers.json)
        """
        self.cache_file = cache_file or (Config.CACHE_DIR / "papers.json")
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self):
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded cache with {len(self.cache)} papers")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}
            logger.info("No existing cache found, starting fresh")

    def _save_cache(self):
        """Save cache to disk"""
        try:
            Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved cache with {len(self.cache)} papers")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached paper data

        Args:
            arxiv_id: ArXiv ID (e.g., "1706.03762")

        Returns:
            Cached paper data or None if not found
        """
        # Normalize arxiv_id (remove version suffix if present)
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id

        if normalized_id in self.cache:
            # Update last accessed time
            self.cache[normalized_id]["last_accessed"] = datetime.now(timezone.utc).isoformat()
            self.cache[normalized_id]["access_count"] = self.cache[normalized_id].get("access_count", 0) + 1
            self._save_cache()
            logger.info(f"Cache HIT for {normalized_id}")
            return self.cache[normalized_id]

        logger.info(f"Cache MISS for {normalized_id}")
        return None

    def set(self, arxiv_id: str, data: Dict[str, Any]):
        """
        Store paper data in cache

        Args:
            arxiv_id: ArXiv ID
            data: Paper metadata and analysis results
        """
        # Normalize arxiv_id
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id

        # Add timestamps
        now = datetime.now(timezone.utc).isoformat()
        data["last_accessed"] = now
        data["access_count"] = data.get("access_count", 0) + 1

        if normalized_id not in self.cache:
            data["created_at"] = now

        self.cache[normalized_id] = data
        self._save_cache()
        logger.info(f"Cached data for {normalized_id}")

    def update(self, arxiv_id: str, updates: Dict[str, Any]):
        """
        Update specific fields in cached paper data

        Args:
            arxiv_id: ArXiv ID
            updates: Dictionary of fields to update
        """
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id

        if normalized_id in self.cache:
            self.cache[normalized_id].update(updates)
            self.cache[normalized_id]["last_accessed"] = datetime.now(timezone.utc).isoformat()
            self._save_cache()
            logger.info(f"Updated cache for {normalized_id}")
        else:
            logger.warning(f"Cannot update non-existent cache entry: {normalized_id}")

    def delete(self, arxiv_id: str) -> bool:
        """
        Delete cached paper data

        Args:
            arxiv_id: ArXiv ID

        Returns:
            True if deleted, False if not found
        """
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id

        if normalized_id in self.cache:
            del self.cache[normalized_id]
            self._save_cache()
            logger.info(f"Deleted cache for {normalized_id}")
            return True

        return False

    def exists(self, arxiv_id: str) -> bool:
        """
        Check if paper exists in cache

        Args:
            arxiv_id: ArXiv ID

        Returns:
            True if cached, False otherwise
        """
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        return normalized_id in self.cache

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total_papers = len(self.cache)
        total_accesses = sum(p.get("access_count", 0) for p in self.cache.values())

        # Calculate total cache size
        total_size = 0
        if self.cache_file.exists():
            total_size = self.cache_file.stat().st_size

        # Add concept map sizes
        for paper in self.cache.values():
            if "concept_map_path" in paper:
                map_path = Path(paper["concept_map_path"])
                if map_path.exists():
                    total_size += map_path.stat().st_size

        return {
            "total_papers": total_papers,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_accesses": total_accesses,
            "papers": [
                {
                    "arxiv_id": arxiv_id,
                    "title": data.get("title", ""),
                    "access_count": data.get("access_count", 0),
                    "last_accessed": data.get("last_accessed", ""),
                    "has_repo": "repo_url" in data,
                    "has_concept_map": "concept_map_path" in data,
                    "has_chroma": "chroma_collection" in data,
                }
                for arxiv_id, data in self.cache.items()
            ]
        }

    def clear_all(self):
        """Clear entire cache"""
        self.cache = {}
        self._save_cache()
        logger.warning("Cleared entire cache")

    def save_concept_map(self, arxiv_id: str, concept_map: Dict[str, Any]) -> Path:
        """
        Save concept map to separate file

        Args:
            arxiv_id: ArXiv ID
            concept_map: Concept map data

        Returns:
            Path to saved concept map file
        """
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        map_path = Config.CONCEPT_MAPS_DIR / f"{normalized_id}.json"

        try:
            Config.CONCEPT_MAPS_DIR.mkdir(parents=True, exist_ok=True)
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(concept_map, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved concept map for {normalized_id}")
            return map_path
        except Exception as e:
            logger.error(f"Failed to save concept map: {e}")
            raise

    def load_concept_map(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Load concept map from file

        Args:
            arxiv_id: ArXiv ID

        Returns:
            Concept map data or None if not found
        """
        normalized_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        map_path = Config.CONCEPT_MAPS_DIR / f"{normalized_id}.json"

        if map_path.exists():
            try:
                with open(map_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load concept map: {e}")
                return None

        return None


# Global cache instance
_cache_instance: Optional[PaperCache] = None


def get_cache() -> PaperCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PaperCache()
    return _cache_instance
