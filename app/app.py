import os
import string
import secrets
from flask import Flask, request, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  
db_path = os.path.join(os.path.dirname(__file__), 'users.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    registration_key = db.Column(db.String(120), unique=True, nullable=False)

class RegistrationKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)

def generate_registration_key(length=16):
    characters = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(characters) for _ in range(length))
    return key


@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', username=user.username)
    return 'Home Page'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)
            flash('Login successful', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    return render_template('dashboard.html', username=user.username)

@app.route('/generate_key', methods=['GET', 'POST'])
def generate_key():
    if request.method == 'POST':
        duration = int(request.form['duration'])  
        num_keys = int(request.form['num_keys'])    
        keys_generated = []

        for _ in range(num_keys):
            key = generate_registration_key() 

            existing_key = RegistrationKey.query.filter_by(key=key).first()

            if not existing_key:
                new_key = RegistrationKey(key=key)
                db.session.add(new_key)
                db.session.commit()
                keys_generated.append(key)

        flash(f'{num_keys} registration keys generated successfully for {duration} days', 'success')
        return render_template('generate_key.html', keys_generated=keys_generated)

    return render_template('generate_key.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        registration_key = request.form['registration_key']

        valid_registration_key = RegistrationKey.query.filter_by(key=registration_key, used=False).first()

        if valid_registration_key:
            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                flash('Username already taken', 'error')
            else:
                new_user = User(username=username, password=generate_password_hash(password), registration_key=registration_key)
                db.session.add(new_user)
                db.session.commit()
                
                
                valid_registration_key.used = True
                db.session.commit()
                
                flash('Registration successful', 'success')
                return redirect(url_for('login'))
        else:
            flash('Invalid registration key or key has already been used', 'error')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
