import os
from flask import Flask
from extensions import db, mail
from globals import model as deepfake_model  # use the globally loaded model


def create_app():
    app = Flask(__name__)

    # ---- Core config (read from environment for deployment) ----
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')

    # DB: use env var if present (Railway / production), else fallback to local SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///users.db'  # local default
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ---- Mail config (all from env, with safe defaults) ----
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # set in .env / Railway
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # set in .env / Railway

    # If you don't care about sending real emails yet, keep this True in Railway
    app.config['MAIL_SUPPRESS_SEND'] = os.getenv('MAIL_SUPPRESS_SEND', 'True').lower() == 'true'

    # ---- Initialize extensions ----
    db.init_app(app)
    mail.init_app(app)

    # ---- Attach Deepfake Detection Model (already loaded in globals.py) ----
    app.model = deepfake_model

    # ---- Register blueprints ----
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp)

    return app
