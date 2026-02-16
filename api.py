import datetime
from datetime import timezone
import psycopg2, os
import sqlFunctions

sqlFunctions.sqlInit()

try: 
  from dotenv import load_dotenv
  load_dotenv()
except:
  pass

db_url = os.getenv("DATABASE_URL")

# helper methods (functions?)

def apiInit():
  global conn
  conn = psycopg2.connect(db_url)
  
  with conn.cursor() as c:
    c.execute('''CREATE TABLE IF NOT EXISTS ushort_api_keys (
                    api_key TEXT PRIMARY KEY,
                    today_uses INTEGER DEFAULT 0,
                    quota_day INTEGER DEFAULT 0,
                    expiry TIMESTAMP)''')
  conn.commit()

def apiKeyExists(api_key):
  with conn.cursor() as c:
    c.execute("SELECT 1 FROM ushort_api_keys WHERE api_key = %s", (api_key,))
    return c.fetchone() is not None

def getApiKeyInfo(api_key):
  with conn.cursor() as c:
    c.execute("SELECT quota_day, expiry FROM ushort_api_keys WHERE api_key = %s", (api_key,))
    return c.fetchone()

def addApiUses(api_key):
  with conn.cursor() as c:
    c.execute("UPDATE ushort_api_keys SET today_uses = today_uses + 1 WHERE api_key = %s", (api_key,))
  conn.commit()
  

# actual api functions

def apiAdd(api_key, short, long, minutes_valid):
  if not apiKeyExists(api_key):
    return {"success": False, "error": "Invalid API key"}
  
  addApiUses(api_key)

  today_uses, quota_day, expiry = getApiKeyInfo(api_key)

  if expiry < datetime.now(timezone.utc):
    return {"success": False, "error": "API key expired"}

  if today_uses >= quota_day:
    return {"success": False, "error": "Daily quota exceeded"}

  sqlFunctions.sqlSet(short, long, minutes_valid)

  with conn.cursor() as c:
    c.execute("UPDATE ushort_api_keys SET quota_day = quota_day + 1 WHERE api_key = %s", (api_key,))
  conn.commit()

  return {"success": True}

def apiGet(api_key, short):
  if not apiKeyExists(api_key):
    return {"success": False, "error": "Invalid API key"}

  addApiUses(api_key)
  today_uses, quota_day, expiry = getApiKeyInfo(api_key)

  if expiry < datetime.now(timezone.utc):
    return {"success": False, "error": "API key expired"}

  long = sqlFunctions.sqlGet(short)
  if long:
    sqlFunctions.sqlAddClick(short)
    return {"success": True, "long": long}
  return {"success": False, "error": "Short URL not found"}