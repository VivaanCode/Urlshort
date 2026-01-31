import os
from flask import Flask, render_template, redirect, request
app = Flask('app', static_folder="static", template_folder="pages")
import random, string
#from replit import db


db = {}

admin_code = "test"


def create_short_id_name():
  output = '_'

  for i in range(1, 6):
    output = output + random.choice(list(string.ascii_letters))
  
  return output
    
@app.route('/created')
def created_page():
  return render_template("created.html", id=request.args["id"])


@app.route('/', defaults={"id": None})
@app.route('/<id>')
def render_page(id):
  if not id:
    id = request.args.get("id")
  if not id:
    return render_template('index.html')
  else:
    try:
      return redirect(db[id])
    except KeyError:
      return render_template("page_not_found.html")

@app.route('/cleardb')
def clear_db_url():
  return render_template('admin.html')
  
  #return render_template("index.html")

@app.route('/api/create')
def api_create():
  id = create_short_id_name()

  db[id] = request.args["long"]

  return redirect("/created?id="+id)

@app.route('/admin/cleardb')
def admin():
  if request.args["admincode"] == admin_code:
    db.clear()
    return '', 200

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