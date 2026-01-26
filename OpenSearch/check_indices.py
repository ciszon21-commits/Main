
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_indices():
    print("Fetching indices from OpenSearch...")
    try:
        indices = services.get_indices()
        print(f"Found {len(indices)} user indices.")
        for idx in indices[:20]:  # Show first 20
            print(f"- {idx['index']} ({idx.get('docs.count', '0')} docs)")
        if len(indices) > 20:
            print("...")
            
        print("\nChecking category mapping for 'sino_early'...")
        categories = services.get_index_categories()
        early = categories.get('sino_early')
        if early:
            print(f"sino_early: {early['count']} indices, {early['total_docs']} total docs")
            for idx in early['indices']:
                print(f"  - {idx['index']}")
        else:
            print("sino_early category not found!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_indices()
