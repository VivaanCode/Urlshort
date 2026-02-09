from math import exp
import os
from flask import Flask, render_template, redirect, request

import random, string, validators
#import sqlite3
import psycopg2
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db_url = os.getenv("DATABASE_URL")
#db_url = ""
admin_code = os.getenv("ADMIN_CODE")
#admin_code = "test"

days_valid = 3

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

app = Flask('app', static_folder="static", template_folder="pages")
limiter = Limiter(
    key_func=get_ip,
    app=app,
    default_limits=["1000 per day"],
    storage_uri="memory://",
)


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("rate_limit.html"), 429

def sqlConnect():
    conn = psycopg2.connect(db_url) #sqlite3.connect('db.sqlite3')
    #c.row_factory = sqlite3.Row
    #print("connected to database")
    #print(c)
    return conn

def sqlInit():
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS ushort_links (
                        short TEXT PRIMARY KEY, 
                        long TEXT, 
                        clicks INTEGER DEFAULT 0,
                        expiry TIMESTAMP)''')
      conn.commit()

def sqlGet(short):
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('SELECT long FROM ushort_links WHERE short = %s', (short,))
        row = c.fetchone()
        #print("got row successfully")
        #print(c)
        #print(row)
        return row[0] if row else None

def sqlGetOther(long):
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('SELECT short FROM ushort_links WHERE long = %s', (long,))
        row = c.fetchone()
        #print("got row successfully")
        #print(c)
        #print(row)
        return row[0] if row else None

def sqlAddClick(short):
     with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('UPDATE ushort_links SET clicks = clicks + 1 WHERE short = %s', (short,))
      conn.commit()

def sqlGetClicks(short):
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('SELECT clicks FROM ushort_links WHERE short = %s', (short,))
        row = c.fetchone()
        #print("got row successfully")
        #print(c)
        #print(row)
        return row[0] if row else None

def sqlSet(short, long):
    expiry = datetime.now() + timedelta(days=days_valid)
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('''INSERT INTO ushort_links (short, long, expiry) 
                         VALUES (%s, %s, %s)
                         ON CONFLICT (short) DO UPDATE SET long = EXCLUDED.long,
                         expiry = EXCLUDED.expiry''', (short, long, expiry))
      conn.commit()
        #print("set row successfully")
        #print(c)

def sqlDeleteOldLinks():
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('DELETE FROM ushort_links WHERE expiry < NOW();')
      conn.commit()
        #print("cleared database")
        #print(c)

def sqlClear():
    with sqlConnect() as conn:
      with conn.cursor() as c:
        c.execute('DELETE FROM ushort_links')
      conn.commit()
        #print("cleared database")
        #print(c)

def sqlGetExpiry(short):
  with sqlConnect() as conn:
    with conn.cursor() as c:
      c.execute('SELECT expiry FROM ushort_links WHERE short = %s', (short,))
      row = c.fetchone()
      return row[0] if row else None

sqlInit()




def create_short_id_name():
  output = '_'

  for i in range(1, 6):
    output = output + random.choice(list(string.ascii_letters))

  if not sqlGet(output) is None:
    return create_short_id_name()
  return output
    
@app.route('/info')
def created_page():
  idArg = request.args.get("id")

  if not idArg:
    return render_template("page_not_found.html")

  
  expiry = sqlGetExpiry(idArg)

  if expiry:
    remaining = expiry - datetime.now()
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)


    if days > 0:
      timeLeft = f"{days}d {hours}h {minutes}m" 
    elif hours > 0:
      timeLeft = f"{hours}h {minutes}m"
    else:
      timeLeft = f"{minutes}m"


    return render_template("created.html", id=idArg, clicks=sqlGetClicks(idArg), expiry=timeLeft)
  return render_template("bad_request.html")


@app.route('/', defaults={"id": None})
@app.route('/<id>')
@limiter.limit("5 per minute; 50 per hour; 200 per day")
def render_page(id):
  sqlDeleteOldLinks()
  if not id:
    id = request.args.get("id")
  if not id:
    return render_template('index.html')
  else:
    try:
      shortId = sqlGet(id)
      if shortId is None:
        return render_template("page_not_found.html")
      sqlAddClick(id)
      return redirect(shortId)
    except Exception as e:
      print("Ran into an error: " + str(e))
      return render_template("page_not_found.html")

@app.route('/cleardb')
def clear_db_url():
  return render_template('admin.html')


@app.route('/api/create')
def api_create():
  long_url = request.args.get("long")
  print(f"[api_create] long={long_url!r}")
  try:
    if request.args.get("long") is None:
      return render_template("invalid_url.html")
  except:
    return render_template("invalid_url.html")

  if not validators.url(request.args.get("long")):
    if validators.url("https://"+request.args.get("long")):
      sqlSet(id, "https://"+request.args["long"])
    else:
      return render_template("invalid_url.html")
    

  id = create_short_id_name()
  sqlSet(id, request.args["long"])

  return redirect("/info?id="+id)

@app.route('/admin/cleardb', methods=['POST'])
def admin():
  if request.form.get("admincode") == admin_code:
    sqlClear()
    return render_template("reset_success.html"), 200
  return render_template("incorrect_admin_code.html")

@app.errorhandler(400)
def bad_request(code):
  return render_template("bad_request.html")
@app.errorhandler(500)
def internal_server_error(code):
  return render_template("internal_server_error.html")
@app.errorhandler(404)
def page_not_found(code):
  return render_template("page_not_found.html")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)