### Getting Started With Soseki/Murasaki Bank
This repository needs to be downloaded with https://github.com/domdit/MurasakiBank

#### 1. Clone Repository
- Clone the repository to your local machine. This, and every subsequent step needs to be done for both soseki and murasaki bank repositories. 

```
git clone https://github.com/domdit/SosekiBank.git your/desired/path/SosekiBank

git clone https://github.com/domdit/MurasakiBank.git your/desired/path/MurasakiBank
```
- Install dependencies
on macOS and Linux:
```
pip install -r requirements.txt
```
on Windows:
```
python -m pip install -r requirements.txt
```
- Configure Environment Variables
Configure necessary environment variables by editing your bashrc file `nano ~/.bashrc`.

Secret Key -You need to set a secret key for this Flask app as well as set the SQLAlchemy Database URI. The Database URI should match what is written below, while the secret key can be anything you want. Go [here](https://stackoverflow.com/questions/34902378/where-do-i-get-a-secret-key-for-flask/34903502) for more info on secret keys and Flask

```
export SECRET_KEY="your_secret_key"
```
- Running Flask
you need to set some more environment variables before running flask. While in your /SosekiBank/ directory, type
```
set FLASK_APP=run.py
set FLASK_ENV=development
```
then you can run the application by:

for Soseki Bank
```
python -m flask run -p 5000
```

for Murasaki Bank
```
python -m flask run -p 3000
```
** the -p option sets the port to 5000, while Flask natively runs on port 5000, we set Murasaki bank up on port 3000 so both can run simultaneously and transfer money between eachother

Soseki bank should now be up and running on your local machine

#### running tests
you can run tests.py in your /SosekiBank/ directory

#### creating database and admin user
** this step is only necessary if database gets deleted!
While, you can create a user at /signup you may need to set up an admin user if the database doesn't exist! first try
admin email: admin@email.com
admin pass: password

if all else fails:
```
python
>>>from bank import db
>>>db.create_all()
>>> from bank import bcrypt
>>>from bank.models import User
>>> hash_password = bcrypt.generate_password_hash('your password').decode('utf-8')
>>>admin = User(email='your email', password=hash_password, first_name='your first name', last_name='your last name', balance=1000, admin=True )
>>>db.session.add(admin)
>>>db,session.commit
```

#### routes
*** probably self explanatory
##### /login
logs in user
##### /signup
signs up user
##### /soseki(or /murasaki)
main page for bank app, login required, can transfer money internally here, see balance, and view user's transaction log
##### /soseki(or /murasaki)/admin
here you can see all bank accounts and their transactions, balances, and emails. you need admin priveledge to access this page
##### /sendmoney
allows you to send money (externally) to murasaki bank through an api call, login required
##### /receivemoney
the route the gets the api call from the other bank and receives the money adn transfers it into recipient bank, login required
