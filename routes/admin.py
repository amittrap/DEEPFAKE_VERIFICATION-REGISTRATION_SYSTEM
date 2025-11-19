from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.admin import Admin
from models.user import User
from extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html')


@admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    username = session.get('admin_username', '')

    # ✅ Fetch all users with their images
    users = User.query.all()

    # DEBUG: print to terminal to confirm
    print(f"[DEBUG] Found {len(users)} users in database.")
    for u in users:
        print(f"[DEBUG] User: {u.email}, Images: {len(u.images)}")

    return render_template('admin.html', username=username, users=users)


@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))
