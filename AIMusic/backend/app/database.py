import aiosqlite
from app.config import settings

async def get_db():
    db = await aiosqlite.connect(settings.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            parent_version_id INTEGER,
            note TEXT,
            session_id TEXT NOT NULL
        )
    """)
    await db.commit()
    await db.close()

async def save_prompt_version(step: str, type: str, content: str, session_id: str, note: str = "", parent_version_id: int = None):
    db = await get_db()
    await db.execute(
        "INSERT INTO prompt_versions (step, type, content, session_id, note, parent_version_id) VALUES (?, ?, ?, ?, ?, ?)",
        (step, type, content, session_id, note, parent_version_id)
    )
    await db.commit()
    await db.close()

async def get_prompt_versions(session_id: str, step: str = None):
    db = await get_db()
    if step:
        cursor = await db.execute(
            "SELECT * FROM prompt_versions WHERE session_id = ? AND step = ? ORDER BY timestamp DESC",
            (session_id, step)
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM prompt_versions WHERE session_id = ? ORDER BY timestamp DESC",
            (session_id,)
        )
    rows = await cursor.fetchall()
    result = [dict(row) for row in rows]
    await db.close()
    return result
