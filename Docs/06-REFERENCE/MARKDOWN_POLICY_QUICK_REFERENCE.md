# Quick Reference: Markdown File Policy

**TL;DR**: Think before creating `.md` files. Check what exists first.

---

## ⚡ Quick Decision Tree

```
Want to create a .md file?

1. Does it already exist?
   YES → Update existing file ✅
   NO → Continue

2. Can you add to existing file?
   YES → Add + update INDEX.md ✅
   NO → Continue

3. Is this permanent knowledge?
   YES → Create in Docs/ folder ✅
   NO → Use /temp/, DELETE after

4. OK to create
   ✅ Persistent → Docs/filename.md
   ❌ Temporary → /temp/filename.md (delete)
```

---

## ❌ Don't Create

```
TEMPORARY ANALYSIS
├── DEBUG_NOTES.md
├── ANALYSIS_REPORT.md
├── IMPLEMENTATION_PLAN.md
├── VERIFICATION_REPORT.md
└── Use /temp/, DELETE after use

SCATTERED DOCUMENTATION
├── FEATURE_PART1.md
├── FEATURE_PART2.md
├── FEATURE_PART3.md
└── Consolidate into single file

ROOT CLUTTER
├── ROOT/TEMPORARY.md
├── ROOT/ANALYSIS.md
├── ROOT/PLANNING.md
└── Only README.md, config files in root
```

---

## ✅ DO Create (In Docs/ only)

```
PERMANENT DOCUMENTATION
├── Docs/ARCHITECTURE.md          ✅ Needed by developers
├── Docs/API_REFERENCE.md         ✅ External documentation
├── Docs/MIGRATION_GUIDE.md       ✅ Permanent knowledge
├── Docs/features/
│   ├── FEATURE_NAME.md           ✅ One per feature
│   └── INDEX.md                  ✅ Updated with entry
└── Keep root clean, all docs in Docs/
```

---

## 📋 Before Committing

Check:
- ❌ Is this .md file in root? → Move to Docs/
- ❌ Is this temporary analysis? → Delete it
- ❌ Is this duplicate content? → Consolidate
- ✅ Is index updated? → Add entry if new file
- ✅ Is root clean? → Only README, config files

---

## 🚫 Anti-Patterns

| Pattern | ❌ Why | ✅ Instead |
|---------|--------|-----------|
| Create 1 .md per task | Clutter | Add to existing guide |
| Leave temp files | Pollution | Delete after use |
| Create in root | Mess | Create in Docs/ |
| Duplicate docs | Inconsistency | Single source of truth |
| Analysis reports | Temporary | Use /temp/, delete |

---

## 🎯 Golden Rules

1. **Check existing first** - Before creating new
2. **Use temp for analysis** - Never permanent commits
3. **Keep root clean** - Only essential files
4. **Update indices** - When adding permanent docs
5. **Consolidate docs** - One file per feature/topic

---

## 🔗 References

**Updated in both repos:**
- `c:\PROJECTS\Water-Balance-Application\.github\copilot-instructions.md`
- `d:\Projects\dashboard_waterbalance\.github\copilot-instructions.md`

**Section**: `🗂️ Repository Hygiene (STRICT)`

---

**Remember**: Less is more. Document in code. Consolidate guides. Keep repositories clean.

