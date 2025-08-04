# Nettoyage automatique des sessions - Phase 2 BiblioSense
import threading
import time
import json
import os
from datetime import datetime, timedelta

class SessionCleanup:
    def __init__(self, cleanup_interval=300, session_timeout=1800):  # 5 min interval, 30 min timeout
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout
        self.is_running = False
        self.cleanup_thread = None
        self.session_storage_file = "dbase/sessions.json"
        
        # Assurer que le dossier existe
        os.makedirs(os.path.dirname(self.session_storage_file), exist_ok=True)
        
    def start_cleanup(self, user_filtered_books):
        """Démarre le nettoyage automatique des sessions"""
        if self.is_running:
            return
            
        self.is_running = True
        self.user_filtered_books = user_filtered_books
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        print("🧹 Session cleanup started")
    
    def stop_cleanup(self):
        """Arrête le nettoyage automatique"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        print("🛑 Session cleanup stopped")
    
    def _cleanup_loop(self):
        """Boucle de nettoyage en arrière-plan"""
        while self.is_running:
            try:
                cleaned_count = self.cleanup_expired_sessions()
                if cleaned_count > 0:
                    print(f"🧹 Cleaned {cleaned_count} expired sessions")
                
                # Sauvegarder les sessions actives
                self.save_active_sessions()
                
            except Exception as e:
                print(f"❌ Error in session cleanup: {e}")
            
            # Attendre avant le prochain nettoyage
            time.sleep(self.cleanup_interval)
    
    def cleanup_expired_sessions(self):
        """Nettoie les sessions expirées"""
        if not hasattr(self, 'user_filtered_books'):
            return 0
            
        current_time = time.time()
        expired_sessions = []
        
        # Charger les timestamps des sessions
        session_timestamps = self.load_session_timestamps()
        
        for user_id in list(self.user_filtered_books.keys()):
            last_activity = session_timestamps.get(user_id, current_time)
            
            if current_time - last_activity > self.session_timeout:
                expired_sessions.append(user_id)
        
        # Supprimer les sessions expirées
        for user_id in expired_sessions:
            self.user_filtered_books.pop(user_id, None)
            session_timestamps.pop(user_id, None)
        
        # Sauvegarder les timestamps mis à jour
        if expired_sessions:
            self.save_session_timestamps(session_timestamps)
        
        return len(expired_sessions)
    
    def update_session_activity(self, user_id):
        """Met à jour l'activité d'une session"""
        session_timestamps = self.load_session_timestamps()
        session_timestamps[user_id] = time.time()
        self.save_session_timestamps(session_timestamps)
    
    def load_session_timestamps(self):
        """Charge les timestamps des sessions depuis le fichier"""
        try:
            if os.path.exists(self.session_storage_file):
                with open(self.session_storage_file, 'r') as f:
                    data = json.load(f)
                    return data.get('session_timestamps', {})
        except Exception as e:
            print(f"⚠️  Error loading session timestamps: {e}")
        
        return {}
    
    def save_session_timestamps(self, session_timestamps):
        """Sauvegarde les timestamps des sessions"""
        try:
            data = {
                'session_timestamps': session_timestamps,
                'last_updated': time.time()
            }
            with open(self.session_storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving session timestamps: {e}")
    
    def save_active_sessions(self):
        """Sauvegarde périodique des sessions actives (pour la persistance)"""
        if not hasattr(self, 'user_filtered_books'):
            return
            
        try:
            # Ne sauvegarder que les métadonnées des sessions (pas les données complètes)
            session_metadata = {}
            for user_id, filtered_books in self.user_filtered_books.items():
                if filtered_books:
                    session_metadata[user_id] = {
                        'book_count': len(filtered_books),
                        'last_updated': time.time()
                    }
            
            backup_data = {
                'active_sessions': session_metadata,
                'total_sessions': len(self.user_filtered_books),
                'backup_time': time.time()
            }
            
            backup_file = self.session_storage_file.replace('.json', '_backup.json')
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error saving session backup: {e}")
    
    def get_cleanup_stats(self):
        """Retourne les statistiques de nettoyage"""
        session_timestamps = self.load_session_timestamps()
        current_time = time.time()
        
        active_sessions = 0
        old_sessions = 0
        
        for user_id, timestamp in session_timestamps.items():
            if current_time - timestamp <= self.session_timeout:
                active_sessions += 1
            else:
                old_sessions += 1
        
        return {
            "cleanup_running": self.is_running,
            "active_sessions": active_sessions,
            "old_sessions": old_sessions,
            "cleanup_interval": self.cleanup_interval,
            "session_timeout": self.session_timeout
        }
