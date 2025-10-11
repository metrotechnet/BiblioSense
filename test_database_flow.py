#!/usr/bin/env python3
"""
Test script for database selection page functionality
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_database_selection_flow():
    """Test the complete database selection flow"""
    print("🚀 Testing Database Selection Flow")
    print("=" * 50)
    
    # Test 1: Access main page without database (should show selection page)
    print("🔍 Test 1: Accessing main page without database parameter...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200 and "Choisissez votre base de données" in response.text:
        print("✅ Main page correctly shows database selection")
    else:
        print("❌ Main page doesn't show database selection")
    
    # Test 2: Access database selection page explicitly
    print("\n🔍 Test 2: Accessing database selection page explicitly...")
    response = requests.get(f"{BASE_URL}/select-database")
    if response.status_code == 200 and "Choisissez votre base de données" in response.text:
        print("✅ Database selection page loads correctly")
    else:
        print("❌ Database selection page doesn't load")
    
    # Test 3: Access main page with valid database parameter
    print("\n🔍 Test 3: Accessing main page with Quebec database...")
    response = requests.get(f"{BASE_URL}/?database=quebec")
    if response.status_code == 200 and "BiblioSense" in response.text and "Base de données" in response.text:
        print("✅ Main page loads with Quebec database")
    else:
        print("❌ Main page doesn't load with Quebec database")
    
    print("\n🔍 Test 4: Accessing main page with Montreal database...")
    response = requests.get(f"{BASE_URL}/?database=montreal")
    if response.status_code == 200 and "BiblioSense" in response.text:
        print("✅ Main page loads with Montreal database")
    else:
        print("❌ Main page doesn't load with Montreal database")
    
    # Test 5: Test invalid database parameter
    print("\n🔍 Test 5: Accessing main page with invalid database...")
    response = requests.get(f"{BASE_URL}/?database=invalid")
    if response.status_code == 200 and "Choisissez votre base de données" in response.text:
        print("✅ Invalid database correctly redirects to selection page")
    else:
        print("❌ Invalid database doesn't redirect to selection page")
    
    # Test 6: Test databases API endpoint
    print("\n🔍 Test 6: Testing databases API endpoint...")
    response = requests.get(f"{BASE_URL}/databases")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Databases API works: {list(data['databases'].keys())}")
        
        # Check database counts
        for db_name, db_info in data['databases'].items():
            print(f"   - {db_info['name']}: {db_info['count']} livres")
    else:
        print("❌ Databases API doesn't work")
    
    print("\n✅ Database selection flow tests completed!")

if __name__ == "__main__":
    test_database_selection_flow()