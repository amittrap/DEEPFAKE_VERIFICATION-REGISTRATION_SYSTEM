from app import create_app
from extensions import db
from models.admin import Admin

app = create_app()

with app.app_context():
    admin = Admin(username='amit')
    admin.set_password('1234')  # change this to your desired password
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully.")
