# Ushort
Hi! Welcome to my URL Shortener.

Build command:
```
pip install -r requirements.txt
```

Start command:
```
python -m gunicorn main:app --bind 0.0.0.0:$PORT
```

Make sure you have enviornment variables ADMIN_CODE and DATABASE_URL set.
If you don't know where to get a database url, it looks like `postegresql://something`. Use [Neon](https://neon.tech)