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
        
        # Initialize in background
        asyncio.create_task(self._async_init())
    
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
                    embedding BLOB NOT NULL,
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
        """Save memory with vector embedding."""
        try:
            await self._init_encoder()
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, lambda: self.encoder.encode([content])[0]
            )
            embedding_blob = embedding.tobytes()
            
            async with self._lock:
                # Save to database
                async with aiosqlite.connect(self.db_path) as conn:
                    cursor = await conn.execute("""
                        INSERT INTO memories (user_id, server_id, content, embedding, metadata, importance)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, server_id, content, embedding_blob, json.dumps(metadata or {}), importance))
                    
                    memory_id = cursor.lastrowid
                    await conn.commit()
                
                # Add to FAISS index
                self.index.add(embedding.reshape(1, -1))
                self.memory_map[self.index.ntotal - 1] = memory_id
            
            logger.info(f"Saved memory for user {user_id}: {content[:50]}...", 
                       extra={'user_id': user_id, 'operation': 'save_memory'})
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}", 
                        extra={'user_id': user_id, 'error_type': 'memory_save_error'})
            return -1
    
    async def retrieve_memory(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5,
        server_id: Optional[str] = None,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories using vector search."""
        try:
            await self._init_encoder()
            
            # Generate query embedding in thread pool
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None, lambda: self.encoder.encode([query])[0]
            )
            
            async with self._lock:
                # Search FAISS index
                similarities, indices = self.index.search(
                    query_embedding.reshape(1, -1), 
                    min(limit * 3, max(1, self.index.ntotal))
                )
                
                # Get memory IDs and filter by user/server
                memory_ids = []
                for i, similarity in zip(indices[0], similarities[0]):
                    if similarity >= min_similarity and i in self.memory_map:
                        memory_ids.append((self.memory_map[i], similarity))
                
                if not memory_ids:
                    return []
                
                # Fetch from database with filtering
                placeholders = ','.join('?' * len(memory_ids))
                query_sql = f"""
                    SELECT id, content, metadata, timestamp, importance
                    FROM memories 
                    WHERE id IN ({placeholders}) AND user_id = ?
                """
                params = [mid for mid, _ in memory_ids] + [user_id]
                
                if server_id:
                    query_sql += " AND (server_id = ? OR server_id IS NULL)"
                    params.append(server_id)
                
                query_sql += " ORDER BY importance DESC, timestamp DESC"
                
                async with aiosqlite.connect(self.db_path) as conn:
                    async with conn.execute(query_sql, params) as cursor:
                        results = []
                        async for row in cursor:
                            memory_id, content, metadata_str, timestamp, importance = row
                            
                            # Find similarity score
                            similarity = next(
                                (sim for mid, sim in memory_ids if mid == memory_id), 
                                0.0
                            )
                            
                            results.append({
                                'id': memory_id,
                                'content': content,
                                'metadata': json.loads(metadata_str) if metadata_str else {},
                                'timestamp': timestamp,
                                'importance': importance,
                                'similarity': float(similarity)
                            })
                        
                        return results[:limit]
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}", 
                        extra={'user_id': user_id, 'error_type': 'memory_retrieve_error'})
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