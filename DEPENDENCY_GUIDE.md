# Dependency Management Guide

This guide ensures you never face dependency conflicts again.

## 🎯 Quick Reference

### Critical Version Constraints

| Package | Version | Why | Never Do |
|---------|---------|-----|----------|
| `openai` | `>=2.26.0` | Fixes "proxies" error with langchain-openai | ❌ Don't use `<2.0.0` |
| `pydantic` | `>=2.7.4` | Required by langchain 1.2.15+ | ❌ Don't use `==2.7.1` |
| `typing-extensions` | `>=4.14.1` | Required by pydantic >=2.7.4 | ❌ Don't pin exact version like `==4.9.0` |
| `uvicorn[standard]` | `>=0.30.1` | Includes production features | ❌ Don't specify both `uvicorn` and `uvicorn[standard]` |
| `faiss-cpu` | `>=1.7.4` | Python 3.11 compatible | ℹ️ Use `>=1.9.0` for Python 3.13+ |

## 🔧 Installation Commands

### Fresh Install
```bash
pip install -r requiterment.txt
```

### Clean Reinstall (if issues occur)
```bash
pip uninstall -y langchain langchain-openai langchain-community openai pydantic
pip install -r requiterment.txt
```

### Update Specific Package
```bash
# Always check requiterment.txt constraints first!
pip install "package_name>=min_version,<max_version"
```

## ⚠️ Common Errors & Solutions

### Error: "proxies parameter" or "unexpected keyword argument 'proxies'"

**Cause:** Using `openai<2.0.0` with `langchain-openai>=0.1.20`

**Solution:**
```bash
pip uninstall openai -y
pip install "openai>=2.26.0,<3.0.0"
```

**Prevention:** Always use `openai>=2.26.0` in requirements

---

### Error: Pydantic version conflict

**Cause:** Using `pydantic<2.7.4` with newer langchain

**Solution:**
```bash
pip install "pydantic>=2.7.4,<3.0.0"
```

**Prevention:** Never pin pydantic to versions below 2.7.4

---

### Error: typing-extensions conflict

**Cause:** Pinning exact version like `typing-extensions==4.9.0`

**Solution:**
```bash
pip install "typing-extensions>=4.14.1"
```

**Prevention:** Always use `>=4.14.1`, never exact version

---

### Error: uvicorn dependency conflict

**Cause:** Specifying both `uvicorn==X.X.X` and `uvicorn[standard]==X.X.X`

**Solution:**
```bash
# Only use uvicorn[standard]
pip install "uvicorn[standard]>=0.30.1"
```

**Prevention:** Only specify `uvicorn[standard]`, not both

---

### Error: Cannot find faiss-cpu version

**Cause:** Wrong Python version (3.13+ needs newer faiss)

**Solution:**
```bash
# For Python 3.11
pip install "faiss-cpu>=1.7.4,<2.0.0"

# For Python 3.13+
pip install "faiss-cpu>=1.9.0,<2.0.0"
```

## 📋 Dependency Chain Explained

```
FastAPI Application
├── fastapi (>=0.111.0)
│   ├── pydantic (>=2.7.4) ← Must be 2.7.4+ for langchain
│   │   └── typing-extensions (>=4.14.1) ← Must be 4.14.1+
│   └── uvicorn[standard] (>=0.30.1)
│
├── LangChain Stack
│   ├── langchain (>=0.2.0)
│   │   └── pydantic (>=2.7.4)
│   ├── langchain-openai (>=0.1.0)
│   │   └── openai (>=2.26.0) ← CRITICAL: Must be 2.x
│   ├── langgraph (>=0.0.40)
│   └── langsmith (>=0.1.0) ← Optional tracing
│
└── Vector Store
    ├── faiss-cpu (>=1.7.4)
    └── sentence-transformers (>=2.3.0)
```

## 🚀 Best Practices

### 1. Always Use Version Ranges
```bash
✅ GOOD: package>=1.0.0,<2.0.0
❌ BAD:  package==1.0.0
```

### 2. Test After Updates
```bash
# After updating requirements
pip install -r requiterment.txt
python -c "from app.agenticAI.llm_Model import LLMFactory; print('✅ Imports OK')"
uvicorn main:app --reload
```

### 3. Check Compatibility Before Adding New Packages
```bash
# Check what versions are compatible
pip install package_name
pip show package_name

# Check dependencies
pip show package_name | grep Requires
```

### 4. Document Why You Need Specific Versions
Always add comments in `requiterment.txt` explaining constraints:
```txt
# CRITICAL: openai>=2.26.0 fixes proxies error with langchain-openai
openai>=2.26.0,<3.0.0
```

## 🔍 Debugging Dependency Issues

### Step 1: Check Current Versions
```bash
pip show openai langchain-openai pydantic typing-extensions
```

### Step 2: Check What's Installed
```bash
pip list | grep -E "openai|langchain|pydantic|typing"
```

### Step 3: Check Conflicts
```bash
pip check
```

### Step 4: See Dependency Tree
```bash
pip install pipdeptree
pipdeptree -p langchain-openai
```

## 📝 When Adding New Dependencies

1. **Check compatibility** with existing packages
2. **Use version ranges** not exact versions
3. **Test installation** in clean environment
4. **Document the constraint** in requiterment.txt
5. **Update this guide** if it's a critical dependency

## 🎓 Understanding Version Specifiers

| Specifier | Meaning | Example | Use Case |
|-----------|---------|---------|----------|
| `==1.0.0` | Exact version | `pydantic==2.7.4` | ❌ Avoid (causes conflicts) |
| `>=1.0.0` | At least | `openai>=2.26.0` | ✅ Good for minimum requirements |
| `<2.0.0` | Less than | `openai<3.0.0` | ✅ Good for preventing breaking changes |
| `>=1.0,<2.0` | Range | `openai>=2.26.0,<3.0.0` | ✅ Best practice |
| `~=1.0.0` | Compatible | `package~=1.0.0` | ⚠️ Use with caution |

## 🆘 Emergency Fix

If everything breaks:

```bash
# 1. Backup current environment
pip freeze > backup_requirements.txt

# 2. Uninstall problematic packages
pip uninstall -y langchain langchain-openai langchain-community \
                  openai pydantic typing-extensions

# 3. Reinstall from clean requirements
pip install -r requiterment.txt

# 4. Verify
python -c "from app.agenticAI.llm_Model import LLMFactory; print('✅ OK')"
uvicorn main:app --reload
```

## 📞 Still Having Issues?

1. Check this guide first
2. Read error message carefully
3. Check `requiterment.txt` comments
4. Run `pip check` to see conflicts
5. Compare with working versions in this guide

---

**Last Updated:** After fixing all dependency conflicts
**Tested With:** Python 3.11, fastapi-crud environment
