import os
from flask import Flask
from extensions import db, mail
from globals import model as deepfake_model  # use the globally loaded model


def create_app():
    app = Flask(__name__)

    # ---- Core config (read from environment for deployment) ----
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')

    # ---- Database config ----
    # Prefer Railway's Postgres DATABASE_URL, then optional SQLALCHEMY_DATABASE_URI,
    # and finally fall back to local SQLite for development.
    db_url = (
        os.getenv("DATABASE_URL")  # Railway / Postgres
        or os.getenv("SQLALCHEMY_DATABASE_URI")  # optional override
        or "sqlite:///users.db"  # local default
    )

    # SQLAlchemy expects "postgresql://" but some providers give "postgres://"
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

    # ✅ Ensure tables exist in the configured database (Postgres on Railway)
    with app.app_context():
        from models.user import User
        from models.image_record import ImageRecord
        from models.admin import Admin
        db.create_all()

    # ---- Attach Deepfake Detection Model (already loaded in globals.py) ----
    app.model = deepfake_model

    # ---- Register blueprints ----
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp)

    return app
