# ✅ Copilot Instructions Update Summary

## Changes Made

Updated `.github/copilot-instructions.md` to reflect recent development patterns and discoveries from the codebase analysis.

### Key Updates

#### 1. **Enhanced Architecture Overview**
- Added details about on-demand Excel loading strategy
- Documented reactive UI with fast startup feature
- Clarified module organization (25+ UI modules)
- Added `flow_volume_loader.py` as critical component

#### 2. **Singleton Pattern Documentation**
- **NEW**: Added reset mechanism section
- Documented `reset_flow_volume_loader()` pattern
- Explained when and how to reset singletons for config changes
- Critical for Settings → Singleton path propagation

#### 3. **Excel Loading (On-Demand Pattern)**
- **NEW**: Comprehensive section on flow diagram Excel loading
- Path resolution priority documented (timeseries → template → default)
- Settings change workflow explained step-by-step
- Format support (Date vs Year/Month columns) documented
- Example code showing fresh instance + cache clear pattern

#### 4. **Configuration Management**
- Enhanced with `config.load_config()` for post-Settings reload
- Emphasized that singletons need explicit reset after config changes
- Added warning about automatic config pickup limitations

#### 5. **Import Path Pattern**
- Clarified as required in ALL src/ modules
- Added emphasis on path insertion for relative imports

#### 6. **Error Handling & Logging**
- Separated into proper sections (7 & 8)
- Included performance timing examples
- Full return value documentation

#### 7. **Flow Diagram Module**
- Added `excel_mapping` pattern documentation
- Documented 21 mapped vs 131 unmapped edges in UG2N
- Loading workflow: Load → Fresh Instance → Clear Cache → Redraw
- Auto-color detection for wastewater/underground return

#### 8. **Common Pitfalls**
- **NEW ITEMS:**
  - Pitfall #8: Singleton config reload timing (critical!)
  - Pitfall #9: Calling reset functions when Settings changes paths
- More specific and actionable

#### 9. **Singleton Reset Patterns**
- **ENTIRELY NEW SECTION**
- Explains when/why/how to reset singletons
- Two working examples (Settings path change, Flow diagram refresh)
- Lists known reset functions and patterns

#### 10. **Utility Singletons Reference**
- Added `get_flow_volume_loader()` with comment
- Now documents all 8 critical singleton getters

### Validation

✅ All patterns sourced from actual codebase
✅ Recent fixes (singleton reset) documented
✅ Examples use real file paths and method names
✅ Maintains backward compatibility with existing content
✅ Organized logically for AI agent onboarding

### What This Helps

AI agents will now understand:
1. **Why** Settings changes require singleton resets
2. **How** Excel loading is on-demand and path-aware
3. **When** to use config reload vs singleton reset
4. **Where** to find working examples (flow_volume_loader.py)
5. **What** patterns to follow for similar features

### Files Updated
- `.github/copilot-instructions.md` (+47 lines, reorganized existing content)

### Example: The Flow

```
User Changes Excel Path in Settings
  ↓
config.set() updates YAML file
  ↓
reset_flow_volume_loader() clears singleton instance
  ↓
User clicks "Load from Excel"
  ↓
get_flow_volume_loader() creates NEW instance
  ↓
new loader reads FRESH config with new path
  ↓
Works! ✅
```

---

**Status**: ✅ READY  
**Reviewer**: AI coding agents will have improved context  
**Impact**: Fewer singleton-related bugs, faster onboarding

