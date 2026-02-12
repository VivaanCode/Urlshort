import os
import random
import string
import validators
from flask import Flask, render_template, redirect, request
from datetime import datetime, timezone, timedelta
from flask_limiter import Limiter
from yarl import URL
import sqlFunctions

lastDBClear = None
admin_code = os.getenv("ADMIN_CODE")


def get_ip():
    if request.headers.get("True-Client-IP"):
        return request.headers.get("True-Client-IP")

    x_forwarded_for = request.headers.get("X-Forwarded-For")

    if x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(",")]
        return ips[-2] if len(ips) >= 2 else ips[0] # return the 2nd last ip address in x-forwarded for (https://community.render.com/t/accessing-client-ips-in-a-node-express-app/36282)

    return request.remote_addr

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


sqlFunctions.sqlInit()




def create_short_id_name():
  output = '_'

  for i in range(1, 6):
    output = output + random.choice(list(string.ascii_letters))

  if not sqlFunctions.sqlGet(output) is None:
    return create_short_id_name()
  return output
    
@app.route('/info')
def created_page():
  idArg = request.args.get("id")

  if not sqlFunctions.sqlGet(idArg):
    return render_template("page_not_found.html")

  
  expiry = sqlFunctions.sqlGetExpiry(idArg)

  if expiry:
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    
    remaining = expiry - datetime.now(timezone.utc)
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if remaining < 0:
      return render_template("page_not_found.html")

    if days > 0:
      timeLeft = f"{days}d {hours}h {minutes}m" 
    elif hours > 0:
      timeLeft = f"{hours}h {minutes}m"
    else:
      timeLeft = f"{minutes}m"


    return render_template("created.html", id=idArg, clicks=sqlFunctions.sqlGetClicks(idArg), expiry=timeLeft)
  return render_template("bad_request.html")


@app.route('/', defaults={"id": None})
@app.route('/<id>')
def render_page(id):
  
  if not id:
    id = request.args.get("id")
  if not id:
    return render_template('index.html')
  else:
    try:
      shortId = sqlFunctions.sqlGet(id)
      if shortId is None:
        return render_template("page_not_found.html")
      sqlFunctions.sqlAddClick(id)
      return redirect(shortId)
    except Exception as e:
      print("Ran into an error: " + str(e))
      return render_template("page_not_found.html")


@app.route('/unshorten')
def render_unshortener():
  return render_template('unshorten.html')
    

@app.route('/advanced')
def render_advanced():
  return render_template('advanced.html')


@app.route('/unshortener')
def unshorten():

   try:
    if request.args.get("short") is None:
      return render_template("invalid_url.html")
   except:
      return render_template("invalid_url.html")


   try:
    ShortURLObject = URL(request.args.get("short"))
    ShortURL = request.args.get("short")

    ShortURLObjectOrigin = str(ShortURLObject.origin())

    ShortURL = ShortURL.replace(ShortURLObjectOrigin+"/", "")
    ShortURL = ShortURL.replace(" ", "")

    if sqlFunctions.sqlGet(ShortURL):
      return render_template("unshortened.html", link=sqlFunctions.sqlGet(ShortURL))

      
    if sqlFunctions.sqlGet(request.args.get("short")):
      return render_template("unshortened.html", link=sqlFunctions.sqlGet(request.args.get("short")))
    url = URL(request.args.get("short"))


    if sqlFunctions.sqlGet(url.query.get('short')):
      return render_template("unshortened.html", link=sqlFunctions.sqlGet(url.query.get('short')))
    if sqlFunctions.sqlGet(url.query.get('id')):
      return render_template("unshortened.html", link=sqlFunctions.sqlGet(url.query.get('id')))
   except Exception as e:
      print(e)
      return render_template("invalid_url.html")
   return render_template("invalid_url.html")

    


@app.route('/cleardb')
def clear_db_url():
  return render_template('admin.html')


@app.route('/api/create')
@limiter.limit("10 per minute; 67 per hour; 200 per day")
def api_create():
  try:
    if request.args.get("long") is None:
      return render_template("invalid_url.html")
  except:
    return render_template("invalid_url.html")

  id = create_short_id_name()
  try:
    if int(request.args.get("minutes_valid")):
      validMinutes = int(request.args.get("minutes_valid"))
    else:
      validMinutes = 4320
  except:
    validMinutes = 4320

  if validMinutes > 4320:
    validMinutes = 4320

  if not validators.url(request.args.get("long")):
    if validators.url("https://"+request.args.get("long")):
      sqlFunctions.sqlSet(id, "https://"+request.args["long"], validMinutes)
      return redirect("/info?id="+id)
    else:
      return render_template("invalid_url.html")
  
  sqlFunctions.sqlSet(id, request.args["long"], validMinutes)

  return redirect("/info?id="+id)

@app.route('/admin/cleardb', methods=['POST'])
def admin():
  if request.form.get("admincode") == admin_code:
    sqlFunctions.sqlClear()
    return render_template("reset_success.html"), 200
  return render_template("incorrect_admin_code.html")


@app.route('/ping')
def clean_up_garbage():
  global lastDBClear
  now = datetime.now()

  if lastDBClear is None:
    sqlFunctions.sqlDeleteOldLinks()
    lastDBClear = now
    return "garbage was cleaned :)"
  if now - lastDBClear >= timedelta(minutes=4.9):
    sqlFunctions.sqlDeleteOldLinks()
    lastDBClear = now
    return "garbage was cleaned :)<br>case 2"
  return "for whatever reason, couldn't clear garbage"



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