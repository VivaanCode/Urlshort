import os
from flask import Flask, render_template, redirect, request
app = Flask('app', static_folder="static", template_folder="pages")
import random, string, validators
import sqlite3

def sqlConnect():
    c = sqlite3.connect('db.sqlite3')
    c.row_factory = sqlite3.Row
    #print("connected to database")
    #print(c)
    return c

def sqlInit():
    with sqlConnect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS ushort_links (short TEXT PRIMARY KEY, long TEXT, clicks INTEGER DEFAULT 0)')
        #print("created table successfully")
        #print(c)

def sqlGet(short):
    with sqlConnect() as c:
        row = c.execute('SELECT long FROM ushort_links WHERE short = ?', (short,)).fetchone()
        #print("got row successfully")
        #print(c)
        #print(row)
        return row[0] if row else None

def sqlGetOther(long):
    with sqlConnect() as c:
        row = c.execute('SELECT short FROM ushort_links WHERE long = ?', (long,)).fetchone()
        #print("got row successfully")
        #print(c)
        print(row[0])
        return row[0] if row else None

def sqlAddClick(short):
     with sqlConnect() as c:
        c.execute('UPDATE ushort_links SET clicks = clicks + 1 WHERE short = ?', (short,))
        c.commit()

def sqlGetClicks(short):
    with sqlConnect() as c:
        row = c.execute('SELECT clicks FROM ushort_links WHERE short = ?', (short,)).fetchone()
        #print("got row successfully")
        #print(c)
        #print(row)
        return row[0] if row else None

def sqlSet(short, long):
    with sqlConnect() as c:
        c.execute('INSERT OR REPLACE INTO ushort_links (short, long) VALUES (?, ?)', (short, long))
        c.commit()
        #print("set row successfully")
        #print(c)

def sqlClear():
    with sqlConnect() as c:
        c.execute('DELETE FROM ushort_links')
        c.commit()
        #print("cleared database")
        #print(c)

sqlInit()

admin_code = os.getenv("ADMIN_CODE")
#admin_code = "test"



def create_short_id_name():
  output = '_'

  for i in range(1, 6):
    output = output + random.choice(list(string.ascii_letters))
  
  return output
    
@app.route('/info')
def created_page():
  return render_template("created.html", id=request.args["id"], clicks=sqlGetClicks(request.args["id"]))


@app.route('/', defaults={"id": None})
@app.route('/<id>')
def render_page(id):
  if not id:
    id = request.args.get("id")
  if not id:
    return render_template('index.html')
  else:
    try:
      sqlAddClick(id)
      return redirect(sqlGet(id))
    except Exception as e:
      print("Ran into an error: " + str(e))
      return render_template("page_not_found.html")

@app.route('/cleardb')
def clear_db_url():
  return render_template('admin.html')


@app.route('/api/create')
def api_create():
  if not validators.url(request.args["long"]):
    return render_template("invalid_url.html")

  try:
    if sqlGetOther(request.args["long"]):
      return redirect("/info?id="+sqlGetOther(request.args["long"]))
  except:
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



app.run(host='0.0.0.0', port=8080)