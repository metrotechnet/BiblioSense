from flask import Flask, jsonify, render_template, request, session
import pandas as pd
from openai import OpenAI
import json
from waitress import serve
import os
import time
import uuid
from utils.gpt_services import get_catagories_with_gpt, get_catagories_with_gpt_cached, create_cached_gpt_function
from utils.text_matching import smart_keyword_match
from utils.performance_monitor import PerformanceMonitor
from utils.gpt_cache import GPTCache
from utils.session_cleanup import SessionCleanup
from utils.config import get_config, get_secret

# -------------------- Global Data Storage --------------------

# Get configuration based on environment
app_config = get_config()

# Global variables to store loaded data
taxonomy_data = None
books_data = None
# Dictionary to store filtered results per session
user_filtered_books = {}
openai_client = None
cached_gpt_classifier = None  # Pre-configured cached GPT function

# Initialize performance monitoring and optimization tools
performance_monitor = PerformanceMonitor(
    max_users=app_config.MAX_CONCURRENT_USERS,
    memory_limit=app_config.MEMORY_LIMIT_PERCENT,
    cpu_limit=app_config.CPU_LIMIT_PERCENT,
    response_time_limit=app_config.MAX_RESPONSE_TIME
)
gpt_cache = GPTCache(
    max_size=app_config.GPT_CACHE_SIZE,
    ttl_seconds=app_config.GPT_CACHE_TTL
)
session_cleanup = None

# -------------------- Configuration --------------------

# Get configuration based on environment
app_config = get_config()

# Paths to JSON files for taxonomy and book data
BOOK_DATABASE_FILE = app_config.BOOK_DATABASE_FILE
TAXONOMY_FILE = app_config.TAXONOMY_FILE

# Configuration de base
DEFAULT_SECRET_ID = app_config.DEFAULT_SECRET_ID
DEFAULT_CREDENTIALS_PATH = app_config.DEFAULT_CREDENTIALS_PATH
PROJECT_ID = app_config.PROJECT_ID

# -------------------- Initialization Functions --------------------

def init_data():
    """
    Initialize and load taxonomy and book data from JSON files.
    This function should be called once at application startup.
    """
    global taxonomy_data, books_data
    
    try:
        # Load taxonomy data
        with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
            taxonomy_data = json.load(f)
        print(f"✅ Taxonomy data loaded from {TAXONOMY_FILE}")
        
        # Load book data
        with open(BOOK_DATABASE_FILE, "r", encoding="utf-8") as f:
            books_data = json.load(f)
        print(f"✅ Book data loaded from {BOOK_DATABASE_FILE} ({len(books_data)} books)")
        # reorder book by alphabetical order of title
        # books_data.sort(key=lambda x: x.get("titre", "").lower())

        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

def init_openai_client():
    """
    Initialize OpenAI client with API key from Secret Manager or environment variables.
    """
    global openai_client
    
    # Si exécuté en local, charger les credentials depuis un fichier
    project_id = PROJECT_ID
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS_PATH
        try:
            with open(DEFAULT_CREDENTIALS_PATH, 'r') as f:
                credentials = json.load(f)
            project_id = credentials['project_id']
        except Exception as e:
            print(f"⚠️  Error loading credentials file: {e}")

    # Essayer Secret Manager seulement si pas de variable d'environnement
    try:
        OPENAI_API_KEY = get_secret(DEFAULT_SECRET_ID, project_id=project_id)
        if OPENAI_API_KEY:
            print("✅ Clé OpenAI récupérée depuis Secret Manager")
        else:
            raise ValueError("OPENAI_API_KEY non trouvée")
    except Exception as e:
        print(f"Erreur Secret Manager: {str(e)[:100]}...")
        raise ValueError("OPENAI_API_KEY n'est pas définie (ni dans .env ni dans Secret Manager)")

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized")

# -------------------- Flask Application Factory --------------------

def create_app():
    """
    Application factory pattern for Flask app creation.
    """
    global session_cleanup
    
    app = Flask(__name__)
    
    # Configure session
    app.secret_key = os.environ.get('SECRET_KEY', 'biblio-sense-1234')
    
    # Initialize data and services
    init_data()
    init_openai_client()
    
    # Initialize session cleanup for Phase 2 optimization
    session_cleanup = SessionCleanup(
        cleanup_interval=app_config.SESSION_CLEANUP_INTERVAL,
        session_timeout=app_config.SESSION_TIMEOUT
    )
    session_cleanup.start_cleanup(user_filtered_books)
    
    # Create pre-configured cached GPT function
    global cached_gpt_classifier
    cached_gpt_classifier = create_cached_gpt_function(gpt_cache, openai_client, taxonomy_data)
    
    print("✅ Phase 2 optimizations initialized: Performance monitoring, GPT caching, Session cleanup")
    
    # -------------------- Flask Routes --------------------

    @app.route("/")
    def index():
        """
        Render the main graph visualization page.
        """
        # Ensure user has a session from the very first page load
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            print(f"🆔 New session created: {session['user_id']}")
        else:
            print(f"🔄 Existing session: {session['user_id']}")
            
        return render_template("index.html")
    
    # create a service that returns the number of books
    @app.route("/count_books")
    def count_books():
        """
        Return the total number of books in the database.
        """
        global books_data
        return jsonify({"count": len(books_data)})  # Return the total book count

    @app.route("/session_info")
    def session_info():
        """
        Return session information for debugging/monitoring with Phase 2 enhancements.
        """
        global user_filtered_books, performance_monitor, gpt_cache
        
        # Session should already exist from index route, but safety check
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            print(f"⚠️  Session created in session_info (unexpected): {session['user_id']}")
        
        user_id = session['user_id']
        
        # Update session activity for cleanup tracking
        if session_cleanup:
            session_cleanup.update_session_activity(user_id)
        
        # Get performance stats (use safe mode for debugging)
        perf_stats = performance_monitor.get_stats(safe_mode=True)
        cache_stats = gpt_cache.get_stats_fast()  # Version rapide pour éviter les blocages
        cleanup_stats = session_cleanup.get_cleanup_stats() if session_cleanup else {}
        
        return jsonify({
            "user_id": user_id,
            "active_sessions": len(user_filtered_books),
            "has_filtered_results": user_id in user_filtered_books and user_filtered_books[user_id] is not None,
            "filtered_count": len(user_filtered_books[user_id]) if user_id in user_filtered_books and user_filtered_books[user_id] else 0,
            # Phase 2 monitoring data
            "performance": perf_stats,
            "cache": cache_stats,
            "cleanup": cleanup_stats
        })

    @app.route("/books")
    @app.route("/books/<int:index>")
    @app.route("/books/<int:start>/<int:end>")
    def books_data_route(index=None, start=None, end=None):
        """
        Return the book graph data (nodes and edges) as JSON for the frontend.
        
        Routes:
        - /books: Return all books
        - /books/<index>: Return a specific book by index
        - /books/<start>/<end>: Return books from start to end index (inclusive)
        
        Query Parameters:
        - source: 'all' (default) for books_data or 'filtered' for filtered_books
        """
        global books_data, user_filtered_books
        
        # Session should already exist from index route, but safety check
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            print(f"⚠️  Session created in books_data_route (unexpected): {session['user_id']}")
        
        user_id = session['user_id']
        
        # Update session activity for Phase 2 tracking
        if session_cleanup:
            session_cleanup.update_session_activity(user_id)
        
        # Get source parameter (default to 'all')
        source = request.args.get('source', 'all').lower()
        
        # Select the appropriate data source
        if source == 'filtered':
            if user_id not in user_filtered_books or user_filtered_books[user_id] is None:
                return {"error": "No filtered results available. Please perform a search first."}, 400
            current_books = user_filtered_books[user_id]
            source_name = "filtered books"
        else:
            current_books = books_data
            source_name = "all books"
        
        # Return specific book by index
        if index is not None:
            if 0 <= index < len(current_books):
                return {
                    "book": current_books[index], 
                    "index": index,
                    "source": source,
                    "total_count": len(current_books),
                    "user_id": user_id
                }
            else:
                return {"error": f"Index {index} out of range for {source_name}. Valid range: 0-{len(current_books)-1}"}, 404
        
        # Return range of books
        if start is not None and end is not None:
            # if start < 0 or end >= len(current_books) or start > end:
            #     return {"error": f"Invalid range [{start}:{end}] for {source_name}. Valid range: 0-{len(current_books)-1}"}, 400
            # end = min(end, len(current_books) - 1)  # Ensure end is within bounds
            return {
                "book_list": current_books[start:end+1], 
                "range": {"start": start, "end": end, "count": end - start + 1},
                "source": source,
                "total_count": len(current_books),
                "user_id": user_id
            }
        
        # Return all books (default behavior)
        return {
            "book_list": current_books,
            "source": source,
            "total_count": len(current_books),
            "user_id": user_id
        }

    @app.route("/filter", methods=["POST"])
    def filter_categories():
        """
        Filter books based on a user query using GPT classification.

        Receives JSON with a 'query' field.
        Uses GPT to classify the query into taxonomy categories and keywords.
        Filters books by taxonomy and keywords, scores matches, and returns sorted results with a description.
        """
        # Start timing
        start_time = time.time()
        
        global taxonomy_data, books_data, openai_client, user_filtered_books, performance_monitor, gpt_cache
        
        # Check if system should throttle requests (Phase 2 optimization)
        should_throttle, throttle_reason = performance_monitor.should_throttle()
        if should_throttle:
            return jsonify({
                "error": f"Service temporarily overloaded: {throttle_reason}. Please try again in a few moments.",
                "retry_after": 30
            }), 503
        
        # Session should already exist from index route, but safety check
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            print(f"⚠️  Session created in filter_categories (unexpected): {session['user_id']}")

        user_id = session['user_id']
        data = request.get_json()
        text = data.get("query", "")
        
        # Update session activity for Phase 2 tracking
        if session_cleanup:
            session_cleanup.update_session_activity(user_id)
        
        print(f"🔍 Processing query for user {user_id}: '{text}'")

        try:
            # Phase 2: Use pre-configured cached GPT call (simplest approach)
            gpt_start = time.time()
            categories = cached_gpt_classifier(text)
            total_gpt_time = time.time() - gpt_start
                
            print(f"Categories from GPT: {categories}")
            

            # Book filtering logic with performance optimizations
            filter_start = time.time()
            
            # Pre-compute keyword sets for faster lookups
            keyword_items = list(categories["Mots-clés"].items())
            taxonomy_items = list(categories["Taxonomie"].items())
            title_author_fields = {"titre", "auteur"}
            
            # Pre-process taxonomy lookup sets for faster intersection
            taxonomy_lookup = {}
            for taxo_key, taxo_classes in taxonomy_items:
                taxonomy_lookup[taxo_key] = {}
                for sub_key, sub_values_set in taxo_classes.items():
                    taxonomy_lookup[taxo_key][sub_key] = set(sub_values_set)
            
            # Single pass through books with optimized scoring
            scored_books = []
            for book in books_data:
                # Early exit if no potential matches
                has_keywords = any(book.get(kw_key) for kw_key, _ in keyword_items)
                has_taxonomy = book.get("classification")
                
                if not has_keywords and not has_taxonomy:
                    continue
                
                taxonomy_score = 0
                title_author_score = 0
                other_keyword_score = 0
                
                # Parse book taxonomy once (only if needed)
                book_taxonomy = {}
                if has_taxonomy and taxonomy_items:
                    try:
                        book_taxonomy = json.loads(book["classification"])
                    except (json.JSONDecodeError, TypeError, KeyError):
                        book_taxonomy = {}
                
                # Check taxonomy matches using pre-computed lookup
                if book_taxonomy:
                    for taxo_key, taxo_classes_lookup in taxonomy_lookup.items():
                        book_taxo_section = book_taxonomy.get(taxo_key)
                        if book_taxo_section:
                            for sub_key, sub_values_set in taxo_classes_lookup.items():
                                book_values = book_taxo_section.get(sub_key)
                                if book_values:
                                    if isinstance(book_values, list):
                                        # Use pre-computed sets for faster intersection
                                        matches = sub_values_set.intersection(book_values)
                                        taxonomy_score += len(matches)
                                    elif book_values in sub_values_set:
                                        taxonomy_score += 1
                
                # Check keyword matches with smart matching (only if has keywords)
                if has_keywords:
                    for keyword_key, keyword_values in keyword_items:
                        book_field = book.get(keyword_key)
                        if not book_field:
                            continue
                            
                        is_title_author = keyword_key in title_author_fields
                        
                        # Handle both single keywords (string) and multiple keywords (list)
                        if isinstance(keyword_values, str):
                            # Backward compatibility for single keyword
                            match_score = smart_keyword_match(keyword_values, book_field, keyword_key)
                            if match_score > 0.5:
                                if is_title_author:
                                    title_author_score += match_score
                                else:
                                    other_keyword_score += match_score
                        elif isinstance(keyword_values, list):
                            # New logic for multiple synonymous keywords
                            best_match_score = 0
                            for keyword_variant in keyword_values:
                                match_score = smart_keyword_match(keyword_variant, book_field, keyword_key)
                                if match_score > best_match_score:
                                    best_match_score = match_score
                                # Early exit if perfect match found
                                if best_match_score >= 1.0:
                                    break
                            # Only count the best match to avoid double-counting synonyms
                            if best_match_score > 0.5:
                                if is_title_author:
                                    title_author_score += best_match_score
                                else:
                                    other_keyword_score += best_match_score
                
                # Calculate total score with title/author priority
                total_score = (title_author_score * 100) + (other_keyword_score * 10) + taxonomy_score
                
                # Only add books with positive scores
                if total_score > 0:
                    # Use dict literal instead of copy() for better performance
                    scored_books.append({
                        **book,
                        "score": total_score,
                        "title_author_matches": title_author_score,
                        "other_keyword_matches": other_keyword_score,
                        "taxonomy_matches": taxonomy_score
                    })
            
            # Sort by descending score (title/author matches will be at top due to highest weight)
            filtered_books = sorted(scored_books, key=lambda x: x["score"], reverse=True)
            
            # Store filtered results for this user session
            user_filtered_books[user_id] = filtered_books
            
            filter_time = time.time() - filter_start
            print(f"⏱️  Book filtering: {filter_time:.2f}s")

            # Calculate total time and track performance (Phase 2)
            total_time = time.time() - start_time
            performance_monitor.track_request(user_id, total_time)
            
            print(f"📊 Performance Summary for user {user_id}:")
            print(f"   - Total GPT time: {total_gpt_time:.2f}s ({(total_gpt_time/total_time)*100:.1f}%)")
            print(f"   - Book filtering: {filter_time:.2f}s ({(filter_time/total_time)*100:.1f}%)")
            print(f"   - Total request time: {total_time:.2f}s")
            print(f"   - Books found: {len(filtered_books)}")
            
            # Phase 2: Log cache and performance statistics (safe mode)
            cache_stats = gpt_cache.get_stats_fast()  # Version rapide
            perf_stats = performance_monitor.get_stats(safe_mode=True)  # Mode sécurisé
            print(f"🔄 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}% ({cache_stats['cache_hits']}/{cache_stats['cache_hits'] + cache_stats['cache_misses']})")
            
            # Afficher la mémoire seulement si disponible (pas en mode debug)
            if not perf_stats.get('debug_mode', False):
                print(f"👥 Active users: {perf_stats['active_users']}, Memory: {perf_stats['memory_usage_percent']:.1f}%")
            else:
                print(f"👥 Active users: {perf_stats['active_users']} (debug mode)")
            
            
            # Log different types of matches with priority
            title_author_matches = sum(1 for book in filtered_books if book.get("title_author_matches", 0) > 0)
            other_keyword_matches = sum(1 for book in filtered_books if book.get("other_keyword_matches", 0) > 0)
            taxonomy_only = len(filtered_books) - title_author_matches - other_keyword_matches
            print(f"   - Title/Author matches: {title_author_matches} (highest priority)")
            print(f"   - Other keyword matches: {other_keyword_matches} (medium priority)")
            print(f"   - Taxonomy only: {taxonomy_only} (lowest priority)")

            # If no books found
            if not filtered_books:
                return jsonify({
                    "description": "Aucun livre trouvé pour cette requête.",
                    "user_id": user_id
                })

            # Return length of filtered books and description with performance metrics
            return jsonify({
                "description": categories["Description"],
                "user_id": user_id,
                "total_books": len(filtered_books),
                # Phase 2: Include performance metrics in response
                "performance": {
                    "response_time": total_time,
                    "gpt_time": total_gpt_time,
                    "filter_time": filter_time,
                    "cache_hit": categories is not None and gpt_cache.get(text, taxonomy_data) is not None
                }
            })

        except json.JSONDecodeError as e:
            total_time = time.time() - start_time
            # Phase 2: Track failed requests for monitoring
            performance_monitor.track_request(user_id, total_time)
            print(f"❌ JSON Decode Error: {e} (after {total_time:.2f}s)")
            return jsonify({
                "error": "Invalid response format from classification service",
                "user_id": user_id,
                "performance": {"response_time": total_time, "error": True}
            }), 500
        except Exception as e:
            total_time = time.time() - start_time
            # Phase 2: Track failed requests for monitoring
            performance_monitor.track_request(user_id, total_time)
            print(f"❌ Error in GPT call: {e} (after {total_time:.2f}s)")
            return jsonify({
                "error": "Classification service temporarily unavailable",
                "user_id": user_id,
                "performance": {"response_time": total_time, "error": True}
            }), 500
    
    # -------------------- Phase 2 Monitoring Routes --------------------
    
    @app.route("/health")
    def health_check():
        """
        Phase 2: Health check endpoint with detailed performance metrics
        """
        # Déterminer si on est en mode développement
        is_development = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('PORT') is None
        
        if is_development:
            # Mode développement - stats rapides pour éviter les blocages
            perf_report = performance_monitor.get_performance_report(safe_mode=True)
            cache_stats = gpt_cache.get_stats_fast()
        else:
            # Mode production - stats complètes
            perf_report = performance_monitor.get_performance_report(safe_mode=False)
            cache_stats = gpt_cache.get_stats(cleanup_expired=True)
            
        cleanup_stats = session_cleanup.get_cleanup_stats() if session_cleanup else {}
        
        return jsonify({
            "status": perf_report["status"],
            "timestamp": perf_report["timestamp"],
            "performance": perf_report,
            "cache": cache_stats,
            "cleanup": cleanup_stats,
            "active_sessions": len(user_filtered_books),
            "version": "Phase 2 - Multi-user optimized"
        })
    
    @app.route("/admin/cache/clear", methods=["POST"])
    def clear_cache():
        """
        Phase 2: Clear GPT cache (admin function)
        """
        gpt_cache.cache.clear()
        gpt_cache.reset_stats()
        return jsonify({"message": "Cache cleared successfully"})
    
    @app.route("/admin/sessions/cleanup", methods=["POST"])
    def force_cleanup():
        """
        Phase 2: Force cleanup of expired sessions (admin function)
        """
        if session_cleanup:
            cleaned = session_cleanup.cleanup_expired_sessions()
            return jsonify({
                "message": f"Cleaned {cleaned} expired sessions",
                "remaining_sessions": len(user_filtered_books)
            })
        return jsonify({"error": "Session cleanup not initialized"}), 500
    
    return app

# -------------------- Main Entry Point --------------------

if __name__ == "__main__":
    print("Starting BiblioSense app...")
    
    # Create the Flask app using the factory pattern
    app = create_app()
    
    # Get port from environment variable for Cloud Run compatibility
    port = int(os.environ.get('PORT', 8080))
    
    # Detect environment
    is_local = os.environ.get('PORT') is None  # No PORT env var = local development
    
    if is_local:
        print("🔧 Running in LOCAL development mode")
        # Use Flask's development server with debug mode but without reloader
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    else:
        print("🚀 Running in PRODUCTION mode (Cloud Run)")
        # Use Waitress for production
        serve(app, host='0.0.0.0', port=port)
