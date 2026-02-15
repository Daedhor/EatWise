# EatWise v0 — как запустить

## Вариант 1: через `python3 -m` (рекомендуется)

Используйте тот Python, который у вас реально установлен (`python3`), и вызывайте pip и streamlit через него:

```bash
cd /Users/shailov/EatWise/eatwise

# Установить зависимости (один раз)
python3 -m pip install -r requirements.txt

# Запустить приложение
python3 -m streamlit run app.py
```

После запуска в терминале появится ссылка (обычно http://localhost:8501) — откройте её в браузере.

---

## Вариант 2: виртуальное окружение (если хотите изолировать зависимости)

```bash
cd /Users/shailov/EatWise/eatwise

# Создать виртуальное окружение
python3 -m venv .venv

# Активировать (macOS/Linux)
source .venv/bin/activate

# Установить зависимости и запустить
pip install -r requirements.txt
streamlit run app.py
```

После работы деактивировать окружение: `deactivate`.

---

## Если команды не находятся

- Вместо `pip` всегда используйте: **`python3 -m pip`**.
- Вместо `streamlit` используйте: **`python3 -m streamlit run app.py`**.

Так вы гарантированно используете тот же Python, что и при установке пакетов.
