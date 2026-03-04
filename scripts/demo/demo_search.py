import asyncio
import os
import sys
import json

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

async def demo_soul_search():
    from api.services.es_service import get_es_service
    
    # Mock AsyncElasticsearch Client
    class MockES:
        async def search(self, index, body):
            q = body['query']['bool']['must'][0]['multi_match']['query']
            print(f"  [ES] Searching for: '{q}' (Synonym expansion: joyful <-> happy enabled)")
            
            # Simulation response
            return {
                "hits": {
                    "total": {"value": 2},
                    "hits": [
                        {
                            "_score": 1.5,
                            "_source": {
                                "id": "101",
                                "entity": "JournalEntry",
                                "content": "I am feeling so happy today, full of JOY!",
                                "timestamp": "2026-02-28"
                            },
                            "highlight": {"content": ["I am feeling so <mark>happy</mark> today, full of <mark>JOY</mark>!"]}
                        },
                        {
                            "_score": 1.2,
                            "_source": {
                                "id": "102",
                                "entity": "JournalEntry",
                                "content": "Finding elation in small things.",
                                "timestamp": "2026-02-27"
                            },
                            "highlight": {"content": ["Finding <mark>elation</mark> in small things."]}
                        }
                    ]
                }
            }
        
    es = get_es_service()
    es.client = MockES()

    print(f"\n{'='*70}")
    print(f"FULL-TEXT SEARCH DEMO: SYNONYMS & ANALYZER (#1087)")
    print(f"{'='*70}")

    print("\n[SCENARIO] User searches for 'joyful'")
    print("Synonym Map: [happy, joyful, cheerful, elated]")
    
    res = await es.search(q="joyful", user_id=1)
    
    hits = res.get('hits', {}).get('hits', [])
    print(f"\nFound {len(hits)} relevant results:")
    for hit in hits:
        source = hit['_source']
        print(f"  - [{source['entity']} #{source['id']}] Score: {hit['_score']}")
        print(f"    Snippet: {hit['highlight']['content'][0]}")

    print("\nSearch Demonstration Complete.")

if __name__ == "__main__":
    asyncio.run(demo_soul_search())
