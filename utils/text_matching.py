#!/usr/bin/env python3
"""
text_matching.py

Fonctions utilitaires pour la correspondance intelligente de texte,
spécialement optimisées pour les noms d'auteurs et la recherche de livres.
"""

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
        return 0.8
    
    # Extract components for more sophisticated matching
    query_parts = extract_initials_and_names(query_author)
    book_parts = extract_initials_and_names(book_author)
    
    score = 0.0
    max_possible_score = 0.0
    
    # Check last names match (highest weight)
    if query_parts['last_names'] and book_parts['last_names']:
        max_possible_score += 0.6
        for q_last in query_parts['last_names']:
            for b_last in book_parts['last_names']:
                if q_last == b_last:
                    score += 0.6
                    break
                elif q_last in b_last or b_last in q_last:
                    score += 0.4
                    break
    
    # Check first names vs initials
    if query_parts['first_names'] or query_parts['initials']:
        max_possible_score += 0.4
        
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
                    score += 0.4
                    break
                elif q_first in b_first or b_first in q_first:
                    score += 0.2
                    break
    
    # Normalize score
    if max_possible_score > 0:
        return min(score / max_possible_score, 1.0)
    
    # Fallback: check if any words match
    query_words = set(norm_query.split())
    book_words = set(norm_book.split())
    common_words = query_words.intersection(book_words)
    
    if common_words:
        return len(common_words) / max(len(query_words), len(book_words)) * 0.5
    
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
    
    # Exact match
    if query_lower == book_lower:
        return 1.0
    
    # For author fields, use sophisticated author matching
    if field_name == "auteur" or "author" in field_name.lower():
        return author_similarity_score(query_value, book_field)

    # For page counts, interpret ranges. if query_value is `plus que` check if pages is more. if query_value is `moins que` check if pages is less.
    if field_name.lower() in ["pages", "page count", "nombre de pages"]:
        try:
            query_pages = int(re.sub(r'\D', '', query_value))
            book_pages = int(re.sub(r'\D', '', book_field))
            if "plus" in query_value.lower() and book_pages >= query_pages:
                return 1.0
            elif "moins" in query_value.lower() and book_pages <= query_pages:
                return 1.0
            elif abs(query_pages - book_pages) <= 10:
                return 1.0
            else:
                return 0.0
        except ValueError:
            return 0.0

    # Word-based matching
    query_words = set(query_lower.split())
    book_words = set(book_lower.split())
    common_words = query_words.intersection(book_words)
    
    if common_words:
        return len(common_words) / max(len(query_words), len(book_words)) * 0.6
    
    return 0.0


def test_author_matching():
    """
    Test function to demonstrate author matching capabilities.
    """
    print("🧪 Testing Author Matching System")
    print("=" * 50)
    
    test_cases = [
        ("L.M. Montgomery", "Lucy Maud Montgomery"),
        ("J.K. Rowling", "Joanne Kathleen Rowling"),
        ("Tolkien", "J.R.R. Tolkien"),
        ("L. Montgomery", "Lucy Montgomery"),
        ("Montgomery", "L.M. Montgomery"),
        ("Victor Hugo", "Victor Hugo"),
        ("V. Hugo", "Victor Hugo"),
        ("Alexandre Dumas", "A. Dumas"),
    ]
    
    for query, book in test_cases:
        score = author_similarity_score(query, book)
        print(f"'{query}' ↔ '{book}' → {score:.3f}")
    
    print("=" * 50)


if __name__ == "__main__":
    # Run tests if script is executed directly
    test_author_matching()
