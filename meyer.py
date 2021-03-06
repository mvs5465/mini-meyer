# load all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# create the application
app = Flask(__name__)
app.config.from_object(__name__)

# load default config and override config from an environment variable
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, 'meyer.db'),
  SECRET_KEY='development key',
  USERNAME='admin',
  PASSWORD='default'
))

## following line unnecessary ##
#app.config.from_envvar('MEYER_SETTINGS', silent=True)

#connect to db
def connect_db():
  """Connects to the specific database"""
  rv = sqlite3.connect(app.config['DATABASE'])
  rv.row_factory = sqlite3.Row
  return rv

#initialize the db
def init_db():
  db = get_db()
  with app.open_resource('schema.sql', mode='r') as f:
    db.cursor().executescript(f.read())
  db.commit()

@app.cli.command('initdb')
def initdb_command():
  """Initializes the database"""
  init_db()
  print "Initialized database"

# connect to db
def get_db():
  """Opens a new db connection if there is none yet for the current application context"""
  if not hasattr(g, 'sqlite_db'):
    g.sqlite_db = connect_db()
  return g.sqlite_db

# teardown db connection after use
@app.teardown_appcontext
def close_db(error):
  """Closes the database again at the end of the request."""
  if hasattr(g, 'sqlite_db'):
    g.sqlite_db.close()

# Default route "/" to show all database entries 
@app.route('/')
def show_entries():
  db = get_db()
  cur = db.execute('SELECT title, text FROM entries ORDER BY id DESC')
  entries = cur.fetchall()
  return render_template('show_entries.html', entries=entries)

# Adding a new entry, route
@app.route('/add', methods=['POST'])
def add_entry():
  if not session.get('logged_in'):
    abort(401)
  db = get_db()
  db.execute('INSERT INTO ENTRIES (title, text) VALUES (?, ?)',
    [request.form['title'], request.form['text']])
  db.commit()
  flash('New entry successfully posted')
  return redirect(url_for('show_entries'))

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
      error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
      error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You have been successfully logged in')
      return redirect(url_for('show_entries'))
  return render_template('login.html', error=error)

# logout
@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You have been logged out.')
  return redirect(url_for('show_entries'))

# Encrypt endpoint
@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
  if request.method == 'POST':
    data = request.form['text']
    ciphertext = encipher(data)
    flash(ciphertext)
    return redirect(url_for('encrypt'))
  return render_template('encrypt.html') 

# Actual "encryption" function
def encipher(plain):
  plain = plain.encode('ascii','replace')
  cipher = plain.upper()
  return cipher
