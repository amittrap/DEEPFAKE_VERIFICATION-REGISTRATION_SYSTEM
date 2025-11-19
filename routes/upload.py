from flask import request, redirect
from models.user import User
from models.image_record import ImageRecord
from extensions import db
from werkzeug.utils import secure_filename
import os
import hashlib

UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

@app.route('/upload', methods=['POST'])
def upload():
    email = request.form['email']
    age = int(request.form['age'])
    gender = request.form['gender']
    occupation = request.form['occupation']
    file = request.files['image']

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    image_hash = hash_file(filepath)

    # Get or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, age=age, gender=gender, occupation=occupation)
        db.session.add(user)
        db.session.commit()

    # Create ImageRecord
    image_record = ImageRecord(user_id=user.id, image_filename=filename, image_hash=image_hash)
    db.session.add(image_record)
    db.session.commit()

    return redirect('/success')  # or wherever you want
