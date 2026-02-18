"""Backup and restore system for memory and vector database."""
import asyncio
import json
import gzip
import pickle
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import sqlite3
import numpy as np
from ..utils.logging import logger
from ..memory.persistent_memory import memory_system

class BackupRestoreSystem:
    """Handles backup and restore of memory and vector data."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_full_backup(self, backup_name: Optional[str] = None) -> str:
        """Create full backup of memory system."""
        if not backup_name:
            backup_name = f"priya_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            logger.info(f"Creating full backup: {backup_name}")
            
            # Backup SQLite database
            await self._backup_database(backup_path)
            
            # Backup FAISS index
            await self._backup_vector_index(backup_path)
            
            # Backup configuration and metadata
            await self._backup_metadata(backup_path)
            
            # Create compressed archive
            archive_path = await self._create_archive(backup_path, backup_name)
            
            # Cleanup temporary directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup completed: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Cleanup on failure
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    async def _backup_database(self, backup_path: Path):
        """Backup SQLite database."""
        db_backup_path = backup_path / "memory.db"
        
        # Copy database file
        shutil.copy2(memory_system.db_path, db_backup_path)
        
        # Export as JSON for portability
        json_backup_path = backup_path / "memory_export.json"
        
        with sqlite3.connect(memory_system.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, user_id, server_id, content, metadata, timestamp, importance
                FROM memories
                ORDER BY timestamp
            """)
            
            memories = []
            for row in cursor.fetchall():
                memory_id, user_id, server_id, content, metadata, timestamp, importance = row
                memories.append({
                    "id": memory_id,
                    "user_id": user_id,
                    "server_id": server_id,
                    "content": content,
                    "metadata": json.loads(metadata) if metadata else {},
                    "timestamp": timestamp,
                    "importance": importance
                })
            
            # Save as compressed JSON
            with gzip.open(json_backup_path, 'wt', encoding='utf-8') as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Database backup completed: {len(memories)} memories")
    
    async def _backup_vector_index(self, backup_path: Path):
        """Backup FAISS vector index."""
        try:
            import faiss
            
            # Save FAISS index
            index_path = backup_path / "faiss_index.bin"
            faiss.write_index(memory_system.index, str(index_path))
            
            # Save memory mapping
            mapping_path = backup_path / "memory_mapping.pkl"
            with open(mapping_path, 'wb') as f:
                pickle.dump(memory_system.memory_map, f)
            
            logger.info("Vector index backup completed")
            
        except Exception as e:
            logger.error(f"Vector index backup failed: {e}")
            # Create empty files to maintain backup structure
            (backup_path / "faiss_index.bin").touch()
            (backup_path / "memory_mapping.pkl").touch()
    
    async def _backup_metadata(self, backup_path: Path):
        """Backup system metadata."""
        metadata = {
            "backup_created": datetime.now().isoformat(),
            "system_version": "2.0.0",
            "vector_dimension": memory_system.vector_dim,
            "total_memories": memory_system.index.ntotal if hasattr(memory_system, 'index') else 0,
            "encoder_model": "all-MiniLM-L6-v2"
        }
        
        metadata_path = backup_path / "backup_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Metadata backup completed")
    
    async def _create_archive(self, backup_path: Path, backup_name: str) -> Path:
        """Create compressed archive of backup."""
        archive_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        # Create tar.gz archive
        import tarfile
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_name)
        
        return archive_path
    
    async def restore_from_backup(self, backup_path: str, restore_vectors: bool = True) -> bool:
        """Restore from backup file."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            logger.info(f"Restoring from backup: {backup_path}")
            
            # Extract archive
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)
            
            import tarfile
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find extracted directory
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                logger.error("No directories found in backup archive")
                return False
            
            restore_dir = extracted_dirs[0]
            
            # Restore database
            await self._restore_database(restore_dir)
            
            # Restore vector index
            if restore_vectors:
                await self._restore_vector_index(restore_dir)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            logger.info("Restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    async def _restore_database(self, restore_dir: Path):
        """Restore SQLite database."""
        # Check for JSON export first (more portable)
        json_backup = restore_dir / "memory_export.json"
        db_backup = restore_dir / "memory.db"
        
        if json_backup.exists():
            logger.info("Restoring from JSON export")
            
            # Clear existing database
            with sqlite3.connect(memory_system.db_path) as conn:
                conn.execute("DELETE FROM memories")
            
            # Load from JSON
            with gzip.open(json_backup, 'rt', encoding='utf-8') as f:
                memories = json.load(f)
            
            # Insert memories
            with sqlite3.connect(memory_system.db_path) as conn:
                for memory in memories:
                    # Generate embedding for restored memory
                    embedding = memory_system.encoder.encode([memory['content']])[0]
                    embedding_blob = embedding.tobytes()
                    
                    conn.execute("""
                        INSERT INTO memories (user_id, server_id, content, embedding, metadata, timestamp, importance)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        memory['user_id'],
                        memory['server_id'],
                        memory['content'],
                        embedding_blob,
                        json.dumps(memory['metadata']),
                        memory['timestamp'],
                        memory['importance']
                    ))
            
            logger.info(f"Restored {len(memories)} memories from JSON")
            
        elif db_backup.exists():
            logger.info("Restoring from database backup")
            
            # Replace database file
            shutil.copy2(db_backup, memory_system.db_path)
            
            logger.info("Database restored from backup file")
        
        else:
            logger.error("No database backup found")
    
    async def _restore_vector_index(self, restore_dir: Path):
        """Restore FAISS vector index."""
        try:
            import faiss
            
            index_path = restore_dir / "faiss_index.bin"
            mapping_path = restore_dir / "memory_mapping.pkl"
            
            if index_path.exists() and mapping_path.exists():
                # Load FAISS index
                memory_system.index = faiss.read_index(str(index_path))
                
                # Load memory mapping
                with open(mapping_path, 'rb') as f:
                    memory_system.memory_map = pickle.load(f)
                
                logger.info("Vector index restored successfully")
            else:
                logger.warning("Vector index backup not found, rebuilding...")
                # Rebuild index from database
                memory_system.index = faiss.IndexFlatIP(memory_system.vector_dim)
                memory_system.memory_map = {}
                memory_system._load_vectors()
                
        except Exception as e:
            logger.error(f"Vector index restore failed: {e}")
            # Rebuild index as fallback
            memory_system.index = faiss.IndexFlatIP(memory_system.vector_dim)
            memory_system.memory_map = {}
            memory_system._load_vectors()
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.stem,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Error reading backup {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    async def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup file."""
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        if backup_file.exists():
            backup_file.unlink()
            logger.info(f"Deleted backup: {backup_name}")
            return True
        else:
            logger.error(f"Backup not found: {backup_name}")
            return False
    
    async def export_user_data(self, user_id: str, output_path: str) -> bool:
        """Export specific user's data."""
        try:
            with sqlite3.connect(memory_system.db_path) as conn:
                cursor = conn.execute("""
                    SELECT content, metadata, timestamp, importance
                    FROM memories
                    WHERE user_id = ?
                    ORDER BY timestamp
                """, (user_id,))
                
                user_memories = []
                for row in cursor.fetchall():
                    content, metadata, timestamp, importance = row
                    user_memories.append({
                        "content": content,
                        "metadata": json.loads(metadata) if metadata else {},
                        "timestamp": timestamp,
                        "importance": importance
                    })
                
                # Export to JSON
                export_data = {
                    "user_id": user_id,
                    "export_date": datetime.now().isoformat(),
                    "total_memories": len(user_memories),
                    "memories": user_memories
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Exported {len(user_memories)} memories for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"User data export failed: {e}")
            return False

# Global instance
backup_system = BackupRestoreSystem()