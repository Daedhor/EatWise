"""Initialize SQLite database with recipes, ingredients, and steps."""
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL,
            text TEXT NOT NULL,
            PRIMARY KEY (recipe_id, sort_order),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_steps (
            recipe_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            step_text TEXT NOT NULL,
            PRIMARY KEY (recipe_id, step_order),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM recipes")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO recipes (id, name, meal_type, cook_time, needs_pan, needs_oven, needs_blender)
            VALUES (1, 'Scrambled eggs with toast', 'breakfast', 10, 1, 0, 0)
        """)

    # Ингредиенты и шаги для рецепта 1 (добавляем, если ещё нет)
    cur.execute("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = 1")
    if cur.fetchone()[0] == 0:
        ingredients = [
            (1, 1, "2 яйца"),
            (1, 2, "1 кусок хлеба"),
            (1, 3, "Соль"),
            (1, 4, "Масло"),
        ]
        cur.executemany(
            "INSERT INTO recipe_ingredients (recipe_id, sort_order, text) VALUES (?, ?, ?)",
            ingredients,
        )
    cur.execute("SELECT COUNT(*) FROM recipe_steps WHERE recipe_id = 1")
    if cur.fetchone()[0] == 0:
        steps = [
            (1, 1, "Разогреть сковороду"),
            (1, 2, "Взбить яйца"),
            (1, 3, "Приготовить омлет"),
            (1, 4, "Поджарить хлеб"),
        ]
        cur.executemany(
            "INSERT INTO recipe_steps (recipe_id, step_order, step_text) VALUES (?, ?, ?)",
            steps,
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
