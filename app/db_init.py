from app import create_app, db
from app.models import User, RegistrationKey

app = create_app()

with app.app_context():

    db.create_all()

    admin_user = User(username='admin', email='admin@example.com')
    admin_user.set_password('monke')
    db.session.add(admin_user)

    db.session.commit()

print("Database initialized successfully.")
