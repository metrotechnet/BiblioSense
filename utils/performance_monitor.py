# Monitoring des performances pour BiblioSense
import psutil
import time
from collections import defaultdict, deque
import threading
import json

class PerformanceMonitor:
    def __init__(self, max_users=200, memory_limit=85, cpu_limit=90, response_time_limit=10):
        self.request_count = defaultdict(int)
        self.response_times = deque(maxlen=1000)  # Plus efficace que la liste
        self.active_users = set()
        self.user_last_activity = {}
        self.lock = threading.Lock()
        
        # Configuration des limites (Phase 2)
        self.max_users = max_users
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.response_time_limit = response_time_limit
        
        # Initialize CPU measurement to avoid first-call blocking
        self._init_cpu_monitoring()
        
    def _init_cpu_monitoring(self):
        """Initialize CPU monitoring to prevent blocking on first call"""
        try:
            # Premier appel pour initialiser psutil (peut être lent)
            psutil.cpu_percent(interval=0.1)
        except Exception as e:
            print(f"⚠️  CPU monitoring initialization warning: {e}")
            # Continuer même si l'initialisation échoue
        
    def track_request(self, user_id, response_time):
        with self.lock:
            self.request_count[user_id] += 1
            self.response_times.append(response_time)
            self.active_users.add(user_id)
            self.user_last_activity[user_id] = time.time()
    
    def cleanup_inactive_users(self, timeout_seconds=300):  # 5 minutes
        """Nettoie les utilisateurs inactifs"""
        current_time = time.time()
        with self.lock:
            inactive_users = [
                user_id for user_id, last_activity in self.user_last_activity.items()
                if current_time - last_activity > timeout_seconds
            ]
            
            for user_id in inactive_users:
                self.active_users.discard(user_id)
                self.user_last_activity.pop(user_id, None)
                
        return len(inactive_users)
    
    def get_stats_safe(self):
        """Version simplifiée pour le développement/debug qui ne bloque pas"""
        with self.lock:
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0
            )
            
            return {
                "active_users": len(self.active_users),
                "total_requests": sum(self.request_count.values()),
                "avg_response_time": avg_response_time,
                "memory_usage_percent": 0.0,  # Placeholder en mode debug
                "memory_used_gb": 0.0,
                "cpu_usage_percent": 0.0,
                "sessions_in_memory": len(self.user_last_activity),
                "debug_mode": True
            }
    
    def get_stats(self, safe_mode=False):
        """
        Get performance stats with optional safe mode for debugging
        safe_mode=True évite les appels psutil qui peuvent bloquer
        """
        if safe_mode:
            return self.get_stats_safe()
            
        try:
            memory = psutil.virtual_memory()
        except Exception as e:
            print(f"⚠️  Memory measurement error: {e}")
            return self.get_stats_safe()
        
        # Fix for debugger blocking: use non-blocking CPU measurement
        try:
            # interval=None pour mesure non-bloquante (instantanée)
            cpu = psutil.cpu_percent(interval=None)
            # Si on obtient 0.0, c'est probablement que psutil n'est pas encore initialisé
            if cpu == 0.0:
                # Essayer une mesure très rapide
                cpu = psutil.cpu_percent(interval=0.01)
        except Exception as e:
            # Fallback si psutil pose problème en mode debug
            print(f"⚠️  CPU measurement fallback: {e}")
            cpu = 0.0
        
        with self.lock:
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0
            )
            
            # Nettoyer les utilisateurs inactifs (seulement si pas en mode debug)
            try:
                self.cleanup_inactive_users()
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
            
            return {
                "active_users": len(self.active_users),
                "total_requests": sum(self.request_count.values()),
                "avg_response_time": avg_response_time,
                "memory_usage_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "cpu_usage_percent": cpu,
                "sessions_in_memory": len(self.user_last_activity)
            }
    
    def should_throttle(self, safe_mode=True):
        """
        Check if system should throttle requests
        safe_mode=True pour éviter les blocages en mode debug
        """
        stats = self.get_stats(safe_mode=safe_mode)
        
        # En mode debug, on throttle seulement sur les utilisateurs actifs
        if stats.get("debug_mode", False):
            if stats["active_users"] > self.max_users:
                return True, "Too many concurrent users"
            return False, ""
        
        # Seuils de throttling configurables (mode normal)
        if stats["memory_usage_percent"] > self.memory_limit:
            return True, "High memory usage"
        if stats["cpu_usage_percent"] > self.cpu_limit:
            return True, "High CPU usage"
        if stats["avg_response_time"] > self.response_time_limit:
            return True, "High response time"
        if stats["active_users"] > self.max_users:
            return True, "Too many concurrent users"
            
        return False, ""
    
    def get_performance_report(self, safe_mode=False):
        """
        Génère un rapport détaillé des performances
        safe_mode=True pour éviter les blocages en mode debug
        """
        stats = self.get_stats(safe_mode=safe_mode)
        throttle_needed, throttle_reason = self.should_throttle(safe_mode=safe_mode)
        
        return {
            **stats,
            "throttle_needed": throttle_needed,
            "throttle_reason": throttle_reason,
            "status": "overloaded" if throttle_needed else "healthy",
            "timestamp": time.time()
        }
