from bank import db
from flask_login import UserMixin
import datetime


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	first_name = db.Column(db.String(255), nullable=False)
	last_name = db.Column(db.String(255), nullable=False)
	admin = db.Column(db.Boolean, unique=False, default=False)
	balance = db.Column(db.Numeric(precision=10, scale=2, asdecimal=True, decimal_return_scale=2))
	logs = db.relationship('TransactionLog', backref='user', lazy=True)


class TransactionLog(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	amount = db.Column(db.Numeric(precision=10, scale=2, asdecimal=True, decimal_return_scale=2))
	from_account = db.Column(db.String(120), nullable=False)
	to_account = db.Column(db.String(120), nullable=False)
	positive = db.Column(db.Boolean, unique=False, default=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)