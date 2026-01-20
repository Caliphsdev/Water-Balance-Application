# Quick Reference: Comment Guidelines

**TL;DR:** Every code change MUST include proper comments or will be REJECTED.

---

## 📝 Quick Comment Template

### Function
```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """Short description (LABEL - e.g., PRIMARY CALCULATOR).
    
    Longer explanation:
    - What it does
    - When to use it
    - Key concepts
    
    Args:
        param1: What this parameter is
        param2: What this parameter is
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this exception happens
    
    Example:
        result = function_name(value1, value2)
    """
```

### Class
```python
class ClassName:
    """Purpose (LABEL - e.g., CORE VALIDATOR).
    
    Multi-line explanation:
    - Main responsibilities
    - Key methods
    - State management
    """
```

### Complex Logic
```python
# Business rule: Explain WHY this logic exists
# Example: Cache results to avoid expensive file I/O
# This improves performance by 10x
cache_key = f"{date}_{facility}"
```

---

## ✅ Checklist for Every Code Change

- [ ] Function has docstring (purpose, args, returns)
- [ ] Complex logic has inline comments (WHY not WHAT)
- [ ] Cache usage is explained (key, TTL, invalidation)
- [ ] Data sources are clear (which Excel/DB, table names)
- [ ] Excel file type is specified (Meter Readings vs Flow Diagram)
- [ ] Business rules are explained
- [ ] Example usage provided
- [ ] Commit message mentions comment updates

---

## ❌ What Gets REJECTED

❌ Code without docstrings  
❌ Functions with no parameter explanations  
❌ Complex logic with no WHY comments  
❌ Unclear data source information  
❌ Missing Excel file distinction  
❌ Cache usage without strategy docs  
❌ Commit messages that don't mention comments  

---

## 📍 Where Comments Go

| Item | Required | Example |
|------|----------|---------|
| Module | YES | File header docstring |
| Class | YES | Class-level docstring |
| Function | YES | Function docstring with args/returns |
| Method | YES | Method docstring |
| Complex loop | YES | Inline comment explaining logic |
| Cache | YES | Explain key, TTL, invalidation |
| Excel/DB query | YES | Specify file/table/column names |
| Business rule | YES | Comment explaining WHY |

---

## 🔑 Key Distinctions

### Excel Files (ALWAYS SPECIFY)
```
✅ GOOD: Load from Meter Readings Excel "Meter Readings" sheet, Column B
✅ GOOD: Load from Flow Diagram Excel "Flows_UG2N" sheet
❌ BAD: Load from Excel (which one?)
```

### Comments
```
✅ WHY: Cache results by (date, facility) to avoid re-reading Excel (perf)
❌ WHAT: Cache results by (date, facility)
```

### Parameters
```
✅ GOOD: facility_code: Unique facility ID (e.g., 'UG2N', 'OLDTSF')
❌ BAD: facility_code: Facility code
```

---

## 🚀 Common Scenarios

### New Function
```
MUST HAVE:
- Full docstring (purpose, args, returns)
- Inline comments for complex logic
- Example usage
- Data source if reading from Excel/DB
```

### Existing Function Change
```
MUST UPDATE:
- Docstring if signature changed
- Inline comments if logic changed
- Cache docs if strategy changed
```

### Complex Logic
```
MUST INCLUDE:
- Comment explaining WHY this logic exists
- Business rule or constraint
- Example of when this path is taken
- Any assumptions or limitations
```

### Excel/DB Query
```
MUST SPECIFY:
- Which Excel file (full path, sheet name)
- Column names and what they contain
- Any data transformations
- Distinguish between Meter Readings vs Flow Diagram
```

### Cache Usage
```
MUST DOCUMENT:
- Cache key format (e.g., "{date}_{facility}")
- TTL (time to live)
- Invalidation trigger (when to clear)
- Why caching improves performance
```

---

## 🎯 Enforcement

### Code Review Will Check:
✅ Every function has docstring  
✅ Parameters are explained  
✅ Return values are documented  
✅ Complex logic is commented  
✅ Data sources are clear  
✅ Excel files are specified  
✅ Cache strategy is explained  
✅ Examples are provided  
✅ Commit message mentions comments  

### Will REJECT If:
❌ Missing docstring  
❌ No parameter explanations  
❌ Complex logic uncommented  
❌ Data source unclear  
❌ Excel file not specified  
❌ Cache usage undocumented  
❌ Commit message doesn't mention comments  

---

## 📚 Full Documentation

For detailed rules, see:
- **Rules:** `.github/instructions/COMMENT_ENFORCEMENT_RULES.md`
- **Summary:** `docs/COMMENT_UPDATES_SUMMARY.md`
- **Architecture:** `.github/copilot-instructions.md`

---

## 💡 Tips

1. **Start with docstring** - Write it before/during implementation
2. **Use examples** - Show how to call the function
3. **Explain business logic** - Not just the code mechanics
4. **Be specific** - "Meter Readings Excel" not just "Excel"
5. **Think like a newcomer** - Would you understand this without asking?

---

**Remember:** Comments are part of the code. No comments = incomplete code = REJECTED.

*Every line of code tells a story. Make sure your comments tell the right one.*
