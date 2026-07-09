import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from knowledge.graph import get_knowledge_graph
g = get_knowledge_graph()
import json
stats = g.get_stats()
print("Stats:", json.dumps(stats, ensure_ascii=False, indent=2))
d = g.to_dict()
print(f"Nodes: {len(d['nodes'])}, Links: {len(d['links'])}")
if d['nodes']:
    for n in d['nodes'][:3]:
        print(f"  - {n['name']} ({n['type']}, conf={n['confidence']})")
if d['links']:
    for l in d['links'][:3]:
        print(f"  {l['source']} --[{l['type']}]--> {l['target']}")
