# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import calendar
	 
app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(app.root_path, 'test.db'),
    SECRET_KEY='development key'
))

app.config.from_envvar('DIARY_SETTINGS', silent=True)	 
db = SQLAlchemy(app)

class Day(db.Model):
	"""
	Represents a day in the diary. A day can have multiple entries associated with it.
	"""
	id = db.Column(db.Integer, primary_key = True)
	date = db.Column(db.Date, nullable = False, unique = True, default=date.today())

	def __repr__(self):
		return '<Day %r>' % self.date.strftime('%d-%m-%Y')
	
class Entry(db.Model):
	"""
	Entry associated with a day.
	"""
	id = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String(120), nullable = False)
	text = db.Column(db.String(360), nullable = False)

	day_id = db.Column(db.Integer, db.ForeignKey('day.id'), nullable = False) 
	day = db.relationship('Day', backref = db.backref('entries', lazy = True))

	def __repr__(self):
		return '<Day %r - %r>' % (self.day.date.strftime('%d-%m-%Y'), self.title)
	
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_date = db.Column(db.Date, nullable = False, default=date.today())

    def __repr__(self):
        return '<User %r>' % self.username

def init_db():
    db.create_all()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.route('/<year>/<month>')
@app.route('/')
def show_days(year = None, month = None):	
	my_month = None if month is None else int(month)
	my_year = None if year is None else int(year)

	if my_month is None:
		my_month = date.today().month
	
	if my_year is None:
		my_year = date.today().year

	month_days = calendar.monthcalendar(int(my_year), int(my_month))
	
	days = db.session.query(Day).all()
	my_month_name = calendar.month_name[ my_month ]
	
	return render_template('show_days.html', days=days, my_month = my_month, my_year = my_year, month_days = month_days, my_month_name = my_month_name )
	
	
@app.route('/show_entries/<my_year>/<my_month>/<my_day>')
def show_entries( my_year, my_month, my_day ):
	"""
	Shows entries associated with a particular day
	"""
	date_string = '%s-%s-%s' % (my_year, my_month, my_day)
	my_date = datetime.strptime(date_string, "%Y-%M-%d").date()
	my_date = db.session.query(Day).filter_by(date = my_date).first()
	my_entries = db.session.query(Entry).filter_by( day = my_date )
	my_month_name = calendar.month_name[ int(my_month) ]
	return render_template('show_entries.html', entries = my_entries, month_name = my_month_name, year = my_year, month = my_month, day =my_day )
	
		
@app.route('/add_user', methods=['POST'])
def add_user():
	my_username = request.form['username']
	my_email = request.form['email']
	my_date = request.form['created_date']
	my_date = datetime.strptime(my_date, "%Y-%M-%d").date()
	db.session.add(User(username= my_username, email = my_email, created_date = my_date))
	db.session.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))@app.route('/add_user', methods=['POST'])
	
	
@app.route('/add_entry/<mydate>', methods=['POST'])
def add_entry(mydate):
	my_day = datetime.strptime(mydate, "%Y-%M-%d").date()
	my_title = request.form['title']
	my_text = request.form['text']
	my_days = db.session.query(Day).filter_by(date = my_day)
	
	# Get the day if it already exists, else create one
	if my_days.count() != 0:
		my_day = my_days.first()
	else: 
		my_day = Day(date = my_day)
	
	# Create entry using the day
	db.session.add(Entry(title = my_title, text = my_text, day = my_day))
	db.session.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries', my_year = my_day.date.year, my_month = my_day.date.month, my_day = my_day.date.day))

@app.route('/entry_page/<my_year>/<my_month>/<my_day>')
def entry_page( my_year, my_month, my_day ):
	my_month_name = calendar.month_name[ int(my_month) ]
	return render_template('entry_page.html', year = my_year, month = my_month, day = my_day, month_name = my_month_name)

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
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)	
		
		
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))		