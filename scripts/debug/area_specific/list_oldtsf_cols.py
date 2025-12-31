import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from utils.flow_volume_loader import get_flow_volume_loader

loader = get_flow_volume_loader()
df = loader._load_sheet('Flows_OLDTSF')
cols = [str(c).strip() for c in df.columns if str(c).strip() not in {'Date','Year','Month'}]
print(f"Columns in Flows_OLDTSF ({len(cols)}):")
for c in cols:
    print(c)
