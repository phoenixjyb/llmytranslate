"""
Enhanced Caching Service with Compression and Smart Invalidation
"""

import asyncio
import hashlib
import json
import time
import gzip
import base64
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    translation: str
    from_lang: str
    to_lang: str
    model: str
    timestamp: float
    access_count: int = 0
    last_accessed: Optional[float] = None
    compressed: bool = False
    size_bytes: int = 0

class EnhancedCacheService:
    """
    High-performance caching service with:
    - LRU eviction policy
    - Compression for large entries
    - Smart cache key generation
    - Performance metrics
    - Persistent storage option
    """
    
    def __init__(self, 
                 max_entries: int = 10000,
                 max_memory_mb: int = 100,
                 compression_threshold: int = 500,
                 ttl_hours: int = 24,
                 persist_to_disk: bool = True):
        
        self.max_entries = max_entries
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.compression_threshold = compression_threshold
        self.ttl_seconds = ttl_hours * 3600
        self.persist_to_disk = persist_to_disk
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU tracking
        self._current_memory_usage = 0
        
        # Performance tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "decompressions": 0,
            "total_saved_time": 0.0
        }
        
        # Initialization flag
        self._loaded_from_disk = False
        
        # Disk persistence
        self.cache_file = Path("cache/translation_cache.json.gz")
        if self.persist_to_disk:
            self.cache_file.parent.mkdir(exist_ok=True)
            # Don't load from disk immediately - do it on first use
    
    def _generate_cache_key(self, text: str, from_lang: str, to_lang: str, model: str, translation_mode: str = "succinct") -> str:
        """Generate a unique cache key for the translation request."""
        # Normalize text for better cache hits
        normalized_text = text.strip().lower()
        
        # Create key components
        key_data = {
            "text": normalized_text,
            "from": from_lang.lower(),
            "to": to_lang.lower(),
            "model": model.lower(),
            "mode": translation_mode.lower()
        }
        
        # Generate hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _compress_data(self, data: str) -> tuple[str, bool]:
        """Compress data if it's large enough."""
        if len(data) < self.compression_threshold:
            return data, False
        
        try:
            compressed = gzip.compress(data.encode('utf-8'))
            compressed_b64 = base64.b64encode(compressed).decode('ascii')
            
            # Only use compression if it actually saves space
            if len(compressed_b64) < len(data):
                self.stats["compressions"] += 1
                return compressed_b64, True
            else:
                return data, False
                
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return data, False
    
    def _decompress_data(self, data: str, is_compressed: bool) -> str:
        """Decompress data if needed."""
        if not is_compressed:
            return data
        
        try:
            compressed = base64.b64decode(data.encode('ascii'))
            decompressed = gzip.decompress(compressed).decode('utf-8')
            self.stats["decompressions"] += 1
            return decompressed
            
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return data  # Return as-is if decompression fails
    
    def _update_access_order(self, key: str):
        """Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_lru_entries(self):
        """Evict least recently used entries to free memory."""
        while (len(self._cache) > self.max_entries or 
               self._current_memory_usage > self.max_memory_bytes):
            
            if not self._access_order:
                break
                
            # Remove oldest entry
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                entry = self._cache[oldest_key]
                self._current_memory_usage -= entry.size_bytes
                del self._cache[oldest_key]
                self.stats["evictions"] += 1
                
                logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        return (time.time() - entry.timestamp) > self.ttl_seconds
    
    async def get_translation(self, 
                            text: str, 
                            from_lang: str, 
                            to_lang: str, 
                            model: str,
                            translation_mode: str = "succinct") -> Optional[Dict[str, Any]]:
        """Get cached translation if available."""
        # Load from disk on first use
        if not self._loaded_from_disk and self.persist_to_disk:
            await self._load_from_disk()
            self._loaded_from_disk = True
            
        cache_key = self._generate_cache_key(text, from_lang, to_lang, model, translation_mode)
        
        if cache_key not in self._cache:
            self.stats["misses"] += 1
            return None
        
        entry = self._cache[cache_key]
        
        # Check if expired
        if self._is_expired(entry):
            del self._cache[cache_key]
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self.stats["misses"] += 1
            return None
        
        # Update access info
        entry.access_count += 1
        entry.last_accessed = time.time()
        self._update_access_order(cache_key)
        
        # Decompress if needed
        translation = self._decompress_data(entry.translation, entry.compressed)
        
        self.stats["hits"] += 1
        
        # Estimate saved time (assume 5 seconds average for LLM call)
        self.stats["total_saved_time"] += 5.0
        
        logger.debug(f"Cache hit for key: {cache_key}")
        
        return {
            "translation": translation,
            "cached": True,
            "cache_timestamp": entry.timestamp,
            "access_count": entry.access_count
        }
    
    async def store_translation(self, 
                              text: str, 
                              from_lang: str, 
                              to_lang: str, 
                              model: str,
                              translation: str,
                              translation_mode: str = "succinct") -> bool:
        """Store translation in cache."""
        cache_key = self._generate_cache_key(text, from_lang, to_lang, model, translation_mode)
        
        # Compress if needed
        stored_translation, is_compressed = self._compress_data(translation)
        
        # Calculate size
        entry_size = len(stored_translation) + len(text) + 200  # Rough estimate
        
        # Create cache entry
        entry = CacheEntry(
            translation=stored_translation,
            from_lang=from_lang,
            to_lang=to_lang,
            model=model,
            timestamp=time.time(),
            access_count=0,
            last_accessed=time.time(),
            compressed=is_compressed,
            size_bytes=entry_size
        )
        
        # Store in cache
        self._cache[cache_key] = entry
        self._current_memory_usage += entry_size
        self._update_access_order(cache_key)
        
        # Evict if necessary
        self._evict_lru_entries()
        
        logger.debug(f"Cached translation for key: {cache_key}")
        
        # Persist to disk periodically
        if self.persist_to_disk and len(self._cache) % 100 == 0:
            asyncio.create_task(self._save_to_disk())
        
        return True
    
    async def _save_to_disk(self):
        """Save cache to disk for persistence."""
        if not self.persist_to_disk:
            return
        
        try:
            # Convert cache to serializable format
            cache_data = {
                key: asdict(entry) for key, entry in self._cache.items()
            }
            
            # Compress and save
            json_data = json.dumps(cache_data, ensure_ascii=False)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            with open(self.cache_file, 'wb') as f:
                f.write(compressed_data)
                
            logger.info(f"Cache saved to disk: {len(self._cache)} entries")
            
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")
    
    async def _load_from_disk(self):
        """Load cache from disk."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'rb') as f:
                compressed_data = f.read()
            
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            cache_data = json.loads(json_data)
            
            # Reconstruct cache entries
            current_time = time.time()
            loaded_count = 0
            
            for key, entry_dict in cache_data.items():
                entry = CacheEntry(**entry_dict)
                
                # Skip expired entries
                if self._is_expired(entry):
                    continue
                
                self._cache[key] = entry
                self._current_memory_usage += entry.size_bytes
                self._access_order.append(key)
                loaded_count += 1
            
            logger.info(f"Cache loaded from disk: {loaded_count} entries")
            
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self._cache),
            "memory_usage_mb": round(self._current_memory_usage / (1024 * 1024), 2),
            "memory_usage_percent": round((self._current_memory_usage / self.max_memory_bytes) * 100, 1),
            "hit_rate_percent": round(hit_rate, 1),
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "total_evictions": self.stats["evictions"],
            "total_compressions": self.stats["compressions"],
            "total_decompressions": self.stats["decompressions"],
            "total_saved_time_seconds": round(self.stats["total_saved_time"], 1),
            "compression_ratio": f"{self.stats['compressions']}/{len(self._cache)}" if len(self._cache) > 0 else "0/0"
        }
    
    async def clear_cache(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()
        self._current_memory_usage = 0
        logger.info("Cache cleared")
    
    async def cleanup(self):
        """Cleanup resources and save to disk."""
        if self.persist_to_disk:
            await self._save_to_disk()

# Global enhanced cache instance
enhanced_cache_service = EnhancedCacheService()
