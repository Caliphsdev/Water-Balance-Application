import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader
from utils.config_manager import config

print(f"Config paths:")
print(f"  timeseries: {config.get('data_sources.timeseries_excel_path')}")
print(f"  template: {config.get('data_sources.template_excel_path')}")

loader = get_flow_volume_loader()
print(f"\nLoader using: {loader.excel_path}")

# Force reload without cache
import pandas as pd
df = pd.read_excel(loader.excel_path, sheet_name="Flows_MERS", header=2)
print(f"\nDirect pandas read of Flows_MERS: {len(df.columns)} columns")
print(f"Columns: {list(df.columns)[:5]}...{list(df.columns)[-5:]}")
