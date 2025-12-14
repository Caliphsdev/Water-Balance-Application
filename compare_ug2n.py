"""Compare UG2N database vs JSON diagram."""
import json

with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

print('JSON DIAGRAM: ug2_north_decline.json')
print('=' * 80)
print(f'Edges: {len(diagram.get("edges", []))}')
print()

json_edges = []
for edge in diagram.get('edges', []):
    from_node = edge.get('from')
    to_node = edge.get('to')
    json_edges.append(f'{from_node}__TO__{to_node}')
    print(f'{from_node:15} -> {to_node:15}')

# Database connections
db_conns = [
    'UG2N_ND__TO__UG2N_NDCDG',
    'UG2N_NDCDG__TO__UG2N_ND',
    'UG2N_NDCDG__TO__UG2N_NDCDG',
    'UG2N_NDSA__TO__UG2N_NDCDG',
    'UG2N_OFF__TO__UG2N_STP',
    'UG2N_RES__TO__UG2N_GH',
    'UG2N_RES__TO__UG2N_OFF',
    'UG2N_SOFT__TO__UG2N_RES',
    'UG2N_STP__TO__UG2N_NDCDG'
]

print(f'\nCOMPARISON:')
print('=' * 80)
print(f'Database: {len(db_conns)} connections')
print(f'JSON diagram: {len(json_edges)} edges')

only_in_db = set(db_conns) - set(json_edges)
only_in_json = set(json_edges) - set(db_conns)

if only_in_db:
    print(f'\nIn Database but NOT in JSON:')
    for conn in sorted(only_in_db):
        print(f'   {conn}')

if only_in_json:
    print(f'\nIn JSON but NOT in Database:')
    for conn in sorted(only_in_json):
        print(f'   {conn}')

if not only_in_db and not only_in_json:
    print(f'\nPerfect match!')
