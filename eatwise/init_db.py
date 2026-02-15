"""Initialize SQLite database with recipes, ingredients, and steps."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "recipes.db"


# Единицы измерения: id -> name (1–8 по ТЗ, 9–10 для совместимости с текущим рецептом)
UNITS = [
    (1, "г"),
    (2, "кг"),
    (3, "мл"),
    (4, "л"),
    (5, "ч.л."),
    (6, "ст.л."),
    (7, "по вкусу"),
    (8, "для жарки"),
    (9, "шт"),
    (10, "кусок"),
]
UNIT_NAME_TO_ID = {name: uid for uid, name in UNITS}


def _ensure_units(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='units'")
    if cur.fetchone() is None:
        cur.execute("CREATE TABLE units (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        cur.executemany("INSERT INTO units (id, name) VALUES (?, ?)", UNITS)
        return
    cur.execute("SELECT COUNT(*) FROM units")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO units (id, name) VALUES (?, ?)", UNITS)


def _create_ingredients_table(cur):
    cur.execute("""
        CREATE TABLE recipe_ingredients (
            recipe_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL,
            unit_id INTEGER NOT NULL,
            PRIMARY KEY (recipe_id, sort_order),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id),
            FOREIGN KEY (unit_id) REFERENCES units(id)
        )
    """)


def _insert_recipe1_ingredients(cur):
    # unit_id: шт=9, кусок=10, по вкусу=7, г=1
    ingredients = [
        (1, 1, "Яйца", 2.0, 9),
        (1, 2, "Хлеб", 1.0, 10),
        (1, 3, "Соль", None, 7),
        (1, 4, "Масло", 10.0, 1),
    ]
    cur.executemany(
        "INSERT INTO recipe_ingredients (recipe_id, sort_order, name, amount, unit_id) VALUES (?, ?, ?, ?, ?)",
        ingredients,
    )


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

    # Таблица единиц измерения (всегда создаём/пополняем первой)
    _ensure_units(cur)

    # Ингредиенты: схема с unit_id или миграция со старой (unit TEXT / text)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipe_ingredients'")
    table_exists = cur.fetchone() is not None
    if table_exists:
        cur.execute("PRAGMA table_info(recipe_ingredients)")
        columns = [row[1] for row in cur.fetchall()]
        if "unit_id" in columns:
            # Уже новая схема
            cur.execute("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = 1")
            if cur.fetchone()[0] == 0:
                _insert_recipe1_ingredients(cur)
        else:
            # Старая схема: unit (TEXT) или text
            migrated = []
            if "unit" in columns:
                cur.execute(
                    "SELECT recipe_id, sort_order, name, amount, unit FROM recipe_ingredients ORDER BY recipe_id, sort_order"
                )
                for row in cur.fetchall():
                    rid, order, name, amount, unit = row
                    unit_id = UNIT_NAME_TO_ID.get((unit or "").strip(), 7)
                    migrated.append((rid, order, name, amount, unit_id))
            else:
                cur.execute(
                    "SELECT recipe_id, sort_order, text FROM recipe_ingredients ORDER BY recipe_id, sort_order"
                )
                m1 = {1: (1, 1, "Яйца", 2.0, 9), 2: (1, 2, "Хлеб", 1.0, 10), 3: (1, 3, "Соль", None, 7), 4: (1, 4, "Масло", 10.0, 1)}
                for rid, order, text in cur.fetchall():
                    if rid == 1:
                        migrated.append(m1.get(order, (rid, order, text, None, 7)))
                    else:
                        migrated.append((rid, order, text, None, 7))
            cur.execute("DROP TABLE recipe_ingredients")
            _create_ingredients_table(cur)
            for row in migrated:
                cur.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, sort_order, name, amount, unit_id) VALUES (?, ?, ?, ?, ?)",
                    row,
                )
    else:
        _create_ingredients_table(cur)
        _insert_recipe1_ingredients(cur)
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
