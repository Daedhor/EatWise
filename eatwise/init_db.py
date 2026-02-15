"""Initialize SQLite database with recipes, ingredients, and steps."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "recipes.db"
RECIPES_JSON_PATH = Path(__file__).parent / "recipes.json"

# Единицы измерения: id -> name
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
    (11, "зубчик"),
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
        return
    # Добавить новые единицы, если их ещё нет (например, зубчик)
    for uid, name in UNITS:
        cur.execute("SELECT 1 FROM units WHERE id = ?", (uid,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO units (id, name) VALUES (?, ?)", (uid, name))


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


def _load_recipes_from_json() -> list[dict]:
    """Загружает рецепты из recipes.json."""
    if not RECIPES_JSON_PATH.exists():
        return []
    with open(RECIPES_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _populate_fallback_recipe(cur):
    """Один рецепт по умолчанию, если recipes.json отсутствует."""
    cur.execute(
        """INSERT INTO recipes (name, meal_type, cook_time, needs_pan, needs_oven, needs_blender)
           VALUES ('Scrambled eggs with toast', 'breakfast', 10, 1, 0, 0)"""
    )
    rid = cur.lastrowid
    for i, (name, amount, unit_id) in enumerate(
        [("Яйца", 2.0, 9), ("Хлеб", 1.0, 10), ("Соль", None, 7), ("Масло", 10.0, 1)], start=1
    ):
        cur.execute(
            "INSERT INTO recipe_ingredients (recipe_id, sort_order, name, amount, unit_id) VALUES (?, ?, ?, ?, ?)",
            (rid, i, name, amount, unit_id),
        )
    for i, step in enumerate(
        ["Разогреть сковороду", "Взбить яйца", "Приготовить омлет", "Поджарить хлеб"], start=1
    ):
        cur.execute("INSERT INTO recipe_steps (recipe_id, step_order, step_text) VALUES (?, ?, ?)", (rid, i, step))


def _populate_from_json(cur):
    """Заполняет БД из recipes.json: рецепты, ингредиенты, шаги."""
    recipes = _load_recipes_from_json()
    if not recipes:
        _populate_fallback_recipe(cur)
        return
    for r in recipes:
        cur.execute(
            """INSERT INTO recipes (name, meal_type, cook_time, needs_pan, needs_oven, needs_blender)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                r["name"],
                r["meal_type"],
                r["cook_time"],
                1 if r.get("needs_pan") else 0,
                1 if r.get("needs_oven") else 0,
                1 if r.get("needs_blender") else 0,
            ),
        )
        recipe_id = cur.lastrowid
        for i, ing in enumerate(r.get("ingredients", []), start=1):
            unit_name = (ing.get("unit") or "").strip()
            unit_id = UNIT_NAME_TO_ID.get(unit_name, 7)
            cur.execute(
                "INSERT INTO recipe_ingredients (recipe_id, sort_order, name, amount, unit_id) VALUES (?, ?, ?, ?, ?)",
                (recipe_id, i, ing["name"], ing.get("amount"), unit_id),
            )
        for i, step in enumerate(r.get("steps", []), start=1):
            cur.execute(
                "INSERT INTO recipe_steps (recipe_id, step_order, step_text) VALUES (?, ?, ?)",
                (recipe_id, i, step),
            )


def _insert_recipe1_ingredients(cur):
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            meal_type TEXT,
            cook_time INTEGER,
            needs_pan INTEGER,
            needs_oven INTEGER,
            needs_blender INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS units (id INTEGER PRIMARY KEY, name TEXT NOT NULL)
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

    _ensure_units(cur)
    # Чеснок: если был в «шт», перевести на «зубчик» (для существующей БД)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipe_ingredients'")
    if cur.fetchone() is not None:
        cur.execute("SELECT 1 FROM units WHERE id = 11")
        if cur.fetchone() is not None:
            cur.execute(
                "UPDATE recipe_ingredients SET unit_id = 11 WHERE name = 'Чеснок' AND unit_id = 9"
            )

    cur.execute("SELECT COUNT(*) FROM recipes")
    recipe_count = cur.fetchone()[0]

    if recipe_count == 0:
        # Новая БД — заполняем из recipes.json (или один рецепт по умолчанию)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipe_ingredients'")
        if cur.fetchone() is None:
            _create_ingredients_table(cur)
        _populate_from_json(cur)
        conn.commit()
        conn.close()
        return

    # Существующая БД — проверяем схему recipe_ingredients
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipe_ingredients'")
    table_exists = cur.fetchone() is not None
    if table_exists:
        cur.execute("PRAGMA table_info(recipe_ingredients)")
        columns = [row[1] for row in cur.fetchall()]
        if "unit_id" in columns:
            cur.execute("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = 1")
            if cur.fetchone()[0] == 0:
                _insert_recipe1_ingredients(cur)
        else:
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
