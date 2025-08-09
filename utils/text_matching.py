#!/usr/bin/env python3
"""
text_matching.py

Fonctions utilitaires pour la correspondance intelligente de texte,
spécialement optimisées pour les noms d'auteurs et la recherche de livres.
"""

from multiprocessing.util import debug
import re
import unicodedata


def normalize_text(text):
    """
    Normalize text by removing accents, converting to lowercase, and cleaning.
    
    Args:
        text (str): Text to normalize
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
    
    # Remove accents and diacritics
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Convert to lowercase and remove extra spaces
    text = text.lower().strip()
    
    # Remove common author suffixes and prefixes
    text = re.sub(r'\b(auteur|narrateur|traducteur|editeur|dr|prof|mr|mrs|ms|sir|lady)\b', '', text)
    text = re.sub(r'[(),]', '', text)  # Remove parentheses and commas
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces
    
    return text


def extract_initials_and_names(author_name):
    """
    Extract initials and full names from an author string.
    If no initials exist, generate them from first names.
    
    Args:
        author_name (str): Author name to analyze
        
    Returns:
        dict: Dictionary with initials, first names, and last names
    """
    normalized = normalize_text(author_name)
    parts = normalized.split()
    
    result = {
        'initials': [],
        'first_names': [],
        'last_names': [],
        'all_parts': parts
    }
    
    for part in parts:
        if len(part) <= 2 and part.replace('.', '').isalpha():
            # This is likely an initial
            initial = part.replace('.', '').upper()
            result['initials'].append(initial)
        elif len(part) > 2:
            # This is likely a full name
            # Heuristic: if it's capitalized in original, it might be a last name
            # For simplicity, we'll treat longer names as potential first or last names
            if parts.index(part) >= len(parts) // 2:
                result['last_names'].append(part)
            else:
                result['first_names'].append(part)
    
    # Generate initials from first names if no initials exist
    if not result['initials'] and result['first_names']:
        for first_name in result['first_names']:
            if first_name and len(first_name) > 0:
                result['initials'].append(first_name[0].upper()+'.')

    return result


def author_similarity_score(query_author, book_author):
    """
    Calculate similarity score between two author names, handling initials and variations.
    
    Args:
        query_author (str): Author name from the query
        book_author (str): Author name from the book data
        
    Returns:
        float: Score from 0 to 1, where 1 is a perfect match
        
    Examples:
        >>> author_similarity_score("L.M. Montgomery", "Lucy Maud Montgomery")
        0.8
        >>> author_similarity_score("J.K. Rowling", "Joanne Kathleen Rowling")
        0.8
        >>> author_similarity_score("Tolkien", "J.R.R. Tolkien")
        0.6
    """
    if not query_author or not book_author:
        return 0.0
    
    # Exact match after normalization
    norm_query = normalize_text(query_author)
    norm_book = normalize_text(book_author)
    
    if norm_query == norm_book:
        return 1.0
    
    # If one is contained in the other (for partial matches)
    if norm_query in norm_book or norm_book in norm_query:
        return 1.0
    
    # Extract components for more sophisticated matching
    query_parts = extract_initials_and_names(query_author)
    book_parts = extract_initials_and_names(book_author)
    
    score = 0.0
    max_possible_score = 0.6
    
    # Check last names match (highest weight)
    if query_parts['last_names'] and book_parts['last_names']:
        for q_last in query_parts['last_names']:
            for b_last in book_parts['last_names']:
                if q_last == b_last:
                    score += 0.4
                    break

    
    # Check first names vs initials
    if query_parts['first_names'] or query_parts['initials']:
        
        # Case 1: Query has initials, book has full first names
        for q_initial in query_parts['initials']:
            for b_first in book_parts['first_names']:
                if b_first.startswith(q_initial.lower()):
                    score += 0.2
                    break
        
        # Case 2: Query has full names, book has initials
        for q_first in query_parts['first_names']:
            for b_initial in book_parts['initials']:
                if q_first.startswith(b_initial.lower()):
                    score += 0.2
                    break
        
        # Case 3: Both have full first names
        for q_first in query_parts['first_names']:
            for b_first in book_parts['first_names']:
                if q_first == b_first:
                    score += 0.2
                    break

    
    # Normalize score
    if max_possible_score > 0:
        return min(score / max_possible_score, 1.0)
    
   
    return 0.0


def smart_keyword_match(query_value, book_field, field_name=""):
    """
    Perform smart matching for different types of fields.
    
    Args:
        query_value (str): Value from the search query
        book_field (str): Field value from the book data
        field_name (str): Name of the field being matched (for specialized handling)
        
    Returns:
        float: Score from 0 to 1 indicating match quality
        
    Examples:
        >>> smart_keyword_match("L.M. Montgomery", "Lucy Maud Montgomery", "auteur")
        0.8
        >>> smart_keyword_match("science fiction", "Science Fiction Novel", "genre")
        0.8
    """
    if not query_value or not book_field:
        return 0.0
    
    query_lower = query_value.lower().strip()
    book_lower = book_field.lower().strip()
    
    
    # For author fields, use sophisticated author matching
    if field_name == "auteur" or "author" in field_name.lower():
        return author_similarity_score(query_value, book_field)
    
    # For title fields, allow partial matches with high weight
    elif field_name.lower() in ["titre", "title"]:
        if query_lower == book_lower:
            return 1.0
        elif query_lower in book_lower or book_lower in query_lower:
            return 0.8
        else:
            return 0.0
        
    # For page counts, interpret ranges. if query_value is `plus que` check if pages is more. if query_value is `moins que` check if pages is less.
    elif field_name.lower() in ["pages", "page count", "nombre de pages"]:
        try:
            query_pages = int(re.sub(r'\D', '', query_value))
            book_pages = int(re.sub(r'\D', '', book_field))
            
            # French/English variants for "more than" / "plus de"
            more_than_patterns = ["plus", "plus de", "plus que", "more than", "more", "over", "above", "minimum"]
            # French/English variants for "less than" / "moins de"
            less_than_patterns = ["moins", "moins de", "moins que", "less than", "less", "under", "below", "maximum", "max"]
            
            query_lower = query_value.lower()
            
            # Check if query contains "more than" variants
            if any(pattern in query_lower for pattern in more_than_patterns):
                if book_pages >= query_pages:
                    return 1.0
                else:
                    return 0.0
            # Check if query contains "less than" variants
            elif any(pattern in query_lower for pattern in less_than_patterns):
                if book_pages <= query_pages:
                    return 1.0
                else:
                    return 0.0
            # Exact match or range (no comparison keywords)
            else:
                if abs(query_pages - book_pages) <= 10:
                    return 1.0 if query_pages == book_pages else 0.9
                else:
                    return 0.0
        except ValueError:
            return 0.0
        
    # For publication years with French/English variants
    elif field_name.lower() in ["parution", "publication year", "année de parution"]:
        try:
            query_year = int(re.sub(r'\D', '', query_value))
            book_year = int(re.sub(r'\D', '', book_field))
            
            # French/English variants for "after" / "après"
            after_patterns = ["après", "apres", "after", "since", "from", "starting", "minimum", "plus récent", "plus recent"]
            # French/English variants for "before" / "avant"
            before_patterns = ["avant", "before", "until", "prior", "maximum", "max", "plus ancien", "older"]
            
            query_lower = query_value.lower()
            
            # Check if query contains "after" variants
            if any(pattern in query_lower for pattern in after_patterns):
                if book_year >= query_year:
                    return 1.0
                else:
                    return 0.0
            # Check if query contains "before" variants
            elif any(pattern in query_lower for pattern in before_patterns):
                if book_year <= query_year:
                    return 1.0
                else:
                    return 0.0
            # Exact year match (no comparison keywords)
            else:
                if query_year == book_year:
                    return 1.0
                else:
                    return 0.0
        except ValueError:
            return 0.0
        
    elif field_name.lower() in ["langue", "language"]:
        if query_lower == book_lower:
            return 1.0
        else:
            return 0.0
        
    elif field_name.lower() in ["editeur", "publisher"]:
        if query_lower == book_lower:
            return 1.0
        elif query_lower in book_lower or book_lower in query_lower:
            return 0.8
        else:
            return 0.0
        
    elif field_name.lower() in ["categorie", "category", "genre"]:
        if re.search(r'\b' + re.escape(query_lower) + r'\b', book_lower):
            return 1.0
        else:
            return 0.0
       
    elif field_name.lower() in ["resume", "summary", "description"]:
        # Check if book_lower appears as full words in query_lower
        if re.search(r'\b' + re.escape(query_value.strip()) + r'\b', book_lower):
            return 1.0
        else:
            return 0.0

    
    return 0.0


def calculate_keyword_score(keyword_items, book, title_author_fields):
    """
    Calculate keyword matching score for a book.
    
    Args:
        keyword_items (list): List of (keyword_key, keyword_values) tuples
        book (dict): Book data dictionary
        title_author_fields (set): Set of fields considered as title/author
        
    Returns:
        tuple: (title_author_score, other_keyword_score)
    """
    # if book.get('id') == 'book_4700':
    #     print("Special case for book_4700")
    has_title_author_match = False
    tot_match_score = 0
    for keyword_key, keyword_values in keyword_items:
        is_title_author = keyword_key in title_author_fields
        if not keyword_values:
            continue
        # Handle both single keywords (string) and multiple keywords (list)
        if isinstance(keyword_values, str):
            keyword_values = [keyword_values]  # Convert to list for uniform processing        
        # Special handling for 'categorie' - check multiple fields
        if keyword_key == 'categorie':

            # Check 'categorie' field
            match_score=0
            categorie_field = book.get('categorie')
            if categorie_field:
                for keyword_variant in keyword_values:
                    match_score = smart_keyword_match(keyword_variant, categorie_field, 'categorie')
                    tot_match_score += match_score
                    if match_score > 0:
                        break

            # Check 'resume' field
            if match_score==0:
                resume_field = book.get('resume')
                if resume_field:
                    for keyword_variant in keyword_values:
                        match_score = smart_keyword_match(keyword_variant, resume_field, 'resume')
                        tot_match_score += match_score
                        if match_score > 0:
                            break
       
        # Standard handling for other fields - check only the corresponding field
        else:
            book_field = book.get(keyword_key)
            if not book_field:
                continue

            for keyword_variant in keyword_values:
                match_score = smart_keyword_match(keyword_variant, book_field, keyword_key)
                tot_match_score += match_score
                if match_score > 0:
                    break

        # Assign scores based on match type
        if tot_match_score > 0 and is_title_author:
            has_title_author_match = True

    
    # If we have title/author match, return that score and 0 for other
    # Otherwise return 0 for title/author and the other score
    score = tot_match_score / len(keyword_items) if keyword_items else 0

    if has_title_author_match:
        return score, 0
    else:
        return 0, score


def merge_taxonomy_from_books(title_author_matches):
    """
    Merge taxonomy from a list of books into a unified structure.
    
    Args:
        title_author_matches (list): List of book dictionaries with classification data
        
    Returns:
        dict: Merged taxonomy structure with all categories from the input books
    """
    import json
    
    # Initialize the merged taxonomy structure
    merged_taxonomy = {
        "Genre Littéraire": {"Fiction": set(), "Non-fiction": set()},
        "Thèmes - Concepts Clés": {
            "Société": set(), 
            "Technologie": set(), 
            "Relations humaines": set(), 
            "Épopées et quêtes": set(), 
            "Philosophie / Métaphysique": set()
        },
        "Type de Public": {"Format": set()},
        "Structure Narrative": {"Point de vue": set(), "Temporalité": set(), "Style": set()},
        "Personnages / Relations": {"Type de protagoniste": set(), "Relations dominantes": set()}
    }
    
    # Process each book's taxonomy
    for book in title_author_matches:
        taxonomy_str = book.get("classification")
        if taxonomy_str:
            try:
                # Parse the JSON string to get the taxonomy dict
                taxonomy = json.loads(taxonomy_str)
                
                # Merge taxonomy categories into the reference structure
                for main_category, sub_categories in taxonomy.items():
                    if main_category in merged_taxonomy:
                        for sub_key, values in sub_categories.items():
                            if sub_key in merged_taxonomy[main_category]:
                                if values:  # Only add non-null values
                                    if isinstance(values, list):
                                        merged_taxonomy[main_category][sub_key].update(values)
                                    elif isinstance(values, str):
                                        merged_taxonomy[main_category][sub_key].add(values)
            except (json.JSONDecodeError, TypeError):
                # Skip books with invalid taxonomy data
                continue
    
    # Convert sets back to lists for easier processing
    for main_category in merged_taxonomy:
        for sub_key in merged_taxonomy[main_category]:
            if isinstance(merged_taxonomy[main_category][sub_key], set):
                merged_taxonomy[main_category][sub_key] = list(merged_taxonomy[main_category][sub_key])
    
    return merged_taxonomy


def calculate_taxonomy_score(merged_taxonomy, book):
    """
    Calculate taxonomy matching score for a book against merged taxonomy.
    
    Args:
        merged_taxonomy (dict): Merged taxonomy structure from matching books
        book (dict): Book data dictionary
        
    Returns:
        int: Taxonomy score
    """
    import json
    
    taxonomy_score = 0
    book_taxonomy = {}
    
    # Parse book taxonomy
    if book.get("classification"):
        try:
            book_taxonomy = json.loads(book["classification"])
        except (json.JSONDecodeError, TypeError, KeyError):
            book_taxonomy = {}
    
    # Check taxonomy matches against merged structure
    if book_taxonomy and merged_taxonomy:
        for main_category, sub_categories in merged_taxonomy.items():
            book_main_section = book_taxonomy.get(main_category)
            if book_main_section:
                for sub_key, merged_values in sub_categories.items():
                    if merged_values:  # Only check if merged category has values
                        book_values = book_main_section.get(sub_key)
                        if book_values:
                            if isinstance(book_values, list):
                                # Count intersections between book values and merged values
                                matches = set(book_values).intersection(set(merged_values))
                                taxonomy_score += len(matches)
                            elif book_values in merged_values:
                                taxonomy_score += 1
    
    return taxonomy_score


def find_taxonomy_matches(books_data, merged_taxonomy, title_author_book_ids):
    """
    Find books that match the merged taxonomy and score them based on similarity.
    
    Args:
        books_data (list): List of all books to search through
        merged_taxonomy (dict): Merged taxonomy structure to match against
        title_author_book_ids (set): Set of book IDs that already matched title/author to exclude
        
    Returns:
        tuple: (taxonomy_matches, max_possible_score) where taxonomy_matches is a list of books 
               with scores and max_possible_score is the highest score found
    """
    taxonomy_matches = []
    max_possible_score = 0
    
    for book in books_data:
        book_taxonomy = book.get("classification")
        if not book_taxonomy:
            continue
        if book["id"] in title_author_book_ids:
            continue
        taxonomy_score = calculate_taxonomy_score(merged_taxonomy, book)
        max_possible_score = max(max_possible_score, taxonomy_score)
        if taxonomy_score > 0:
            book_copy = {**book, "score": taxonomy_score}
            taxonomy_matches.append(book_copy)

    # Sort by score descending and filter to top-scoring books
    taxonomy_matches = sorted(taxonomy_matches, key=lambda x: x.get("score", 0), reverse=True)
    if max_possible_score > 0:
        taxonomy_matches = [book for book in taxonomy_matches if book.get("score", 0) >= max(1, 2 * max_possible_score / 3)]

    return taxonomy_matches


def filter_books_by_keywords(books_data, keyword_items, title_author_fields):
    """
    Filter books based on keyword matching and categorize them by match type.
    
    Args:
        books_data (list): List of all books to search through
        keyword_items (list): List of (field, keywords) tuples from GPT keyword extraction
        title_author_fields (set): Set of field names considered as title/author fields
        
    Returns:
        tuple: (title_author_matches, other_keyword_matches, best_title_author_score, has_title_or_author)
               where each match list contains books with their scores
    """
    title_author_matches = []
    other_keyword_matches = []
    
    
    # Single pass through books with optimized scoring
    for book in books_data:
        # Early exit if no potential matches
        has_keywords = any(book.get(kw_key) for kw_key, _ in keyword_items)
        
        if not has_keywords:
            continue

        # Check keyword matches with smart matching (only if has keywords)
        title_author_score, other_keyword_score = calculate_keyword_score(keyword_items, book, title_author_fields)

        # if title_author_score has score >0 that save in title_author_matches
        if title_author_score >= 1.0:
            book_copy = {**book, "score": title_author_score}
            title_author_matches.append(book_copy)
        elif title_author_score == 0 and other_keyword_score >= 1.0:
            book_copy = {**book, "score": other_keyword_score}
            other_keyword_matches.append(book_copy)

    # Sort title_author_matches in descending order by score
    title_author_matches = sorted(title_author_matches, key=lambda x: x.get("score", 0), reverse=True)
    # sort other_keyword_matches in descending order by score
    other_keyword_matches = sorted(other_keyword_matches, key=lambda x: x.get("score", 0), reverse=True)

    return title_author_matches, other_keyword_matches

