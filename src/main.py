from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, json, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
import functools
import tasks
import os

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50), unique=True, nullable=False)
	first_name = db.Column(db.String(50))
	last_name = db.Column(db.String(50))
	email = db.Column(db.String(100), unique=True)
	password = db.Column(db.String(100), nullable=False)
	is_admin = db.Column(db.Boolean, nullable=False, default=False)
	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

	def __repr__(self):
		return '<User %r>' % self.name

def validate_user(user, name, passwd):
	if not user or not bcrypt.checkpw(passwd.encode('utf-8'), user.password):
		return False
	return True

def get_options(user):
	task_list = ['fifocapgains', 'billledgercomp']
	names = tasks.get_customer_names()
	fy = [*range(2012,2021)]

	data = {
			'tasks' : task_list,
			'names' : names,
			'fy' : fy }

	return jsonify(data)

def task_fifocapgains(user, customer, fy):
	xls_file = '/downloads/{0}/{1}_capgain_{2}.xlsx'.format(user,customer.replace(' ', '' ), fy)

	data = tasks.get_fifo_cap_gains(customer, fy, xls_file[1:])

	data.update({'xls' : xls_file})

	response = app.response_class(
				response=json.dumps(data), status=200,
				mimetype='application/json')

	return response

def task_billledgercomp(user, date):
	xls_file = '/downloads/{0}/billledger_{1}.xlsx'.format(user,date)

	data = tasks.get_bill_ledger_comp(date, xls_file[1:])
	
	data.update({'xls' : xls_file})

	response = app.response_class(
				response=json.dumps(data), status=200,
				mimetype='application/json')

	return response

@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		loginname = request.form['loginname']
		passwd = request.form['psw']
		user = User.query.filter_by(name=loginname).first()
		if validate_user(user, loginname, passwd) == True:
			session["loginname"] = loginname
			return redirect(url_for('user', name=loginname))
		else:
			flash("Username or password is not valid!", "Warning")			
	else:
		pass	
	
	return render_template("login.html")

def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "loginname" not in session:
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return secure_function

def admin_required(func):
	@functools.wraps(func)
	def secure_function(*args, **kwargs):
		if "loginname" not in session:
 			return redirect(url_for("login"))
		
		user = User.query.filter_by(name=session['loginname']).first()
		if not user or (user.is_admin == False):
			return redirect(request.url_root)

		return func(*args, **kwargs)

	return secure_function

@app.route('/home')
@login_required
def home():
	return redirect(url_for("user", name=session['loginname']))

@app.route('/user/<name>')
@login_required
def user(name):
	userdb = User.query.filter_by(name=name).first()
	if userdb.is_admin == True:
		return render_template("reports.html", name=name)
	elif session['loginname'] != name:
		return redirect(request.url_root)

	return render_template("customer.html", name=name)

@app.route('/downloads/<string:name>/<string:file_name>')
@login_required
def downloads(name, file_name):

	if session['loginname'] != name:
		abort(404)

	dir_path = os.path.join(app.config['DOWNLOADS_PATH'], name)

	print('download', dir_path, file_name)

	try:
		return send_from_directory(dir_path, filename=file_name, as_attachment=True)
	except FileNotFoundError:
		abort(404)

@app.route('/query', methods=['POST'])
@login_required
def options():
	#print(request.method, request.get_json(silent=True))
	params = request.get_json()
	print(params)

	if params['opcode'] == 1:
		return get_options(session.get('loginname'))
	elif params['opcode'] == 2:
		return task_fifocapgains(session.get('loginname'), params['name'], params['fy'])	
	elif params['opcode'] == 3:
		return task_billledgercomp(session.get('loginname'), params['date'])	
	else:	
		return None

@app.route('/reports')
@login_required
def reports():
	return render_template("reports.html", name=session.get('loginname'))

@app.route('/logout')
@login_required
def logout():
	name = session['loginname']
	flash("{} has logged out!!!".format(name), "Info")
	session.pop('loginname',None)
	return render_template("login.html")

@app.route('/useredit', methods=['POST', 'GET'])
@admin_required
def user_edit():
	if request.method == 'POST':
		fname = request.form.get('first-name')
		lname = request.form.get('last-name')
		email = request.form.get('user-email')
		name = request.form.get('login-name')
		password = request.form.get('pswd')
		hashedpwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
		is_admin = True if request.form.get('is-admin') else False
		new_user = User(name=name, password=hashedpwd, is_admin=is_admin, email=email, first_name=fname, last_name=lname)
		dir_path = os.path.join(app.config['DOWNLOADS_PATH'], name)

		try:
			db.session.add(new_user)
			db.session.commit()
			os.mkdir(dir_path)
			return redirect(url_for('user_edit'))
		except OSError as e:
			return "<h2>Error creating user directory</h2>"
		except:
			return "<h2>There was an error</h2>"
	else:
		users = User.query.order_by(User.date_created)	
		return render_template("useredit.html", name=session.get('loginname'), users=users)

@app.route('/delete/<int:id>')
@admin_required
def delete(id):
	user_to_del = User.query.get_or_404(id)
	try:
		db.session.delete(user_to_del)
		db.session.commit()
		return redirect('/useredit')
	except:
		return "<h2> Error in deleting user </h2>"

if __name__ == "__main__":
	app.run()
