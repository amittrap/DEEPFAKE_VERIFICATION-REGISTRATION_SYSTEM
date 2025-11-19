from tensorflow.keras.models import load_model
from utils.predict import predict_image
from utils.hash_utils import get_image_hash
from blockchain.interact import store_image_hash, verify_image_hash

import os
from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User
from models.image_record import ImageRecord

# Load ML model once
model = load_model('model/Xception_deepfake_model.keras')

backend_bp = Blueprint('backend', __name__)

@backend_bp.route('/analyze', methods=['POST'])
def analyze_image():
    try:
        image = request.files.get('image')
        if not image:
            return jsonify({'error': '⚠️ No image provided'}), 400

        # Ensure temp directory exists
        os.makedirs('temp', exist_ok=True)
        temp_path = os.path.join('temp', image.filename)
        image.save(temp_path)

        # Generate unique hash
        hash_value = get_image_hash(temp_path)

        # Extract optional user data
        email = request.form.get('email')
        age = request.form.get('age')
        gender = request.form.get('gender')
        occupation = request.form.get('occupation')

        # -----------------------------
        # 1️⃣ Blockchain-first verification
        # -----------------------------
        exists, details = verify_image_hash(hash_value)
        if exists:
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return jsonify({
                'status': 'real-verified',
                'hash': hash_value,
                'message': '✔️ Image verified as REAL and already on blockchain.',
                'blockchain_details': details
            }), 200

        # -----------------------------
        # 2️⃣ Run ML model only if hash is new
        # -----------------------------
        label, confidence = predict_image(model, temp_path)

        # -----------------------------
        # 3️⃣ Save image permanently
        # -----------------------------
        permanent_dir = 'static/images'
        os.makedirs(permanent_dir, exist_ok=True)
        permanent_filename = f"{hash_value}.png"
        permanent_path = os.path.join(permanent_dir, permanent_filename)
        os.rename(temp_path, permanent_path)

        # -----------------------------
        # 4️⃣ Store user & record in DB (research only)
        # -----------------------------
        user = None
        if email and age and gender and occupation:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    age=int(age),
                    gender=gender,
                    occupation=occupation
                )
                db.session.add(user)
                db.session.flush()

        new_record = ImageRecord(
            user_id=user.id if user else None,
            image_filename=permanent_filename,
            image_hash=hash_value,
            label=label.lower(),
            confidence=confidence
        )
        db.session.add(new_record)
        db.session.commit()

        # -----------------------------
        # 5️⃣ Blockchain storage for REAL images
        # -----------------------------
        if label.lower() == 'real':
            store_image_hash(hash_value, name=occupation or "Anonymous", email=email or "unknown@example.com")
            status = 'real-new'
            message = '✅ Image verified as REAL and stored on blockchain.'
        else:
            status = 'fake'
            message = '⚠️ Image detected as FAKE (Deepfake).'

        return jsonify({
            'status': status,
            'hash': hash_value,
            'confidence': round(confidence, 4),
            'label': label.lower(),
            'message': message,
            'image_url': f"/static/images/{permanent_filename}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
