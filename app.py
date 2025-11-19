from flask import Flask
from extensions import db, mail
from tensorflow.keras.models import load_model
import os

def create_app():
    app = Flask(__name__)

    # Config inside the function, where `app` exists
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') or 'your-email@gmail.com'
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') or 'your-email-password'

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Load Deepfake Detection Model
    model_path = os.path.join('model', 'Xception_deepfake_model.keras')
    app.model = load_model(model_path)

    # Register blueprints
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp)

    return app
