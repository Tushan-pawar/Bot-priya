# Memory System - Quick Reference

## 🚀 Quick Start
```bash
pip install -r requirements.txt
python migrate_db.py  # If upgrading
python main.py
```

## 💾 Save Memory
```python
from src.memory.persistent_memory import memory_system

await memory_system.save_memory(
    user_id="123",
    content="User loves pizza",
    importance=0.8  # 0.0-1.0
)
```

## 🔍 Search Memory
```python
results = await memory_system.retrieve_memory(
    user_id="123",
    query="favorite food",
    limit=5
)

for r in results:
    print(f"{r['content']} (similarity: {r['similarity']:.2f})")
```

## 📊 Get Context
```python
from src.core.personality import priya_core

history = await priya_core.memory_system.get_relevant_history(
    user_id="123",
    current_message="What's my favorite food?",
    max_tokens=2000
)
```

## 🗜️ Compress Context
```python
from src.memory.context_compression import context_compressor

compressed = await context_compressor.compress_context(
    user_id="123",
    messages=[...],  # List of message dicts
)
```

## 🔧 Configuration

### Token Limits
```python
# src/bot.py
max_tokens=2000  # Adjust for your LLM
```

### Vector Search
```python
# src/memory/persistent_memory.py
limit=10  # Number of memories to retrieve
```

### Compression
```python
# src/memory/context_compression.py
max_tokens=4000      # When to compress
summary_ratio=0.3    # Summary size
```

## 📈 Performance

| Operation | Speed | Notes |
|-----------|-------|-------|
| Save | ~50ms | Includes embedding |
| Search | ~30ms | 10k memories |
| Compress | ~2s | Uses LLM |

## 🐛 Debug

```python
# Check index size
print(memory_system.index.ntotal)

# Count tokens
tokens = context_compressor.count_tokens("text")

# Test search
results = await memory_system.retrieve_memory(
    user_id="test", query="test", limit=5
)
```

## ✅ Features

- ✅ Vector similarity search (FAISS)
- ✅ Semantic understanding
- ✅ Token-aware windows
- ✅ Automatic compression
- ✅ Stateless processing
- ✅ Persistent storage
- ✅ <100ms retrieval

## 📚 Docs

- [MEMORY_SYSTEM.md](MEMORY_SYSTEM.md) - Full architecture
- [MEMORY_SETUP.md](MEMORY_SETUP.md) - Setup guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Changes

## 🎯 Key Points

1. **Stateless** - No in-memory conversation storage
2. **Vector-powered** - Semantic search, not keywords
3. **Token-aware** - Respects context limits
4. **Auto-compress** - Handles long conversations
5. **Persistent** - Survives restarts

## 🚨 Common Issues

**No results from search?**
- Run `migrate_db.py`
- Check embeddings are being saved

**Token limit exceeded?**
- Reduce `max_tokens` parameter
- Increase compression threshold

**Slow first run?**
- Sentence transformer downloads ~80MB
- Cached after first run

## 💡 Tips

1. Higher importance = kept longer
2. More retrieval limit = better context
3. Lower max_tokens = faster responses
4. Regular cleanup = better performance

---

**Need help?** Check the full docs or open an issue!
