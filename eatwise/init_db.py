"""Initialize SQLite database with recipes table and one sample recipe."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "recipes.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            meal_type TEXT,
            cook_time INTEGER,
            needs_pan INTEGER,
            needs_oven INTEGER,
            needs_blender INTEGER
        )
    """)
    cur.execute("SELECT COUNT(*) FROM recipes")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO recipes (id, name, meal_type, cook_time, needs_pan, needs_oven, needs_blender)
            VALUES (1, 'Scrambled eggs with toast', 'breakfast', 10, 1, 0, 0)
        """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
