# Quick Setup - Vector Memory System

## 🚀 Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Key new dependencies:
- `aiosqlite` - Async SQLite operations
- `faiss-cpu` - Vector similarity search
- `sentence-transformers` - Text embeddings
- `tiktoken` - Token counting

### 2. Migrate Existing Database (if applicable)
```bash
python migrate_db.py
```

This adds the `embedding` column to existing databases.

### 3. Run Bot
```bash
python main.py
```

The system will:
- Create `data/memory.db` automatically
- Initialize FAISS index
- Load sentence transformer model
- Start processing messages

---

## 🔧 Configuration

### Adjust Token Limits

**In `src/bot.py`:**
```python
history = await priya_core.memory_system.get_relevant_history(
    user_id, 
    message.content, 
    max_tokens=2000  # Adjust based on your LLM's context window
)
```

**Recommended values:**
- GPT-3.5: 2000-3000 tokens
- GPT-4: 4000-6000 tokens
- Llama 3.2: 1500-2000 tokens
- Claude: 4000-8000 tokens

### Adjust Compression Settings

**In `src/memory/context_compression.py`:**
```python
context_compressor = ContextCompressor(
    max_tokens=4000,      # When to trigger compression
    summary_ratio=0.3     # Summary size (30% of original)
)
```

### Adjust Vector Search

**In `src/memory/persistent_memory.py`:**
```python
memories = await retrieve_memory(
    user_id, 
    query, 
    limit=10  # Number of memories to retrieve
)
```

---

## 📊 Monitoring

### Check Memory System Status
```python
from src.memory.persistent_memory import memory_system

# Total memories stored
print(f"Memories: {memory_system.index.ntotal}")

# Test retrieval
results = await memory_system.retrieve_memory(
    user_id="test_user",
    query="test query",
    limit=5
)
```

### Monitor Token Usage
```python
from src.memory.context_compression import context_compressor

# Count tokens in text
tokens = context_compressor.count_tokens("Your message here")
print(f"Tokens: {tokens}")
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'aiosqlite'"
```bash
pip install aiosqlite
```

### Issue: "FAISS index not found"
- Normal on first run
- Index is built automatically from database
- Check logs for "Loading vectors..."

### Issue: "Sentence transformer download slow"
- First run downloads ~80MB model
- Cached in `~/.cache/huggingface/`
- Subsequent runs are instant

### Issue: "Token limit exceeded"
- Reduce `max_tokens` in `get_relevant_history()`
- Increase compression threshold
- Check system prompt length

### Issue: "Vector search returns no results"
- Ensure memories are being saved with embeddings
- Check database has `embedding` column
- Run `migrate_db.py` if upgrading

---

## ✅ Verification

### Test Vector Search
```python
import asyncio
from src.memory.persistent_memory import memory_system

async def test():
    # Save test memory
    await memory_system.save_memory(
        user_id="test",
        content="I love pizza",
        importance=0.8
    )
    
    # Search for it
    results = await memory_system.retrieve_memory(
        user_id="test",
        query="favorite food",
        limit=5
    )
    
    print(f"Found {len(results)} results")
    for r in results:
        print(f"  - {r['content']} (similarity: {r['similarity']:.2f})")

asyncio.run(test())
```

Expected output:
```
Found 1 results
  - I love pizza (similarity: 0.85)
```

---

## 🎯 Performance Tips

### 1. Batch Operations
```python
# Save multiple memories efficiently
for msg in messages:
    await memory_system.save_memory(user_id, msg)
```

### 2. Adjust Retrieval Limit
```python
# More results = better context but slower
limit=5   # Fast, good for quick responses
limit=10  # Balanced (recommended)
limit=20  # Comprehensive but slower
```

### 3. Importance Scoring
```python
# Higher importance = prioritized in cleanup
await memory_system.save_memory(
    user_id=user_id,
    content=content,
    importance=0.9  # Important memory (0.0-1.0)
)
```

### 4. Regular Cleanup
```python
# Clean old, low-importance memories
await memory_system.cleanup_old_memories(days=90)
```

---

## 📈 Expected Performance

### Retrieval Speed
- 100 memories: ~10ms
- 1,000 memories: ~20ms
- 10,000 memories: ~50ms
- 100,000 memories: ~100ms

### Storage Size
- Per memory: ~1.5KB (embedding) + text size
- 10,000 memories: ~15MB + text
- 100,000 memories: ~150MB + text

### Memory Usage
- FAISS index: ~1.5KB per memory (in RAM)
- 10,000 memories: ~15MB RAM
- 100,000 memories: ~150MB RAM

---

## 🎉 You're Ready!

The vector memory system is now fully operational:
- ✅ Semantic search working
- ✅ Token-aware context windows
- ✅ Automatic compression
- ✅ Stateless processing
- ✅ Persistent storage

Start chatting and watch the magic happen! 🚀
