from flask import Blueprint, render_template, request
import os
from pathlib import Path

from utils.hash_utils import get_image_pixel_hash_from_stream
from utils.predict import predict_image
from blockchain.interact import store_result, get_result
from models.user import User
from models.image_record import ImageRecord
from extensions import db
from globals import model

frontend_bp = Blueprint('frontend', __name__)

# Project root (this file is in routes/, so go two levels up if needed)
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
STATIC_IMAGES_DIR = BASE_DIR / "static" / "images"


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


def _normalize_onchain_info(raw):
    """
    Take whatever get_result(...) returns (dict, tuple, or None)
    and normalize it to:

      (info_dict_or_none, is_present_bool)

    info_dict format:
      {
        "label": str | None,
        "confidence": float | None,   # 0–1 if available
        "timestamp": int | None,
        "recorder": str | None,
      }

    is_present_bool tells us whether there is a REAL stored record
    on chain for this hash.
    """
    if raw is None:
        return None, False

    # Case 1: our interact.get_result already returns a dict
    if isinstance(raw, dict):
        label = raw.get("label")
        conf = raw.get("confidence")
        ts = raw.get("timestamp")
        rec = raw.get("recorder") or raw.get("uploader")

        # Try to normalize confidence to 0–1 float
        conf_val = None
        if conf is not None:
            try:
                conf_val = float(conf)
                # If on-chain is stored as 0–10000 integer but not scaled yet
                if conf_val > 1.0:
                    # heuristic: treat as scaled if <= 10000
                    if conf_val <= 10000:
                        conf_val = conf_val / 10000.0
                    else:
                        conf_val = 1.0
            except (TypeError, ValueError):
                conf_val = None

        # Determine if this looks like an empty record
        empty = (
            (label is None or str(label).strip() == "")
            and (ts in (None, 0))
        )
        info = {
            "label": label,
            "confidence": conf_val,
            "timestamp": ts,
            "recorder": rec,
        }
        return (info, not empty)

    # Case 2: raw tuple/list directly from contract
    # Expected shape: (contentHash, label, confidence, timestamp, recorder)
    if isinstance(raw, (tuple, list)) and len(raw) >= 5:
        _, label, conf_scaled, ts, rec = raw

        # check for "empty" default struct (no record)
        is_zero_addr = (
            isinstance(rec, str)
            and rec.lower() == "0x0000000000000000000000000000000000000000"
        )
        if (label == "" or label is None) and conf_scaled == 0 and ts == 0 and is_zero_addr:
            return None, False

        # Otherwise, it's a real stored record
        conf_val = None
        try:
            conf_val = float(conf_scaled) / 10000.0
        except (TypeError, ValueError):
            conf_val = None

        info = {
            "label": label,
            "confidence": conf_val,
            "timestamp": ts,
            "recorder": rec,
        }
        return info, True

    # Any other unexpected type -> treat as "not present"
    return None, False


def log_image_if_new(email, age, gender, occupation,
                     image_filename, image_hash, label, confidence):
    """
    Logging ONLY (no verification logic):

    - If image_hash already exists in ImageRecord -> do NOTHING.
    - If not -> create User (if needed) and insert ONE ImageRecord row.
    - DB is never used for detection/verification, only for storing history once.
    """
    if not image_hash or not label:
        return

    existing = ImageRecord.query.filter_by(image_hash=image_hash).first()
    if existing:
        return

    # Ensure user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            age=int(age),
            gender=gender,
            occupation=occupation,
        )
        db.session.add(user)
        db.session.flush()  # get user.id

    rec = ImageRecord(
        user_id=user.id,
        image_filename=image_filename,
        image_hash=image_hash,
        label=label.lower(),
        confidence=confidence if confidence is not None else 0.0,
    )
    db.session.add(rec)
    db.session.commit()


@frontend_bp.route('/')
def home():
    return render_template('index.html')


@frontend_bp.route('/analyze', methods=['POST'])
def analyze_frontend():
    """
    Blockchain + ML verification; DB only for one-time logging.

    1. Compute hash.
    2. Check blockchain using get_result():
       - If record exists -> image is REAL & already verified (show that).
       - If not -> run ML to decide REAL/FAKE.
    3. REAL and not yet on-chain -> store_result() and show "registered & authentic".
    4. FAKE -> never store on blockchain, show "fake" message.
    5. After verification, log hash in DB once (if not already logged).
    """
    image = request.files.get('image')
    if not image or image.filename.strip() == '':
        return "⚠️ No selected image", 400

    # Form data
    email = request.form.get('email')
    age = request.form.get('age')
    gender = request.form.get('gender')
    occupation = request.form.get('occupation')

    if not all([email, age, gender, occupation]):
        return "⚠️ Please fill in all fields", 400

    # Ensure folders exist (absolute paths)
    TEMP_DIR.mkdir(exist_ok=True)
    STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    temp_path = TEMP_DIR / image.filename
    image.save(temp_path)

    # 1️⃣ Compute image hash
    with open(temp_path, 'rb') as f:
        hash_value = get_image_pixel_hash_from_stream(f)  # 64-char hex expected

    ext = os.path.splitext(image.filename)[1]
    new_filename = f"{hash_value}{ext}"
    permanent_path = STATIC_IMAGES_DIR / new_filename

    # Ensure image is stored in static (for display)
    if permanent_path.exists():
        temp_path.unlink(missing_ok=True)
    else:
        os.replace(temp_path, permanent_path)

    # Variables
    label = None
    confidence = None
    label_for_db = None
    conf_for_db = None
    html = "<h2>Result:</h2>"

    # 2️⃣ Prepare hash for blockchain
    content_hash_bytes32 = None
    try:
        content_hash_bytes32 = _hex_to_bytes32(hash_value)
    except Exception:
        content_hash_bytes32 = None
        html += (
            '<p style="color:orange;"><strong>⚠️ Could not convert hash for blockchain; '
            'using ML verification only.</strong></p>'
        )

    # 3️⃣ Check blockchain first – source of truth for REAL images
    raw_onchain = None
    if content_hash_bytes32 is not None:
        try:
            raw_onchain = get_result(content_hash_bytes32)
        except Exception:
            raw_onchain = None
            html += (
                '<p style="color:orange;"><strong>⚠️ Blockchain query failed; '
                'falling back to ML-only verification.</strong></p>'
            )

    onchain_info, is_onchain = _normalize_onchain_info(raw_onchain)

    # 4️⃣ CASE 1: Hash is already on-chain → image REAL & verified
    if is_onchain:
        html += (
            '<p style="color:green;"><strong>✔️ Image is REAL and already present '
            'on the blockchain (previously verified as authentic).</strong></p>'
        )

        chain_label = None
        chain_conf_val = None
        chain_ts = None
        recorder = None

        if onchain_info is not None:
            chain_label = onchain_info.get("label")
            chain_conf_val = onchain_info.get("confidence")
            chain_ts = onchain_info.get("timestamp")
            recorder = onchain_info.get("recorder")

        if chain_label is not None:
            html += f"<p><strong>On-chain label:</strong> {chain_label}</p>"

        if chain_conf_val is not None:
            html += f"<p><strong>On-chain confidence:</strong> {chain_conf_val:.2%}</p>"

        if chain_ts is not None:
            html += f"<p><strong>On-chain timestamp:</strong> {chain_ts}</p>"

        if recorder is not None:
            html += f"<p><strong>On-chain recorder:</strong> {recorder}</p>"

        # For DB logging we know it's real from chain
        label_for_db = "real"
        conf_for_db = chain_conf_val if chain_conf_val is not None else 1.0

        html += f"<p><strong>Image Hash:</strong> {hash_value}</p>"
        html += f'<img src="/static/images/{new_filename}" width="200">'

        # 🗄️ Logging (no effect on verification)
        log_image_if_new(
            email=email,
            age=age,
            gender=gender,
            occupation=occupation,
            image_filename=new_filename,
            image_hash=hash_value,
            label=label_for_db,
            confidence=conf_for_db,
        )

        return html

    # 5️⃣ CASE 2: Hash NOT on-chain (or chain unavailable) → run ML

    label, confidence = predict_image(model, str(permanent_path))
    label_for_db = label.lower()
    conf_for_db = confidence

    # 6️⃣ Decide blockchain action based on model label
    if label.lower() == "real" and content_hash_bytes32 is not None:
        try:
            receipt = store_result(
                content_hash_bytes32,
                label=label.lower(),
                confidence=confidence,
            )
            tx_hash = receipt.transactionHash.hex()

            html += (
                '<p style="color:green;"><strong>✅ Image is REAL, registered on '
                'the blockchain and verified as authentic.</strong></p>'
            )
            html += f'<p><strong>Blockchain Tx Hash:</strong> <code>{tx_hash}</code></p>'
        except Exception as e:
            html += (
                '<p style="color:orange;"><strong>⚠️ Image is REAL but could not be '
                'stored on blockchain.</strong></p>'
            )
            html += f"<p><small>Error: {str(e)}</small></p>"

    elif label.lower() == "real":
        # Real, but we couldn't talk to chain / convert hash
        html += (
            '<p style="color:green;"><strong>✅ Image is REAL (verified by model), '
            'but hash format or blockchain connectivity prevented registration.</strong></p>'
        )
    else:
        # FAKE → never store on blockchain
        html += (
            '<p style="color:red;"><strong>⚠️ Image is FAKE (Deepfake detected) and '
            'cannot be registered on the blockchain.</strong></p>'
        )

    # Common info for this branch
    html += f"<p><strong>Model Label:</strong> {label.title()}</p>"
    html += f"<p><strong>Model Confidence:</strong> {confidence:.2%}</p>"
    html += f"<p><strong>Image Hash:</strong> {hash_value}</p>"
    html += f'<img src="/static/images/{new_filename}" width="200">'

    # 🗄️ Logging step (only if hash not seen before in DB)
    log_image_if_new(
        email=email,
        age=age,
        gender=gender,
        occupation=occupation,
        image_filename=new_filename,
        image_hash=hash_value,
        label=label_for_db,
        confidence=conf_for_db,
    )

    return html
