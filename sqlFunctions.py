from datetime import datetime, timedelta, timezone
import psycopg2, os

conn = None

try: 
  from dotenv import load_dotenv
  load_dotenv()
except:
  pass

db_url = os.getenv("DATABASE_URL")

def sqlInit():
    global conn
    conn = psycopg2.connect(db_url)
    
    with conn.cursor() as c:
      c.execute('''CREATE TABLE IF NOT EXISTS ushort_links (
                      short TEXT PRIMARY KEY, 
                      long TEXT, 
                      clicks INTEGER DEFAULT 0,
                      expiry TIMESTAMP,
                      password_hash TEXT)''')
    conn.commit()

def sqlGetHashedPassword(short):
    try:
      with conn.cursor() as c:
        c.execute('SELECT password_hash FROM ushort_links WHERE short = %s', (short,))
        row = c.fetchone()
        return row[0] if row else None
    except psycopg2.InterfaceError as e:
        sqlInit()
        return sqlGetHashedPassword(short)

def sqlGet(short): # get long from short
    try:
      with conn.cursor() as c:
        c.execute('SELECT long FROM ushort_links WHERE short = %s', (short,))
        row = c.fetchone()
        return row[0] if row else None
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlGet(short)

def sqlGetOther(long): # get short from long
    try:
      with conn.cursor() as c:
        c.execute('SELECT short FROM ushort_links WHERE long = %s', (long,))
        row = c.fetchone()
        return row[0] if row else None
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlGetOther(long)

def sqlAddClick(short):
    try:
      with conn.cursor() as c:
        c.execute('UPDATE ushort_links SET clicks = clicks + 1 WHERE short = %s', (short,))
      conn.commit()
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlAddClick(short)

def sqlGetClicks(short):
    try:
      with conn.cursor() as c:
        c.execute('SELECT clicks FROM ushort_links WHERE short = %s', (short,))
        row = c.fetchone()
        return row[0] if row else None
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlGetClicks(short)

def sqlSet(short, long, minutes_valid, password_hash=None):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes_valid)
    try:
      with conn.cursor() as c:
        c.execute('''INSERT INTO ushort_links (short, long, expiry, password_hash) 
                          VALUES (%s, %s, %s, %s)
                          ON CONFLICT (short) DO UPDATE SET long = EXCLUDED.long,
                          expiry = EXCLUDED.expiry, 
                          password_hash = EXCLUDED.password_hash''', (short, long, expiry, password_hash))
      conn.commit()
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlSet(short, long, minutes_valid, password_hash)

def sqlDeleteOldLinks():
    try:
      with conn.cursor() as c:
        c.execute("DELETE FROM ushort_links WHERE expiry < CURRENT_TIMESTAMP AT TIME ZONE 'UTC';")
      conn.commit()
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlDeleteOldLinks()

def sqlClear():
    try:
      with conn.cursor() as c:
        c.execute('DELETE FROM ushort_links')
      conn.commit()
    except psycopg2.InterfaceError as e:
      sqlInit()
      return sqlClear()

def sqlGetExpiry(short):
  try:
    with conn.cursor() as c:
      c.execute('SELECT expiry FROM ushort_links WHERE short = %s', (short,))
      row = c.fetchone()
      return row[0] if row else None
  except psycopg2.InterfaceError as e:
    sqlInit()
    return sqlGetExpiry(short)