# EatWise

## Как запустить

Из **корня репозитория** (папка `EatWise`):

```bash
# Инициализация БД (один раз)
python3 eatwise/init_db.py

# Запуск приложения
python3 -m streamlit run eatwise/app.py
```

Либо перейти в папку приложения и запускать оттуда:

```bash
cd eatwise
python3 init_db.py
python3 -m streamlit run app.py
```
