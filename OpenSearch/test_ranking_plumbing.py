
import os
import sys
import django
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_boosting():
    client = services.get_client()
    
    # 1. Find a test document
    resp = client.search(index="sino_early", body={"size": 1})
    if not resp['hits']['hits']:
        print("No documents found to test.")
        return

    hit = resp['hits']['hits'][0]
    doc_id = hit['_id']
    index = hit['_index']
    title = hit['_source'].get('title', 'Unknown')
    
    print(f"Testing on doc: {title} ({doc_id})")
    
    # 2. Get current vote
    doc = client.get(index=index, id=doc_id)
    initial_vote = doc['_source'].get('vote', 0)
    print(f"Initial vote: {initial_vote}")
    
    # 3. Increment vote
    print("Incrementing vote...")
    success = services.increment_vote(index, doc_id)
    if not success:
        print("Failed to increment vote!")
        return
        
    time.sleep(1) # Wait for update
    
    # 4. Verify new vote
    doc = client.get(index=index, id=doc_id)
    new_vote = doc['_source'].get('vote', 0)
    print(f"New vote: {new_vote}")
    
    if new_vote > initial_vote:
        print("SUCCESS: Vote count incremented.")
    else:
        print("FAILURE: Vote count did not increase.")

if __name__ == "__main__":
    test_boosting()
