from bank import db, app, bcrypt
from bank.models import User
import unittest
from unittest import mock
import json


class FakeResponse(object):
	def __init__(self, status_code, json=None):
		self.status_code = status_code
		self.data = json or {}

	def json(self):
		return json.loads(self.data)


class FlaskTestCase(unittest.TestCase):

	def setUp(self):
		app.config['TESTING'] = True
		app.config['WTF_CSRF_ENABLED'] = False
		app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_site.db'
		self.app = app.test_client()
		db.create_all()
		db.session.commit()

		#add users to the db for tests
		hash_password = bcrypt.generate_password_hash('password').decode('utf-8')
		test_user_1 = User(email='test1@gmail.com', password=hash_password, first_name='test',
					last_name='test', balance=1000, admin=False)
		test_user_2 = User(email='test2@gmail.com', password=hash_password, first_name='test',
					last_name='test', balance=1000, admin=False)
		test_user_3 = User(email='test3@gmail.com', password=hash_password, first_name='test',
						   last_name='test', balance=1000, admin=True)
		external_test_user = User(email='external@gmail.com', password=hash_password, first_name='test',
						   last_name='test', balance=1000, admin=True)

		db.session.add(test_user_1)
		db.session.add(test_user_2)
		db.session.add(test_user_3)
		db.session.add(external_test_user)
		db.session.commit()

		self.test_user_1 = User.query.filter_by(email='test1@gmail.com').first()
		self.test_user_2 = User.query.filter_by(email='test2@gmail.com').first()
		self.test_user_3 = User.query.filter_by(email='test3@gmail.com').first()
		self.external_test_user = User.query.filter_by(email='external@gmail.com').first()

	# Check Flask was set up
	def test_index(self):
		tester = self.app
		response = tester.get('/', content_type='html/text')
		self.assertEqual(response.status_code, 200)

	# Check login page loads correctly
	def test_login_page_loads(self):
		tester = self.app
		response = tester.get('/login', content_type='html/text')
		self.assertTrue(b'Log In to Soseki Bank' in response.data)

	# Check signup page loads correctly
	def test_signup_page_loads(self):
		tester = self.app
		response = tester.get('/signup', content_type='html/text')
		self.assertTrue(b'Sign Up For Soseki Bank' in response.data)

	# Check that I can sign up as a test user
	def test_signup_works(self):
		tester = self.app
		response = tester.post('/signup', data=dict(first_name='test', last_name='customer', email='test@email.com',
													password='password', confirm_password='password'), follow_redirects=True)
		self.assertIn(b'Thank you for signing up', response.data)

	def test_signup_fails_when_wrong_confirm_password(self):
		tester = self.app
		response = tester.post('/signup', data=dict(first_name='test', last_name='customer', email='test@email.com',
													password='password', confirm_password='passw0rd'), follow_redirects=True)
		self.assertIn(b'Field must be equal to password.', response.data)

	# create user and make sure they can log in
	def test_login_works(self):
		hash_password = bcrypt.generate_password_hash('password').decode('utf-8')
		user = User(email='test@gmail.com', password=hash_password, first_name='test',
					last_name='test', balance=1000, admin=False)
		db.session.add(user)
		db.session.commit()

		tester = self.app
		response = tester.post('/login', data=dict(email='test@gmail.com', password='password'), follow_redirects=True)
		self.assertIn(b'Hello', response.data)

	# Check that the login fails when wrong data
	def test_login_fails(self):
		tester = self.app
		response = tester.post('/login', data=dict(email='x@email.com', password='password'), follow_redirects=True)
		self.assertIn(b'The email or password you entered was incorrect, please try again', response.data)

	# Check logout route works
	def test_logout(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_2.email, password='password'), follow_redirects=True)
		response = tester.get('/logout', content_type='html/text', follow_redirects=True)
		self.assertIn(b'You have successfully logged out', response.data)

	# Test admin log in works
	def test_admin_login(self):
		tester = self.app
		response = tester.post('/login', data=dict(email=self.test_user_3.email, password='password'), follow_redirects=True)
		self.assertIn(b'Admin Panel', response.data)

	# Test admin panel shows a list of all users
	def test_admin_panel(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_3.email, password='password'), follow_redirects=True)
		response = tester.get('/soseki/admin', content_type='html/text')
		self.assertIn(b'View Transactions', response.data)

	# Test to make sure money is transferred internally correctly
	def test_internal_money_transfer_send(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)

		# Test money was taken out of sender's account
		response = tester.post('/soseki', data=dict(email=self.test_user_2.email, amount=200), follow_redirects=True)
		self.assertIn(b'$800', response.data)

		# Test money was added to recipient's account
		response = tester.post('/login', data=dict(email=self.test_user_2.email, password='password'), follow_redirects=True)
		self.assertIn(b'$1200', response.data)

	# test transfer fails if wrong email is entered
	def test_internal_money_transfer_wrong_email(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/soseki', data=dict(email='wrong@email.com', amount=200), follow_redirects=True)
		self.assertIn(b'There is no user with that email address in our database, please try again!', response.data)

	# Test if sending a negative amount internally fails
	def test_internal_money_transfer_negative(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/soseki', data=dict(email=self.test_user_2.email, amount=-200), follow_redirects=True)
		self.assertIn(b'You must send more than $0!', response.data)

	# Test if sending too many decimal places internally fails
	def test_internal_money_transfer_too_many_decimals(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/soseki', data=dict(email=self.test_user_2.email, amount=200.111), follow_redirects=True)
		self.assertIn(b'Please only enter 2 decimal places!', response.data)

	# Test if sending more money than your balance fails
	def test_internal_money_transfer_too_much_money(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/soseki', data=dict(email=self.test_user_2.email, amount=20000),
							   follow_redirects=True)
		self.assertIn(b'You do not have enough funds for that transaction', response.data)

	# Test if logs are created
	def test_internal_money_transfer_transaction_log(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)

		# test if sender log is created
		response = tester.post('/soseki', data=dict(email=self.test_user_2.email, amount=20),
							   follow_redirects=True)
		self.assertIn(b'From:', response.data)

		# test if recipient log is created
		tester.post('/login', data=dict(email=self.test_user_2.email, password='password'), follow_redirects=True)
		self.assertIn(b'From:', response.data)

	# Test receive money fails when sent an email address not in the database
	def test_receive_external_money_transfer_wrong_email(self):
		# set up mock external transfer to receive from other bank
		transaction = {}
		transaction['bank'] = 'Other Bank'
		transaction['sender_name'] = "{0} {1}".format('mock', 'murasakimember')
		transaction['sender_email'] = 'mock@murasaki.com'
		transaction['recipient_email'] = 'wrong@email.com'
		transaction['amount'] = str(200)

		tester = self.app

		# check status code
		response = tester.post('/receivemoney?transaction=', json=transaction, follow_redirects=True)
		self.assertEqual(response.status_code, 400)

		# check 'user does not exist'
		self.assertIn(b'does not exist!', response.data)

	def test_send_external_money_transfer(self):
		tester = self.app

		user_data = {}
		user_data['recipient_name'] = "{0} {1}".format('test', 'user')
		user_data['recipient_email'] = 'test@email.com'
		user_data['bank'] = 'Murasaki Bank'

		with mock.patch('bank.routes.my_request', return_value=FakeResponse(200, json.dumps({'data': user_data}))):

			tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
			response = tester.post('/sendmoney', follow_redirects=True, data=dict(email='domdit@gmail.com', amount=20))

		self.assertIn(b'Successfully sent an external transfer', response.data)

	def test_send_external_money_transfer_wrong_email(self):
		tester = self.app

		user_data = {}
		user_data['recipient_name'] = "{0} {1}".format('test', 'user')
		user_data['recipient_email'] = 'test@email.com'
		user_data['bank'] = 'Soseki Bank'

		with mock.patch('bank.routes.my_request', return_value=FakeResponse(400, {'user': 'does not exist!'})):

			tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
			response = tester.post('/sendmoney', follow_redirects=True, data=dict(email='domdit@gmail.com', amount=20))

		self.assertIn(b'Could not find user based on the email given, try again!', response.data)


	def test_external_money_transfer_negative(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/sendmoney', data=dict(email=self.test_user_2.email, amount=-200), follow_redirects=True)
		self.assertIn(b'You must send more than $0!', response.data)

	# Test if sending too many decimal places internally fails
	def test_external_money_transfer_too_many_decimals(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/sendmoney', data=dict(email=self.test_user_2.email, amount=200.111),
							   follow_redirects=True)
		self.assertIn(b'Please only enter 2 decimal places!', response.data)

	# Test if sending more money than your balance fails
	def test_external_money_transfer_too_much_money(self):
		tester = self.app
		tester.post('/login', data=dict(email=self.test_user_1.email, password='password'), follow_redirects=True)
		response = tester.post('/sendmoney', data=dict(email=self.test_user_2.email, amount=20000),
							   follow_redirects=True)
		self.assertIn(b'You do not have enough funds for that transaction', response.data)

	# Tests if user can receive money externally properly
	def test_external_money_transfer_receive(self):

		# set up mock external transfer to receive from other bank
		transaction = {}
		transaction['bank'] = 'Other Bank'
		transaction['sender_name'] = "{0} {1}".format('mock', 'murasakimember')
		transaction['sender_email'] = 'mock@murasaki.com'
		transaction['recipient_email'] = self.external_test_user.email
		transaction['amount'] = str(200)

		tester = self.app

		# Make sure response code is 200 when receiving money
		response = tester.post('/receivemoney?transaction=', json=transaction, follow_redirects=True)
		self.assertEqual(response.status_code, 200)

		# Make sure the recipient received the money
		response = tester.post('/login', data=dict(email=self.external_test_user.email, password='password'), follow_redirects=True)
		self.assertIn(b'1200', response.data)

		# Make sure the log is properly updated
		response = tester.post('/login', data=dict(email=self.external_test_user.email, password='password'), follow_redirects=True)
		self.assertIn(b'Other Bank', response.data)

	def tearDown(self):
		db.session.remove()
		db.drop_all()


if __name__ == '__main__':
	unittest.main()