from re import Match
from flask import Flask, jsonify, render_template, request, session
import pandas as pd
from openai import OpenAI
import json
from waitress import serve
import os
import time
import uuid
from utils.gpt_services import get_catagories_with_gpt, get_catagories_with_gpt_cached, get_description_with_gpt_cached, get_keywords_with_gpt_cached, create_cached_gpt_function, log_query
from utils.text_matching import smart_keyword_match, calculate_keyword_score, calculate_taxonomy_score, merge_taxonomy_from_books, find_taxonomy_matches, filter_books_by_keywords
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
QUERY_LOG_FILE = "dbase/query_log.json"

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
    Also clears GPT cache for a fresh start.
    """
    global openai_client, gpt_cache
    
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
    
    # Clear GPT cache for fresh start
    if gpt_cache:
        cache_size_before = len(gpt_cache.cache)
        gpt_cache.cache.clear()
        gpt_cache.reset_stats()
        print(f"🧹 GPT cache cleared at startup ({cache_size_before} entries removed)")
    else:
        print("🧹 GPT cache will be cleared after initialization")

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
    global cached_gpt_keywords
    global cached_gpt_description
    cached_gpt_classifier, cached_gpt_keywords, cached_gpt_description = create_cached_gpt_function(gpt_cache, openai_client, taxonomy_data)

    print("✅ Optimizations initialized: Performance monitoring, GPT caching, Session cleanup")
    
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
        Advanced book filtering system using GPT-powered classification.
        
        This endpoint processes user queries through multiple phases:
        1. GPT keyword extraction for precise field matching
        2. Multi-tier book filtering (title/author > keywords > taxonomy)  
        3. Intelligent taxonomy merging and scoring
        4. Performance monitoring and caching optimization
        
        Args:
            JSON request with 'query' field containing the search text
            
        Returns:
            JSON response with filtered results count and description
        """
        # ==================== INITIALIZATION & THROTTLING ====================
        start_time = time.time()
        global taxonomy_data, books_data, openai_client, user_filtered_books, performance_monitor, gpt_cache
        
        # Performance throttling check - prevent system overload
        should_throttle, throttle_reason = performance_monitor.should_throttle()
        if should_throttle:
            return jsonify({
                "error": f"Service temporarily overloaded: {throttle_reason}. Please try again in a few moments.",
                "retry_after": 30
            }), 503
        
        # Session management with fallback safety
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            print(f"⚠️  Emergency session created in filter_categories: {session['user_id']}")

        user_id = session['user_id']
        data = request.get_json()
        query_text = data.get("query", "")
        
        # Update session activity for cleanup tracking
        if session_cleanup:
            session_cleanup.update_session_activity(user_id)
        
        print(f"🔍 Processing query for user {user_id}: '{query_text}'")

        try:
            # ==================== PHASE 1: GPT KEYWORD EXTRACTION ====================
            gpt_start_time = time.time()
            
            # Extract keywords from user query using cached GPT service
            # This identifies specific fields (title, author, genre, etc.) mentioned in the query
            keywords_result = cached_gpt_keywords(query_text)
            keyword_items = list(keywords_result["Mots-clés"].items())
            # print in structure format
            print(f"   → Extracted keywords: {json.dumps(keyword_items, ensure_ascii=False)}")
            gpt_keywords_time = time.time() - gpt_start_time

            # ==================== PHASE 2: KEYWORD-BASED FILTERING ====================
            keyword_filter_start = time.time()
            
            # Configure field priorities for matching
            title_author_fields = {"titre", "auteur"}
            # Check if keywords has title or author flags
            has_title_or_author = any(kw_key in title_author_fields for kw_key, _ in keyword_items)


            # Multi-tier filtering: separate title/author matches from general keyword matches
            title_author_matches, other_keyword_matches = filter_books_by_keywords(
                books_data, keyword_items, title_author_fields
            )
            
            keyword_filter_time = time.time() - keyword_filter_start
            print(f"   → Title/Author matches: {len(title_author_matches)}")
            print(f"   → Other keyword matches: {len(other_keyword_matches)}")

            # ==================== PHASE 3: TAXONOMY STRATEGY SELECTION ====================
            taxonomy_start_time = time.time()
            filtered_books = []
            
            # Strategy 1: High-confidence title/author matches found
            if len(title_author_matches) > 0 and title_author_matches[0].get("score", 0) >= 1:
                print("🎯 Strategy: Using title/author matches with merged taxonomy")
                # Merge taxonomy from found books to find similar works
                merged_taxonomy = merge_taxonomy_from_books(title_author_matches)
                filtered_books = title_author_matches
                
            # Strategy 2: Low-confidence or no title/author matches  
            elif len(title_author_matches) > 0:
                print("🤔 Strategy: Uncertain title/author, using GPT taxonomy")
                # Not confident about title/author matches, rely on GPT classification
                merged_taxonomy = cached_gpt_classifier(query_text)
                filtered_books = []

            # Strategy 3: No title/author matches, check for other keywords
            elif has_title_or_author==False and len(other_keyword_matches) > 0:
                print("🤔 Strategy: No title/author, using GPT taxonomy")
                # Not confident about title/author matches, rely on GPT classification
                merged_taxonomy = []
                filtered_books = other_keyword_matches 

            # Strategy 4: No title/author or other keyword matches 
            elif len(other_keyword_matches) == 0:
                print("🤔 Strategy: No title/author or other keyword matches, using GPT taxonomy")
                # Not confident about title/author matches, rely on GPT classification
                merged_taxonomy = cached_gpt_classifier(query_text)
                filtered_books = [] 


            # Normalize taxonomy format (convert sets to lists for JSON serialization)
            for main_category in merged_taxonomy:
                for sub_key in merged_taxonomy[main_category]:
                    if isinstance(merged_taxonomy[main_category][sub_key], set):
                        merged_taxonomy[main_category][sub_key] = list(merged_taxonomy[main_category][sub_key])

            # print merged taxonomy for debugging
            # print(f"📚 Merged taxonomy: {json.dumps(merged_taxonomy, ensure_ascii=False, indent=2)}"   )

            taxonomy_time = time.time() - taxonomy_start_time

            # ==================== PHASE 4: TAXONOMY-BASED EXPANSION ====================
            taxonomy_expansion_start = time.time()
            
            # Find additional books matching the established taxonomy
            # Exclude books already found through title/author matching
            taxonomy_matches = []
            if len(merged_taxonomy) > 0:
                title_author_book_ids = {book["id"] for book in title_author_matches}
                taxonomy_matches = find_taxonomy_matches(
                    books_data, merged_taxonomy, title_author_book_ids
                )          
                # Combine all results: prioritized matches + taxonomy expansions
                filtered_books.extend(taxonomy_matches)
            
            taxonomy_expansion_time = time.time() - taxonomy_expansion_start

            # ==================== PHASE 5: DESCRIPTION GENERATION ====================
            description_start_time = time.time()
            
            # Generate user-friendly description of the search results
            description_result = cached_gpt_description(query_text, merged_taxonomy)
            
            description_time = time.time() - description_start_time
            
            # ==================== PHASE 6: RESULTS PROCESSING & STORAGE ====================
            storage_start_time = time.time()
            
            # Debug output: show top results for verification
            # print(f"🎯 Final results preview:")
            # for i, book in enumerate(filtered_books[:10], 1):
            #     print(f"   {i}. {book.get('titre', 'Unknown Title')} (Score: {book.get('score', 0)})")

            # Store filtered results in user session for pagination
            user_filtered_books[user_id] = filtered_books
            
            storage_time = time.time() - storage_start_time

            # ==================== PHASE 7: PERFORMANCE ANALYTICS ====================
            # Calculate comprehensive timing breakdown
            total_time = time.time() - start_time
            total_gpt_time = gpt_keywords_time + description_time
            total_filtering_time = keyword_filter_time + taxonomy_time + taxonomy_expansion_time
            
            # Track request for performance monitoring
            performance_monitor.track_request(user_id, total_time)
            
            # Detailed performance logging
            # print(f"� Comprehensive Performance Analysis for user {user_id}:")
            # print(f"   ├─ GPT Operations: {total_gpt_time:.3f}s ({(total_gpt_time/total_time)*100:.1f}%)")
            # print(f"   │  ├─ Keyword extraction: {gpt_keywords_time:.3f}s")
            # print(f"   │  └─ Description generation: {description_time:.3f}s")
            # print(f"   ├─ Book Filtering: {total_filtering_time:.3f}s ({(total_filtering_time/total_time)*100:.1f}%)")
            # print(f"   │  ├─ Keyword filtering: {keyword_filter_time:.3f}s")
            # print(f"   │  ├─ Taxonomy processing: {taxonomy_time:.3f}s")
            # print(f"   │  └─ Taxonomy expansion: {taxonomy_expansion_time:.3f}s")
            # print(f"   ├─ Storage operations: {storage_time:.3f}s")
            print(f"   └─ TOTAL REQUEST TIME: {total_time:.3f}s")
            print(f"   📚 Results: {len(filtered_books)} books found")
            
            # Cache and system performance metrics
            cache_stats = gpt_cache.get_stats_fast()
            perf_stats = performance_monitor.get_stats(safe_mode=True)
            # print(f"🔄 Cache efficiency: {cache_stats['hit_rate_percent']:.1f}% hit rate")
            
            # if not perf_stats.get('debug_mode', False):
            #     print(f"� System resources: {perf_stats['active_users']} users, {perf_stats['memory_usage_percent']:.1f}% memory")
            # else:
            #     print(f"� System status: {perf_stats['active_users']} users (debug mode)")

            # ==================== PHASE 8: RESULT ANALYTICS & LOGGING ====================
            # Categorize and analyze match types
            title_author_count = len(title_author_matches)
            other_keyword_count = len(other_keyword_matches)
            taxonomy_only_count = len(taxonomy_matches)
            
            # print(f"🔍 Match type breakdown:")
            # print(f"   ├─ Title/Author matches: {title_author_count} (highest priority)")
            # print(f"   ├─ Other keyword matches: {other_keyword_count} (medium priority)")
            # print(f"   └─ Taxonomy-only matches: {taxonomy_only_count} (lowest priority)")

            # Calculate detailed scoring statistics for analytics
            score_stats = None
            if filtered_books:
                scores = [book.get("score", 0) for book in filtered_books]
                score_stats = {
                    "total_scores": {
                        "max": max(scores) if scores else 0,
                        "min": min(scores) if scores else 0,
                        "avg": sum(scores) / len(scores) if scores else 0
                    },
                    "match_counts": {
                        "title_author_matches": title_author_count,
                        "other_keyword_matches": other_keyword_count,  
                        "taxonomy_only_matches": taxonomy_only_count
                    },
                    "performance_breakdown": {
                        "title_author_avg_score": 100 if title_author_count > 0 else 0,
                        "other_keyword_avg_score": 100 if other_keyword_count > 0 else 0,
                        "taxonomy_avg_score": (sum(book.get("score", 0) for book in taxonomy_matches) / len(taxonomy_matches)) if taxonomy_matches else 0
                    }
                }

            # ==================== PHASE 9: RESPONSE GENERATION ====================
            # Prepare logging data structure
            log_data = {
                "Taxonomy": merged_taxonomy, 
                "Mots-clés": keywords_result["Mots-clés"], 
                "Description": description_result.get("Description", "")
            }

            # Handle different result scenarios
            if not filtered_books:
                # No results found - log and return empty response
                log_query(user_id, query_text, 0, total_time, log_data, score_stats)
                
                return jsonify({
                    "description": description_result.get("Description", "Aucune description disponible"),
                    "user_id": user_id,
                    "total_books": 0,
                    "performance": {
                        "total_time": round(total_time, 3),
                        "gpt_time": round(total_gpt_time, 3),
                        "filtering_time": round(total_filtering_time, 3)
                    }
                })
            else:
                # Successful search - log and return results
                log_query(user_id, query_text, len(filtered_books), total_time, log_data, score_stats)
                
                return jsonify({
                    "description": description_result.get("Description", "Aucune description disponible"),
                    "user_id": user_id,
                    "total_books": len(filtered_books),
                    "performance": {
                        "total_time": round(total_time, 3),
                        "gpt_time": round(total_gpt_time, 3),
                        "filtering_time": round(total_filtering_time, 3),
                        "cache_hit_rate": round(cache_stats['hit_rate_percent'], 1)
                    }
                })

        except json.JSONDecodeError as e:
            # ==================== ERROR HANDLING: JSON DECODE ====================
            total_time = time.time() - start_time
            log_query(user_id, query_text, -1, total_time)  # -1 indicates error
            performance_monitor.track_request(user_id, total_time)
            
            print(f"❌ JSON Decode Error: {e} (after {total_time:.3f}s)")
            return jsonify({
                "error": "Invalid response format from classification service",
                "user_id": user_id,
                "performance": {"response_time": round(total_time, 3), "error": True}
            }), 500
            
        except Exception as e:
            # ==================== ERROR HANDLING: GENERAL EXCEPTIONS ====================
            total_time = time.time() - start_time
            log_query(user_id, query_text, -1, total_time)  # -1 indicates error
            performance_monitor.track_request(user_id, total_time)
            
            print(f"❌ Unexpected error in filter_categories: {e} (after {total_time:.3f}s)")
            return jsonify({
                "error": "Classification service temporarily unavailable",
                "user_id": user_id,
                "performance": {"response_time": round(total_time, 3), "error": True}
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
    
    # Add a service to get logs
    @app.route("/admin/logs", methods=["GET"])
    def get_logs():
        """
        Phase 2: Get query logs (admin function)
        """
        try:
            with open("dbase/query_log.json", "r", encoding="utf-8") as f:
                logs = json.load(f)
            return jsonify(logs)
        except Exception as e:
            print(f"⚠️  Error retrieving logs: {e}")
            return jsonify({"error": "Failed to retrieve logs"}), 500
        
    @app.route("/admin/logs/clear", methods=["POST"])
    def clear_logs():   
        """
        Phase 2: Clear query logs (admin function)
        """
        try:
            with open("dbase/query_log.json", "w", encoding="utf-8") as f:
                json.dump([], f)  # Clear the log file
            return jsonify({"message": "Logs cleared successfully"})
        except Exception as e:
            print(f"⚠️  Error clearing logs: {e}")
            return jsonify({"error": "Failed to clear logs"}), 500
    
    
    
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
        # Use Flask's development server with debug mode and reloader enabled
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    else:
        print("🚀 Running in PRODUCTION mode (Cloud Run)")
        # Use Waitress for production
        serve(app, host='0.0.0.0', port=port)
