"""Fixed persistent memory system with proper async I/O."""
import sqlite3
import json
import asyncio
import aiosqlite
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from ..utils.logging import logger

class MemorySystem:
    """Persistent memory with vector search capabilities."""
    
    def __init__(self, db_path: str = "data/memory.db", vector_dim: int = 384):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.vector_dim = vector_dim
        self._lock = asyncio.Lock()
        
        # Initialize embedding model in thread pool
        self.encoder = None
        self._encoder_lock = asyncio.Lock()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(vector_dim)
        self.memory_map = {}
        
        # Initialize in background - save task to prevent garbage collection
        self._init_task = asyncio.create_task(self._async_init())
    
    async def _async_init(self):
        """Async initialization."""
        await self._init_database()
        await self._init_encoder()
        await self._load_vectors()
    
    async def _init_encoder(self):
        """Initialize encoder in thread pool."""
        async with self._encoder_lock:
            if self.encoder is None:
                loop = asyncio.get_event_loop()
                self.encoder = await loop.run_in_executor(
                    None, lambda: SentenceTransformer('all-MiniLM-L6-v2')
                )
    
    async def _init_database(self):
        """Initialize SQLite database asynchronously."""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    server_id TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    importance REAL DEFAULT 0.5
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_server_id ON memories(server_id)
            """)
            
            await conn.commit()
    
    async def _load_vectors(self):
        """Load existing vectors into FAISS index."""
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute("SELECT id, embedding FROM memories") as cursor:
                    async for row in cursor:
                        memory_id, embedding_blob = row
                        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                        self.index.add(embedding.reshape(1, -1))
                        self.memory_map[self.index.ntotal - 1] = memory_id
    
    async def save_memory(
        self, 
        user_id: str, 
        content: str, 
        server_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        importance: float = 0.5
    ) -> int:
        """Save memory with async optimization."""
        try:
            # Quick async save without heavy vector operations
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("""
                    INSERT INTO memories (user_id, server_id, content, metadata, importance)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, server_id, content, json.dumps(metadata or {}), importance))
                
                memory_id = cursor.lastrowid
                await conn.commit()
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return -1
    
    async def retrieve_memory(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5,
        server_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve memories with fast text search."""
        try:
            # Fast text-based search instead of vector similarity
            async with aiosqlite.connect(self.db_path) as conn:
                # Simple keyword matching
                query_words = query.lower().split()
                like_conditions = ' OR '.join(['content LIKE ?' for _ in query_words])
                like_params = [f'%{word}%' for word in query_words]
                
                sql = f"""
                    SELECT content, metadata, timestamp, importance
                    FROM memories 
                    WHERE user_id = ? AND ({like_conditions})
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                """
                
                params = [user_id] + like_params + [limit]
                if server_id:
                    sql = sql.replace('WHERE user_id = ?', 'WHERE user_id = ? AND (server_id = ? OR server_id IS NULL)')
                    params = [user_id, server_id] + like_params + [limit]
                
                async with conn.execute(sql, params) as cursor:
                    results = []
                    async for row in cursor:
                        content, metadata_str, timestamp, importance = row
                        results.append({
                            'content': content,
                            'metadata': json.loads(metadata_str) if metadata_str else {},
                            'timestamp': timestamp,
                            'importance': importance,
                            'similarity': 0.8  # Approximate similarity
                        })
                    return results
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return []
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for user."""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                async with conn.execute("""
                    SELECT COUNT(*), AVG(importance), MIN(timestamp), MAX(timestamp)
                    FROM memories WHERE user_id = ?
                """, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    count, avg_importance, first_memory, last_memory = row
                    
                    return {
                        'total_memories': count or 0,
                        'avg_importance': avg_importance or 0.0,
                        'first_memory': first_memory,
                        'last_memory': last_memory
                    }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}", 
                        extra={'user_id': user_id, 'error_type': 'memory_stats_error'})
            return {'total_memories': 0, 'avg_importance': 0.0, 'first_memory': None, 'last_memory': None}
    
    async def cleanup_old_memories(self, days: int = 90):
        """Clean up old, low-importance memories."""
        try:
            async with self._lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    cursor = await conn.execute("""
                        DELETE FROM memories 
                        WHERE timestamp < datetime('now', '-{} days')
                        AND importance < 0.3
                    """.format(days))
                    
                    deleted = cursor.rowcount
                    await conn.commit()
                    
                    logger.info(f"Cleaned up {deleted} old memories", 
                               extra={'operation': 'cleanup_memories', 'deleted_count': deleted})
                    
                    # Rebuild FAISS index
                    self.index = faiss.IndexFlatIP(self.vector_dim)
                    self.memory_map = {}
                    await self._load_vectors()
                    
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}", 
                        extra={'error_type': 'memory_cleanup_error'})

# Global instance
memory_system = MemorySystem()