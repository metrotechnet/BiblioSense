# Cache pour les réponses GPT - Phase 2 BiblioSense
import json
import hashlib
import time
from collections import OrderedDict
import threading

class GPTCache:
    def __init__(self, max_size=500, ttl_seconds=3600):  # Cache pour 1 heure
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _generate_key(self, query, taxonomy_data):
        """Génère une clé de cache basée sur la requête et la taxonomie"""
        # Créer un hash de la requête et de la structure de taxonomie
        data = {
            "query": query.lower().strip(),
            "taxonomy_hash": hashlib.md5(
                json.dumps(taxonomy_data, sort_keys=True).encode()
            ).hexdigest()
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def get(self, query, taxonomy_data):
        """Récupère une réponse du cache si elle existe et n'est pas expirée"""
        try:
            key = self._generate_key(query, taxonomy_data)
        except Exception as e:
            print(f"⚠️  Cache key generation error: {e}")
            self.cache_misses += 1
            return None
        
        try:
            with self.lock:
                if key in self.cache:
                    cached_data, timestamp = self.cache[key]
                    
                    # Vérifier si le cache n'est pas expiré
                    if time.time() - timestamp < self.ttl_seconds:
                        # Déplacer à la fin (LRU)
                        self.cache.move_to_end(key)
                        self.cache_hits += 1
                        return cached_data
                    else:
                        # Cache expiré, le supprimer
                        del self.cache[key]
                
                self.cache_misses += 1
                return None
        except Exception as e:
            print(f"⚠️  Cache get error: {e}")
            self.cache_misses += 1
            return None
    
    def set(self, query, taxonomy_data, response):
        """Stocke une réponse dans le cache"""
        try:
            key = self._generate_key(query, taxonomy_data)
        except Exception as e:
            print(f"⚠️  Cache key generation error in set: {e}")
            return False
        
        try:
            with self.lock:
                # Si le cache est plein, supprimer le plus ancien
                if len(self.cache) >= self.max_size:
                    # Supprimer le plus ancien (FIFO)
                    self.cache.popitem(last=False)
                
                self.cache[key] = (response, time.time())
                return True
        except Exception as e:
            print(f"⚠️  Cache set error: {e}")
            return False
    
    def clear_expired(self):
        """Nettoie les entrées expirées du cache (thread-safe)"""
        with self.lock:
            return self.clear_expired_unsafe()
    
    def clear_expired_unsafe(self):
        """Nettoie les entrées expirées du cache (non thread-safe, appeler dans un lock)"""
        current_time = time.time()
        expired_keys = []
        
        try:
            for key, (_, timestamp) in self.cache.items():
                if current_time - timestamp >= self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                
        except Exception as e:
            # En mode debug, ignorer les erreurs de nettoyage
            print(f"⚠️  Cache cleanup warning: {e}")
            
        return len(expired_keys)
    
    def get_stats_fast(self):
        """Version rapide des stats sans nettoyage (pour le développement)"""
        with self.lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate_percent": hit_rate,
                "expired_cleaned": 0,  # Pas de nettoyage en mode rapide
                "debug_mode": True
            }
    
    def get_stats(self, cleanup_expired=False):
        """
        Retourne les statistiques du cache
        cleanup_expired: Si True, nettoie les entrées expirées (peut être lent)
        """
        with self.lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            # Nettoyage optionnel (éviter en mode debug/développement)
            expired_count = 0
            if cleanup_expired:
                try:
                    expired_count = self.clear_expired_unsafe()  # Version sans lock
                except Exception:
                    expired_count = 0  # Ignore errors in debug mode
            
            return {
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate_percent": hit_rate,
                "expired_cleaned": expired_count
            }
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        with self.lock:
            self.cache_hits = 0
            self.cache_misses = 0
