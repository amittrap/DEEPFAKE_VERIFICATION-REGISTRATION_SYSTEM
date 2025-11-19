from flask import Blueprint, render_template, request
import os
import hashlib

from utils.hash_utils import get_image_pixel_hash_from_stream
from utils.predict import predict_image
from blockchain.interact import store_result, get_result
from models.user import User
from models.image_record import ImageRecord
from extensions import db
from globals import model

frontend_bp = Blueprint('frontend', __name__)


def _hex_to_bytes32(hex_str: str) -> bytes:
    """
    Convert a 64-char hex string (or '0x' + 64) to 32-byte value for Solidity bytes32.
    """
    h = hex_str.strip().lower()
    if h.startswith("0x"):
        h = h[2:]
    if len(h) != 64:
        raise ValueError(f"image hash must be 64 hex chars (got {len(h)})")
    return bytes.fromhex(h)


@frontend_bp.route('/')
def home():
    return render_template('index.html')


@frontend_bp.route('/analyze', methods=['POST'])
def analyze_frontend():
    """Handles image upload, prediction, duplicate check, and blockchain storage."""
    image = request.files.get('image')
    if not image or image.filename.strip() == '':
        return "⚠️ No selected image", 400

    # Get form data
    email = request.form.get('email')
    age = request.form.get('age')
    gender = request.form.get('gender')
    occupation = request.form.get('occupation')

    if not all([email, age, gender, occupation]):
        return "⚠️ Please fill in all fields", 400

    os.makedirs('temp', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    temp_path = os.path.join('temp', image.filename)
    image.save(temp_path)

    # Compute pixel hash (this should give you a deterministic hex string)
    with open(temp_path, 'rb') as f:
        hash_value = get_image_pixel_hash_from_stream(f)  # e.g., 64-char hex

    ext = os.path.splitext(image.filename)[1]
    new_filename = f"{hash_value}{ext}"
    permanent_path = os.path.join('static/images', new_filename)

    # ✅ Global duplicate check (any user) in local DB
    existing_record = ImageRecord.query.filter_by(image_hash=hash_value).first()

    if existing_record:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return f"""
        <h2>Duplicate Submission Detected</h2>
        <p style="color:orange;"><strong>⚠️ This image already exists in the system.</strong></p>
        <p><strong>User:</strong> {existing_record.user.email}</p>
        <p><strong>Prediction:</strong> {existing_record.label.title()}</p>
        <p><strong>Confidence:</strong> {existing_record.confidence:.2%}</p>
        <p><strong>Hash:</strong> {existing_record.image_hash}</p>
        <p><strong>Submitted At:</strong> {existing_record.timestamp}</p>
        <img src="/static/images/{existing_record.image_filename}" width="200">
        """

    # 🔎 If new → Predict with ML model
    label, confidence = predict_image(model, temp_path)

    # Move image to permanent location
    if os.path.exists(permanent_path):
        os.remove(temp_path)
    else:
        os.rename(temp_path, permanent_path)

    # Ensure user exists in DB
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, age=int(age), gender=gender, occupation=occupation)
        db.session.add(user)
        db.session.flush()  # get user.id

    # Insert local DB record
    new_record = ImageRecord(
        user_id=user.id,
        image_filename=new_filename,
        image_hash=hash_value,
        label=label.lower(),
        confidence=confidence
    )
    db.session.add(new_record)
    db.session.commit()

    # Build result HTML
    html = "<h2>Result:</h2>"

    # 🌐 Blockchain integration (Sepolia)
    tx_hash = None
    onchain_info = None

    if label.lower() == 'real':
        # convert hex hash => bytes32 for contract
        try:
            content_hash_bytes32 = _hex_to_bytes32(hash_value)
        except Exception as e:
            # If hash format is wrong, don't crash the app; just skip blockchain
            html += f'<p style="color:orange;"><strong>⚠️ Could not convert hash for blockchain.</strong> ({e})</p>'
            content_hash_bytes32 = None

        if content_hash_bytes32 is not None:
            # Check if this hash already exists on-chain
            onchain_info = get_result(content_hash_bytes32)

            if onchain_info is None:
                # Not on-chain yet → store it
                try:
                    receipt = store_result(
                        content_hash_bytes32,
                        label=label.lower(),
                        confidence=confidence
                    )
                    tx_hash = receipt.transactionHash.hex()
                    html += '<p style="color:green;"><strong>✅ Image is REAL and stored on blockchain.</strong></p>'
                    html += f'<p><strong>Blockchain Tx Hash:</strong> <code>{tx_hash}</code></p>'
                except Exception as e:
                    # If blockchain write fails, still show ML result
                    html += '<p style="color:orange;"><strong>⚠️ Image is REAL but could not be stored on blockchain.</strong></p>'
                    html += f'<p><small>Error: {str(e)}</small></p>'
            else:
                html += '<p style="color:green;"><strong>✔️ Image is REAL and already on blockchain.</strong></p>'
                # Optionally show some on-chain metadata
                html += f"<p><strong>On-chain label:</strong> {onchain_info['label']}</p>"
                html += f"<p><strong>On-chain confidence:</strong> {onchain_info['confidence']:.2%}</p>"
    else:
        html += '<p style="color:red;"><strong>⚠️ Image is FAKE (Deepfake detected)</strong></p>'

    html += f"<p><strong>Model Confidence:</strong> {confidence:.2%}</p>"
    html += f"<p><strong>Image Hash:</strong> {hash_value}</p>"
    html += f'<img src="/static/images/{new_filename}" width="200">'

    return html
