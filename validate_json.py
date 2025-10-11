#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

def validate_json_file(filepath):
    """Validate JSON file and provide detailed feedback"""
    try:
        print(f"Validating: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✓ JSON is valid!")
        print(f"✓ File contains {len(data)} items")
        print(f"✓ File type: {type(data)}")
        
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            print(f"✓ First item keys: {list(first_item.keys())}")
            
            # Check for required fields
            required_fields = ['id', 'titre', 'auteur', 'lien']
            missing_fields = [field for field in required_fields if field not in first_item]
            
            if missing_fields:
                print(f"⚠ Missing required fields: {missing_fields}")
            else:
                print("✓ All required fields present")
                
            # Check for common issues
            issues = []
            
            # Check for duplicate IDs
            ids = [item.get('id') for item in data if 'id' in item]
            if len(ids) != len(set(ids)):
                issues.append("Duplicate IDs found")
            
            # Check for empty values
            for i, item in enumerate(data[:10]):  # Check first 10 items
                for key, value in item.items():
                    if value == "" or value is None:
                        issues.append(f"Empty value for '{key}' in item {i}")
                        break
            
            if issues:
                print("⚠ Issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✓ No obvious issues detected")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON Error: {e}")
        print(f"✗ Line {e.lineno}, Column {e.colno}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    filepath = r"C:\Users\denis\OneDrive\BiblioSense\dbase\book_dbase_montreal.json"
    validate_json_file(filepath)