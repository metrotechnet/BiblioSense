#!/usr/bin/env python3
"""
Test script for database selection functionality
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_databases_endpoint():
    """Test the /databases endpoint"""
    print("🔍 Testing /databases endpoint...")
    response = requests.get(f"{BASE_URL}/databases")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available databases: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_count_books(database=None):
    """Test the /count_books endpoint with database selection"""
    if database:
        url = f"{BASE_URL}/count_books/{database}"
        print(f"🔍 Testing /count_books/{database} endpoint...")
    else:
        url = f"{BASE_URL}/count_books"
        print("🔍 Testing /count_books endpoint (default)...")
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Book count: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_books_endpoint(database=None):
    """Test the /books endpoint with database selection"""
    if database:
        url = f"{BASE_URL}/books/{database}/0/4"  # First 5 books
        print(f"🔍 Testing /books/{database}/0/4 endpoint...")
    else:
        url = f"{BASE_URL}/books/0/4"  # First 5 books
        print("🔍 Testing /books/0/4 endpoint (default)...")
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Books data: Database={data.get('database', 'N/A')}, Count={len(data.get('book_list', []))}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def test_filter_endpoint(query="science fiction", database="quebec"):
    """Test the /filter endpoint with database selection"""
    print(f"🔍 Testing /filter endpoint with database '{database}' and query '{query}'...")
    
    payload = {
        "query": query,
        "database": database
    }
    
    response = requests.post(f"{BASE_URL}/filter", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Filter results: Database={data.get('database', 'N/A')}, Books={data.get('total_books', 0)}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    print("🚀 Testing Database Selection Functionality")
    print("=" * 50)
    
    # Test 1: List available databases
    databases_info = test_databases_endpoint()
    print("\n" + "-" * 30 + "\n")
    
    # Test 2: Count books for each database
    test_count_books()  # Default (Quebec)
    test_count_books("quebec")
    test_count_books("montreal")
    print("\n" + "-" * 30 + "\n")
    
    # Test 3: Get books from each database
    test_books_endpoint()  # Default (Quebec)
    test_books_endpoint("quebec")
    test_books_endpoint("montreal")
    print("\n" + "-" * 30 + "\n")
    
    # Test 4: Filter with different databases
    test_filter_endpoint("science fiction", "quebec")
    test_filter_endpoint("fantasy", "montreal")
    
    print("\n✅ All tests completed!")