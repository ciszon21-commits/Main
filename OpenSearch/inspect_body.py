
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def inspect_query_body():
    print("Inspecting OpenSearch query body...")
    
    # We can't easily capture the body without patching the client's search method
    from unittest.mock import patch
    
    with patch('opensearchpy.OpenSearch.search') as mock_search:
        mock_search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        
        # Test Case 1: Empty Query
        services.search("", indices="*")
        args, kwargs = mock_search.call_args
        print("\n--- Body for empty query ('*') ---")
        print(json.dumps(kwargs.get('body'), indent=2, ensure_ascii=False))
        
        # Test Case 2: Keyword Query
        services.search("測試", indices="*")
        args, kwargs = mock_search.call_args
        print("\n--- Body for keyword '測試' ('*') ---")
        print(json.dumps(kwargs.get('body'), indent=2, ensure_ascii=False))

        # Test Case 3: Category Query
        services.search("", indices="sino_early*")
        args, kwargs = mock_search.call_args
        print("\n--- Body for category 'sino_early*' ---")
        print(f"Target Indices: {kwargs.get('index')}")
        print(json.dumps(kwargs.get('body'), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    inspect_query_body()
