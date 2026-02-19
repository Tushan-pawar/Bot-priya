"""Long-term context compression and summarization."""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tiktoken
from ..utils.logging import logger
from ..memory.persistent_memory import memory_system

class ContextCompressor:
    """Compresses long conversation contexts into summaries."""
    
    def __init__(self, max_tokens: int = 4000, summary_ratio: float = 0.3):
        self.max_tokens = max_tokens
        self.summary_ratio = summary_ratio
        self.encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))
    
    async def compress_context(
        self, 
        user_id: str, 
        messages: List[Dict[str, str]],
        server_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Compress messages if they exceed token limit."""
        total_tokens = sum(self.count_tokens(msg.get('content', '')) for msg in messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        logger.info(f"Compressing context: {total_tokens} > {self.max_tokens} tokens")
        
        system_msg = [m for m in messages if m.get('role') == 'system']
        user_msgs = [m for m in messages if m.get('role') != 'system']
        
        if len(user_msgs) <= 2:
            return messages
        
        recent_msgs = user_msgs[-2:]
        old_msgs = user_msgs[:-2]
        
        old_text = '\n'.join([f"{m['role']}: {m['content']}" for m in old_msgs])
        summary = await self._create_summary(old_text)
        
        if summary:
            await self._save_summary(user_id, summary, server_id)
            summary_msg = {'role': 'system', 'content': f"Previous conversation: {summary}"}
            return system_msg + [summary_msg] + recent_msgs
        
        return system_msg + recent_msgs
    
    def _split_context(self, context: str) -> List[str]:
        """Split context into logical chunks."""
        # Split by conversation turns or time periods
        chunks = []
        current_chunk = ""
        
        lines = context.split('\n')
        for line in lines:
            current_chunk += line + '\n'
            
            # Split on conversation boundaries
            if (line.strip().endswith(('.', '!', '?')) and 
                self.count_tokens(current_chunk) > 500):
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _create_summary(self, text: str) -> Optional[str]:
        """Create summary of text chunk."""
        try:
            from ..models.llm_fallback import llm_system
            
            summary_prompt = f"""Summarize this conversation chunk in 2-3 sentences, focusing on:
1. Key topics discussed
2. Important information shared
3. User preferences or context

Conversation:
{text}

Summary:"""
            
            messages = [{"role": "user", "content": summary_prompt}]
            summary = await llm_system.generate_response(messages, temperature=0.3)
            
            return summary.strip() if summary else None
            
        except Exception as e:
            logger.error(f"Failed to create summary: {e}")
            return None
    
    async def _save_summary(
        self, 
        user_id: str, 
        summary: str, 
        server_id: Optional[str] = None
    ):
        """Save summary to memory system."""
        await memory_system.save_memory(
            user_id=user_id,
            content=f"[SUMMARY] {summary}",
            server_id=server_id,
            metadata={"type": "summary", "created_at": datetime.now().isoformat()},
            importance=0.7
        )
    
    async def _get_existing_summaries(self, user_id: str, server_id: Optional[str] = None) -> List[str]:
        """Get existing summaries for user."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._fetch_summaries, user_id, server_id)
        except Exception as e:
            logger.error(f"Failed to get summaries: {e}")
            return []
    
    def _fetch_summaries(self, user_id: str, server_id: Optional[str]) -> List[str]:
        """Fetch summaries from database."""
        import sqlite3
        with sqlite3.connect(memory_system.db_path) as conn:
            query = "SELECT content FROM memories WHERE user_id = ? AND content LIKE '[SUMMARY]%'"
            params = [user_id]
            if server_id:
                query += " AND (server_id = ? OR server_id IS NULL)"
                params.append(server_id)
            query += " ORDER BY timestamp DESC LIMIT 5"
            cursor = conn.execute(query, params)
            return [row[0][9:].strip() for row in cursor.fetchall() if row[0].startswith("[SUMMARY]")]
    
    async def cleanup_old_summaries(self, days: int = 30):
        """Clean up old summaries."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._cleanup_summaries, days)
            logger.info("Cleaned up old summaries")
        except Exception as e:
            logger.error(f"Failed to cleanup summaries: {e}")
    
    def _cleanup_summaries(self, days: int):
        """Delete old summaries from database."""
        import sqlite3
        with sqlite3.connect(memory_system.db_path) as conn:
            conn.execute(
                "DELETE FROM memories WHERE content LIKE '[SUMMARY]%' AND timestamp < datetime('now', '-{} days')".format(days)
            )

# Global instance
context_compressor = ContextCompressor()