"""
EatWise v0 — минимальный веб-прототип на Streamlit.
Пользователь выбирает ограничения и получает один рецепт.
"""
import sqlite3
from pathlib import Path

import streamlit as st

from init_db import init_db

DB_PATH = Path(__file__).parent / "recipes.db"

MEAL_LABELS = {"breakfast": "Завтрак", "lunch": "Обед", "dinner": "Ужин"}
TOOL_COLUMNS = [
    ("needs_pan", "Сковорода"),
    ("needs_oven", "Духовка"),
    ("needs_blender", "Блендер"),
]


def get_recipe_by_id(recipe_id: int) -> dict | None:
    """Возвращает рецепт по id или None."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_recipe(meal_type: str, max_time: int, has_pan: bool, has_oven: bool, has_blender: bool):
    """Возвращает один случайный рецепт по фильтрам или None."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Базовые условия
    conditions = ["meal_type = ?", "cook_time <= ?"]
    params = [meal_type, max_time]

    # Инструменты: рецепт подходит только если все нужные инструменты есть у пользователя
    if not has_pan:
        conditions.append("needs_pan = 0")
    if not has_oven:
        conditions.append("needs_oven = 0")
    if not has_blender:
        conditions.append("needs_blender = 0")

    query = f"""
        SELECT * FROM recipes
        WHERE {' AND '.join(conditions)}
        ORDER BY RANDOM()
        LIMIT 1
    """
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def format_used_tools(recipe: dict) -> list[str]:
    """Список использованных инструментов по-русски."""
    used = []
    for col, label in TOOL_COLUMNS:
        if recipe.get(col):
            used.append(label)
    return used


def get_ingredients(recipe_id: int) -> list[dict]:
    """Возвращает список ингредиентов: name, amount (или None), unit_name."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """SELECT i.name, i.amount, u.name
           FROM recipe_ingredients i
           JOIN units u ON i.unit_id = u.id
           WHERE i.recipe_id = ?
           ORDER BY i.sort_order""",
        (recipe_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"name": r[0], "amount": r[1], "unit": (r[2] or "").strip()} for r in rows]


def _format_amount(amount: float) -> str:
    """Количество: целое или один знак после запятой (русский формат)."""
    if amount is None:
        return ""
    if amount == int(amount):
        return str(int(amount))
    return str(round(amount, 1)).replace(".", ",")


def format_ingredient(ing: dict, num: int) -> str:
    """Форматирует один ингредиент: '1) Название — количество единица' или '1) Название — по вкусу'."""
    name = ing["name"]
    amount = ing.get("amount")
    unit = (ing.get("unit") or "").strip()
    if amount is not None and unit and unit not in ("по вкусу", "для жарки"):
        return f"{num}) {name} — {_format_amount(amount)} {unit}"
    if unit in ("по вкусу", "для жарки"):
        return f"{num}) {name} — {unit}"
    if amount is not None:
        return f"{num}) {name} — {_format_amount(amount)}"
    return f"{num}) {name}"


def get_steps(recipe_id: int) -> list[str]:
    """Возвращает пошаговые инструкции рецепта по порядку."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT step_text FROM recipe_steps WHERE recipe_id = ? ORDER BY step_order",
        (recipe_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def _build_copy_text(recipe_name: str, ingredients: list[dict]) -> str:
    """Собирает текст для копирования: название и нумерованные ингредиенты (ссылку добавляет JS)."""
    lines = [recipe_name]
    for i, ing in enumerate(ingredients, start=1):
        lines.append(format_ingredient(ing, i))
    return "\n".join(lines)


def _render_copy_button(recipe_name: str, ingredients: list[dict], recipe_id: int):
    """Кнопка «Скопировать ингредиенты»: копирует в буфер название, ингредиенты и ссылку (JS)."""
    copy_body = _build_copy_text(recipe_name, ingredients)
    # Экранируем для вставки в JS-строку (обратный слэш, кавычки, переносы)
    copy_body_esc = copy_body.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    html = f"""
    <div id="copy-block">
        <button id="copy-btn" type="button" style="
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            border: 1px solid #ccc;
            background: #f0f2f6;
            cursor: pointer;
            font-size: 0.9rem;
        ">Скопировать ингредиенты</button>
        <span id="copy-toast" style="margin-left: 0.5rem; color: green; font-size: 0.9rem; display: none;">Список ингредиентов и ссылка на рецепт скопированы в буфер обмена!</span>
    </div>
    <script>
        (function() {{
            var btn = document.getElementById('copy-btn');
            var toast = document.getElementById('copy-toast');
            var body = '{copy_body_esc}';
            var recipeId = {recipe_id};
            function showToast() {{
                toast.style.display = 'inline';
                setTimeout(function() {{ toast.style.display = 'none'; }}, 3000);
            }}
            function fallbackCopy(text) {{
                var ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                document.body.appendChild(ta);
                ta.select();
                try {{
                    document.execCommand('copy');
                }} catch (e) {{}}
                document.body.removeChild(ta);
            }}
            btn.onclick = function() {{
                var loc = window.top && window.top.location ? window.top.location : window.location;
                var base = loc.origin + (loc.pathname || '/');
                if (!base.endsWith('/')) base += '/';
                var link = base + '?recipe_id=' + recipeId;
                var full = body + '\\nСсылка на рецепт: ' + link;
                if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {{
                    navigator.clipboard.writeText(full).then(showToast).catch(function() {{ fallbackCopy(full); showToast(); }});
                }} else {{
                    fallbackCopy(full);
                    showToast();
                }}
            }};
        }})();
    </script>
    """
    st.components.v1.html(html, height=50)


def _render_recipe(recipe: dict, ingredients: list[dict], steps: list[str], tools: list[str]):
    """Отрисовка блока рецепта: название, время, инструменты, ингредиенты (с кнопкой копирования), шаги."""
    recipe_id = recipe["id"]
    st.success(f"**{recipe['name']}**")
    st.write(f"⏱ **Время приготовления:** {recipe['cook_time']} мин")
    if tools:
        st.write("🛠 **Используемые инструменты:** ", ", ".join(tools))

    st.divider()
    st.subheader("📋 Ингредиенты")
    if ingredients:
        for i, ing in enumerate(ingredients, start=1):
            st.write(format_ingredient(ing, i))
        _render_copy_button(recipe["name"], ingredients, recipe_id)
    else:
        st.caption("Ингредиенты не указаны.")

    st.divider()
    st.subheader("👨‍🍳 Пошаговые инструкции")
    if steps:
        for i, step in enumerate(steps, start=1):
            st.write(f"**{i}.** {step}")
    else:
        st.caption("Инструкции не указаны.")


def main():
    init_db()

    st.set_page_config(page_title="EatWise", page_icon="🍳")
    st.title("🍳 EatWise")

    # Открытие по ссылке ?recipe_id=<id> — показываем только рецепт
    recipe_id_param = None
    if hasattr(st, "query_params") and st.query_params:
        recipe_id_param = st.query_params.get("recipe_id")
    if recipe_id_param is None and hasattr(st, "experimental_get_query_params"):
        q = st.experimental_get_query_params()
        recipe_id_param = (q.get("recipe_id") or [None])[0] if q else None

    if recipe_id_param is not None:
        try:
            rid = int(recipe_id_param)
            recipe = get_recipe_by_id(rid)
            if recipe:
                st.link_button("← Генератор рецептов", url="/", type="secondary")
                ingredients = get_ingredients(rid)
                steps = get_steps(rid)
                tools = format_used_tools(recipe)
                _render_recipe(recipe, ingredients, steps, tools)
                return
        except ValueError:
            pass
        st.warning("Рецепт не найден. Укажите корректный recipe_id в ссылке или выберите рецепт ниже.")

    st.caption("Выберите ограничения — получите рецепт")
    meal_choice = st.radio(
        "Тип приёма пищи",
        options=list(MEAL_LABELS.keys()),
        format_func=lambda x: MEAL_LABELS[x],
        horizontal=True,
    )
    max_time = st.slider("Максимальное время приготовления (минуты)", 5, 120, 30, 5)
    st.subheader("Доступные инструменты")
    has_pan = st.checkbox("Сковорода", value=True)
    has_oven = st.checkbox("Духовка", value=False)
    has_blender = st.checkbox("Блендер", value=False)

    if st.button("Что приготовить?"):
        recipe = get_recipe(meal_choice, max_time, has_pan, has_oven, has_blender)
        if recipe is None:
            st.warning("Нет подходящего рецепта.")
        else:
            recipe_id = recipe["id"]
            ingredients = get_ingredients(recipe_id)
            steps = get_steps(recipe_id)
            tools = format_used_tools(recipe)
            _render_recipe(recipe, ingredients, steps, tools)


if __name__ == "__main__":
    main()
