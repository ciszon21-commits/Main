
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_aliases():
    print("Fetching aliases from OpenSearch...")
    try:
        client = services.get_client()
        aliases = client.cat.aliases(format='json')
        print(f"Found {len(aliases)} aliases.")
        for a in aliases:
            print(f"- {a['alias']} -> {a['index']}")
            
        indices = client.cat.indices(format='json')
        print("\nAll User Indices:")
        for idx in indices:
            if not idx['index'].startswith('.'):
                print(f"- {idx['index']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_aliases()
