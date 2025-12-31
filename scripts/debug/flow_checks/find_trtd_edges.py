import json
from pathlib import Path

p=Path('data/diagrams/ug2_north_decline.json')
edges=json.load(open(p)).get('edges',[])
for i,e in enumerate(edges):
    if e.get('from')=='oldtsf_trtd' and e.get('to')=='oldtsf_old_tsf':
        print(i, e.get('flow_type'), e.get('volume'), e.get('excel_mapping'))
