from bank import app, db, bcrypt, login_manager
from bank.forms import LoginForm, RegistrationForm, InternalTransferForm, ExternalTransferForm
from bank.models import User, TransactionLog
from bank.utils import decimal_check
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, current_user, login_required, logout_user
from decimal import Decimal
import requests


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)


@app.route("/logout")
def logout():
	logout_user()
	flash('You have successfully logged out', 'success')
	return redirect(url_for('login'))


@app.route("/", methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	login_form = LoginForm()

	if request.method == 'POST':
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.email.data).first()
			if user and bcrypt.check_password_hash(user.password, login_form.password.data):
				login_user(user)
				return redirect(url_for('soseki'))

			else:
				flash('The email or password you entered was incorrect, please try again', 'warning')
				return redirect(url_for('login'))

	context = {
		'title': 'Log in to Soseki Bank',
		'login_form': login_form,
	}
	return render_template('index.html', **context)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
	signup_form = RegistrationForm()

	if request.method == 'POST':
		if signup_form.validate_on_submit():
			hash_password = bcrypt.generate_password_hash(signup_form.password.data).decode('utf-8')
			user = User(email=signup_form.email.data, password=hash_password, first_name=signup_form.first_name.data, last_name=signup_form.last_name.data, balance=1000, admin=False,)
			db.session.add(user)
			flash('Thank you for signing up for Soseki Bank!', 'success')

			db.session.commit()
			return redirect(url_for('login'))

	context = {
		'title': 'Sign Up For Soseki Bank',
		'signup_form': signup_form,
	}
	return render_template('signup.html', **context)


@app.route('/soseki', methods=['GET', 'POST'])
@login_required
def soseki():
	internal_transfer_form = InternalTransferForm()

	if request.method == 'POST':
		if internal_transfer_form.validate_on_submit():
			sender = current_user
			recipient = User.query.filter_by(email=internal_transfer_form.email.data).first()
			amount = internal_transfer_form.amount.data

			if amount < 0.01: # Check if user is trying to send 0 or a negative amount
				flash('You must send more than $0!', 'warning')
				return redirect(url_for('soseki'))

			if decimal_check(amount) > 2: # Make sure user only inputs 2 decimal places
				flash('Please only enter 2 decimal places!', 'warning')
				return redirect(url_for('soseki'))

			balance_after_transaction = sender.balance - amount # Check if user will send more than their balance
			if balance_after_transaction <= 0:
				flash('You do not have enough funds for that transaction', "warning")
				return redirect(url_for('soseki'))

			sender.balance -= amount
			recipient.balance += amount

			about_sender = "{0} {1} <{2}>".format(sender.first_name, sender.last_name, sender.email)
			about_recipient = "{0} {1} <{2}>".format(recipient.first_name, recipient.last_name, recipient.email)

			sender_transaction_log = TransactionLog(amount=amount, from_account=about_sender, to_account=about_recipient, user_id=sender.id, positive=False)
			recipient_transaction_log = TransactionLog(amount=amount, from_account=about_sender, to_account=about_recipient, user_id=recipient.id, positive=True)

			db.session.add(sender_transaction_log)
			db.session.add(recipient_transaction_log)
			db.session.commit()
			flash('You successfully sent an internal money transfer', 'success')
			return redirect(url_for('soseki'))

	context = {
		'user': current_user,
		'title': 'Welcome To Soseki Bank',
		'internal_transfer': internal_transfer_form,
		'log': TransactionLog.query.order_by(TransactionLog.date.desc()).filter_by(user_id=current_user.id).all()
	}
	return render_template('soseki.html', **context)


@app.route('/soseki/admin', methods=['GET', 'POST'])
@login_required
def admin():

	if current_user.admin != True:
		flash('You do not have proper permission to view that page!', 'danger')
		return redirect(url_for('soseki'))

	signup_form = RegistrationForm()

	if request.method == 'POST':
		if signup_form.validate_on_submit():
			hash_password = bcrypt.generate_password_hash(signup_form.password.data).decode('utf-8')
			user = User(email=signup_form.email.data, password=hash_password, first_name=signup_form.first_name.data, last_name=signup_form.last_name.data, balance=1000, admin=True )
			db.session.add(user)
			flash('You created a new Admin User!', 'success')

			db.session.commit()
			return redirect(url_for('admin'))

	context = {
		'signup_form': signup_form,
		'user': current_user,
		'users': User.query.order_by(User.last_name).all(),
		'title': 'Welcome To Soseki Bank Admin Page',
		'logs': TransactionLog.query.order_by(TransactionLog.date.desc()).filter_by(user_id=current_user.id).all()
	}
	return render_template('admin.html', **context)


def my_request(transaction):
	url = 'http://127.0.0.1:5000/receivemoney?transaction='
	return requests.post(url, json=transaction)


@app.route('/sendmoney', methods=['GET', 'POST'])
@login_required
def sendmoney():
	external_transfer = ExternalTransferForm()

	if request.method == 'POST':
		if external_transfer.validate_on_submit():
			amount = external_transfer.amount.data

			if amount < 0.01: # Check if user is trying to send 0 or a negative amount
				flash('You must send more than $0!', 'warning')
				return redirect(url_for('sendmoney'))

			if decimal_check(amount) > 2: # Make sure user only inputs 2 decimal places
				flash('Please only enter 2 decimal places!', 'warning')
				return redirect(url_for('sendmoney'))

			balance_after_transaction = current_user.balance - amount # Check if user will send more than their balance
			if balance_after_transaction <= 0:
				flash('You do not have enough funds for that transaction', "warning")
				return redirect(url_for('sendmoney'))

			transaction = {}
			transaction['bank'] = 'Soseki Bank'
			transaction['sender_name'] = "{0} {1}".format(current_user.first_name, current_user.last_name)
			transaction['sender_email'] = current_user.email
			transaction['recipient_email'] = external_transfer.email.data
			transaction['amount'] = str(external_transfer.amount.data)

			r = my_request(transaction)

			if r.status_code == 200:

				user_data = r.json()

				current_user.balance -= external_transfer.amount.data

				about_recipient = "{0} <{1}> at {2}".format(user_data['data']['recipient_name'], user_data['data']['recipient_email'], user_data['data']['bank'])
				about_sender = "{0} <{1}>".format(transaction['sender_name'], transaction['sender_email'])

				sender_transaction_log = TransactionLog(amount=external_transfer.amount.data, from_account=about_sender, to_account=about_recipient, user_id=current_user.id, positive=False)

				db.session.add(sender_transaction_log)
				db.session.commit()

				flash('Successfully sent an external transfer', 'success')
				return redirect(url_for('soseki'))

			else:
				flash('Could not find user based on the email given, try again!', 'success')
				return redirect(url_for('sendmoney'))

	context = {
		'user': current_user,
		'external_transfer':external_transfer,
		'title': 'Send Money Externally',
	}
	return render_template('external.html', **context)


@app.route('/receivemoney', methods=['GET', 'POST'])
def receivemoney():

	transaction = request.get_json('transaction')
	user = User.query.filter_by(email=transaction['recipient_email']).first()

	if user:
		amount = Decimal(transaction['amount'])
		user.balance += amount

		about_recipient = "{0} {1} <2>".format(user.first_name, user.last_name, user.email)
		about_sender = "{0} <{1}> at {2}".format(transaction['sender_name'], transaction['sender_email'], transaction['bank'])
		transaction_log = TransactionLog(amount=amount, from_account=about_sender, to_account=about_recipient, user_id=user.id, positive=True)

		db.session.add(transaction_log)
		db.session.commit()

		user_data = {}
		user_data['recipient_name'] = "{0} {1}".format(user.first_name, user.last_name)
		user_data['recipient_email'] = user.email
		user_data['bank'] = 'Soseki Bank'

		return jsonify({'data': user_data}), 200

	else:
		return jsonify({'user': 'does not exist!'}), 400






