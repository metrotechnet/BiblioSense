#!/usr/bin/env python3
"""
Test script to verify French database names display correctly
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_french_names():
    """Test that French names are displayed correctly"""
    print("🇫🇷 Testing French Database Names Display")
    print("=" * 50)
    
    # Test 1: Check databases API returns French names
    print("🔍 Test 1: Checking databases API for French names...")
    try:
        response = requests.get(f"{BASE_URL}/databases")
        if response.status_code == 200:
            data = response.json()
            quebec_name = data['databases']['quebec']['name']
            montreal_name = data['databases']['montreal']['name']
            
            if quebec_name == "Québec":
                print("✅ Quebec database shows as 'Québec'")
            else:
                print(f"❌ Quebec database shows as '{quebec_name}' instead of 'Québec'")
                
            if montreal_name == "Montréal":
                print("✅ Montreal database shows as 'Montréal'")
            else:
                print(f"❌ Montreal database shows as '{montreal_name}' instead of 'Montréal'")
                
            print(f"📊 Database info:")
            for db_key, db_info in data['databases'].items():
                print(f"   - {db_info['name']}: {db_info['count']} livres")
        else:
            print(f"❌ Error accessing databases API: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check main page with Quebec database
    print("\n🔍 Test 2: Checking main page with Quebec database...")
    try:
        response = requests.get(f"{BASE_URL}/?database=quebec")
        if response.status_code == 200:
            if "Québec" in response.text:
                print("✅ Main page shows 'Québec' in header")
            else:
                print("❌ Main page doesn't show 'Québec' in header")
        else:
            print(f"❌ Error accessing main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check main page with Montreal database
    print("\n🔍 Test 3: Checking main page with Montreal database...")
    try:
        response = requests.get(f"{BASE_URL}/?database=montreal")
        if response.status_code == 200:
            if "Montréal" in response.text:
                print("✅ Main page shows 'Montréal' in header")
            else:
                print("❌ Main page doesn't show 'Montréal' in header")
        else:
            print(f"❌ Error accessing main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Check database selection page
    print("\n🔍 Test 4: Checking database selection page...")
    try:
        response = requests.get(f"{BASE_URL}/select-database")
        if response.status_code == 200:
            content = response.text
            if "Québec" in content and "Montréal" in content:
                print("✅ Database selection page shows French names")
            else:
                print("❌ Database selection page doesn't show proper French names")
                if "Quebec" in content or "Montreal" in content:
                    print("   ⚠️  Found English names instead")
        else:
            print(f"❌ Error accessing selection page: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ French names testing completed!")

if __name__ == "__main__":
    test_french_names()