from bank.models import User
from flask_wtf import FlaskForm
from flask import flash
from wtforms import StringField, DecimalField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError


class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
	first_name = StringField('First Name', validators=[DataRequired()])
	last_name = StringField('Last Name', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one.')


class InternalTransferForm(FlaskForm):
	email = StringField('Email of Recipient', validators=[DataRequired(), Email()])
	amount = DecimalField('Amount to Transfer', places=2, validators=[DataRequired()], render_kw={'step': '.01'})
	submit = SubmitField('Transfer')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()

		if not user:
			flash('There is no user with that email address in our database, please try again!', 'warning')
			raise ValidationError('There is no user with that email address.')


class ExternalTransferForm(FlaskForm):
	email = StringField('Email of Recipient', validators=[DataRequired(), Email()])
	amount = DecimalField('Amount to Transfer', places=2, validators=[DataRequired()], render_kw={'step': '.01'})
	submit = SubmitField('Transfer')