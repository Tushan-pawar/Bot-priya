"""Database migration: Add embedding column to memories table."""
import asyncio
import aiosqlite
from pathlib import Path

async def migrate_database():
    """Add embedding column if it doesn't exist."""
    db_path = Path("data/memory.db")
    
    if not db_path.exists():
        print("No database found - will be created on first run")
        return
    
    async with aiosqlite.connect(db_path) as conn:
        # Check if embedding column exists
        cursor = await conn.execute("PRAGMA table_info(memories)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'embedding' not in column_names:
            print("Adding embedding column...")
            await conn.execute("ALTER TABLE memories ADD COLUMN embedding BLOB")
            await conn.commit()
            print("✅ Migration complete!")
        else:
            print("✅ Database already up to date")

if __name__ == "__main__":
    asyncio.run(migrate_database())
