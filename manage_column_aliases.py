#!/usr/bin/env python
"""
Column Alias Manager - Interactive CLI for managing column-to-flow aliases.

Allows users to add, update, remove, and view column aliases without editing JSON manually.
Prevents typos and makes it easy to batch-add renamed columns.

Usage:
    python manage_column_aliases.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.column_alias_resolver import get_column_alias_resolver, reset_column_alias_resolver


def main():
    resolver = get_column_alias_resolver()
    
    while True:
        print("\n" + "="*60)
        print("Column Alias Manager")
        print("="*60)
        print("1. List all aliases")
        print("2. Add/update an alias")
        print("3. Remove an alias")
        print("4. Batch add aliases (from list)")
        print("5. Exit")
        print("="*60)
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            aliases = resolver.all_aliases()
            if not aliases:
                print("\n❌ No aliases configured yet")
            else:
                print(f"\n✅ {len(aliases)} aliases configured:\n")
                for col, target in sorted(aliases.items()):
                    print(f"  {col}")
                    print(f"    → {target}\n")
        
        elif choice == "2":
            col_name = input("\nColumn name (as appears in Excel): ").strip()
            target_flow = input("Target flow (from__TO__to format): ").strip()
            if col_name and target_flow:
                resolver.add_alias(col_name, target_flow)
                print(f"✅ Alias added: {col_name} → {target_flow}")
            else:
                print("❌ Both fields required")
        
        elif choice == "3":
            col_name = input("\nColumn name to remove: ").strip()
            if col_name in resolver.all_aliases():
                resolver.remove_alias(col_name)
                print(f"✅ Alias removed: {col_name}")
            else:
                print(f"❌ Alias not found: {col_name}")
        
        elif choice == "4":
            print("\nBatch add aliases (enter one per line, format: COLUMN_NAME | target_flow)")
            print("Example: OLDTSF_to_TRTDs(return) | oldtsf_trtd__TO__oldtsf_old_tsf")
            print("(Leave blank line to finish)\n")
            
            count = 0
            while True:
                line = input().strip()
                if not line:
                    break
                if " | " not in line:
                    print("❌ Invalid format, skipping. Use: COLUMN_NAME | target_flow")
                    continue
                col_name, target_flow = line.split(" | ", 1)
                col_name = col_name.strip()
                target_flow = target_flow.strip()
                if col_name and target_flow:
                    resolver.add_alias(col_name, target_flow)
                    count += 1
            
            print(f"\n✅ Added {count} aliases")
        
        elif choice == "5":
            print("\nGoodbye!")
            break
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
