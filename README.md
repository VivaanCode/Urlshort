# Ushort

Hi! Welcome to my URL Shortener.

---

## Build command

```bash
pip install -r requirements.txt
```

## Start command

```bash
python -m gunicorn main:app --bind 0.0.0.0:$PORT
```

Make sure you have enviornment variables `ADMIN_CODE` and `DATABASE_URL` set.  
If you don't know where to get a database url, it looks like `postegresql://something`.  
Use [Neon](https://neon.tech)

---

## Endpoints

### `/`
Page for basic URL creation.

### `/<id>`
Redirects to the long link.

### `/info/<short url>`
Returns information about the link like the expiry date and amount of clicks.

### `/unshorten`
Shows a page for finding out where short links lead.

### `/advanced`
Page for advanced URL creation. Passwords coming soon?

### `/unshortener`
API endpoint for within the app to unshorten links

### `/api/create`
API endpoint for within the app to create links

### `/admin/cleardb`
Clears the database using the password from .env

### `/ping`
Clears expired links, to be pinged by UptimeRobot or etc. every 5 minutes.

---

## API Usage

All endpoints require a Bearer authorization header. If you want one for some reason, reach out.  
All endpoints return JSON.

### `/api/apicreate?long=<long link>&minutes_valid=<minutes valid>`
Creates a new short link.

### `/api/getlink?short=<short string>`
Returns information about the link like the expiry date and amount of clicks.  
The short string is the `<id>` in `/<id>`.  
You cannot give a full short link for this endpoint.  
Warning: This will only return 404 if you accidentally send a full short link for it.

---

## Contact

vivaan [at] vivaan [dot] dev
