# Configuration pour la Phase 2 - BiblioSense
import json
import os
from google.cloud import secretmanager

class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'biblio-sense-phase2-prod')
    
    # Phase 2: Configuration de performance
    MAX_CONCURRENT_USERS = int(os.environ.get('MAX_CONCURRENT_USERS', 200))
    MEMORY_LIMIT_PERCENT = int(os.environ.get('MEMORY_LIMIT_PERCENT', 85))
    CPU_LIMIT_PERCENT = int(os.environ.get('CPU_LIMIT_PERCENT', 90))
    MAX_RESPONSE_TIME = int(os.environ.get('MAX_RESPONSE_TIME', 10))
    
    # Configuration du cache GPT
    GPT_CACHE_SIZE = int(os.environ.get('GPT_CACHE_SIZE', 500))
    GPT_CACHE_TTL = int(os.environ.get('GPT_CACHE_TTL', 3600))  # 1 heure
    
    # Configuration du nettoyage des sessions
    SESSION_CLEANUP_INTERVAL = int(os.environ.get('SESSION_CLEANUP_INTERVAL', 300))  # 5 minutes
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 1800))  # 30 minutes
    
    # Configuration OpenAI
    DEFAULT_SECRET_ID = "openai-api-key"
    DEFAULT_CREDENTIALS_PATH = "../bibliosense-467520-789ce439ce99.json"
    PROJECT_ID = "bibliosense-467520"
    
    # Configuration des bases de données
    BOOK_DATABASE_FILE = "dbase/book_dbase.json"
    TAXONOMY_FILE = "dbase/classification_books.json"

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    MAX_CONCURRENT_USERS = 50
    GPT_CACHE_SIZE = 100
    SESSION_CLEANUP_INTERVAL = 60  # 1 minute pour les tests

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    MAX_CONCURRENT_USERS = 500
    GPT_CACHE_SIZE = 1000
    MEMORY_LIMIT_PERCENT = 80  # Plus conservateur en production
    CPU_LIMIT_PERCENT = 85

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    MAX_CONCURRENT_USERS = 10
    GPT_CACHE_SIZE = 50
    SESSION_CLEANUP_INTERVAL = 30

# Sélection de la configuration basée sur l'environnement
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retourne la configuration appropriée selon l'environnement"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])

def get_secret(secret_name, project_id=None):
    """
    Récupère un secret depuis Google Secret Manager
    
    Args:
        secret_name (str): Nom du secret dans Secret Manager
        project_id (str): ID du projet GCP (optionnel, utilisera le projet par défaut si non spécifié)
    
    Returns:
        str: Valeur du secret
    """
    try:
        # Créer le client Secret Manager
        client = secretmanager.SecretManagerServiceClient()

        if not project_id:
            project_id = "BiblioSense"  # Nom de projet GCP valide (minuscules)

        # Construire le nom de la ressource du secret
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        # Récupérer le secret
        response = client.access_secret_version(request={"name": name})
        
        # Décoder et retourner la valeur
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)['OPENAI_API_KEY']

    except Exception as e:
        print(f"⚠️  Erreur lors de la récupération du secret '{secret_name}': {e}")
        print(f"🔄 Fallback vers les variables d'environnement...")
        return os.getenv(secret_name.upper().replace('-', '_'))

