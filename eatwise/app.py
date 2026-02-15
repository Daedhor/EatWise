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


def get_ingredients(recipe_id: int) -> list[str]:
    """Возвращает список ингредиентов рецепта по порядку."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT text FROM recipe_ingredients WHERE recipe_id = ? ORDER BY sort_order",
        (recipe_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


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


def main():
    init_db()

    st.set_page_config(page_title="EatWise", page_icon="🍳")
    st.title("🍳 EatWise")
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

            st.success(f"**{recipe['name']}**")
            st.write(f"⏱ **Время приготовления:** {recipe['cook_time']} мин")
            if tools:
                st.write("🛠 **Используемые инструменты:** ", ", ".join(tools))

            st.divider()
            st.subheader("📋 Ингредиенты")
            if ingredients:
                for ing in ingredients:
                    st.write(f"- {ing}")
            else:
                st.caption("Ингредиенты не указаны.")

            st.divider()
            st.subheader("👨‍🍳 Пошаговые инструкции")
            if steps:
                for i, step in enumerate(steps, start=1):
                    st.write(f"**{i}.** {step}")
            else:
                st.caption("Инструкции не указаны.")


if __name__ == "__main__":
    main()
