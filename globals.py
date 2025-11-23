# globals.py
import os
import logging
from tensorflow.keras.models import load_model

# Simple logger
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "Xception_deepfake_model.keras")

# Optional: model download URL from env (we’ll use later)
MODEL_URL = os.getenv("MODEL_URL")

model = None  # default

def _load_model_from_disk():
    """Try loading the Keras model from disk."""
    global model
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"[globals] Model file not found at {MODEL_PATH}")
        return

    try:
        logger.info(f"[globals] Loading model from {MODEL_PATH}...")
        model = load_model(MODEL_PATH)
        logger.info("[globals] Model loaded successfully.")
    except Exception as e:
        logger.error(f"[globals] Failed to load model: {e}")
        model = None


# Try to load immediately (if file exists)
os.makedirs(MODEL_DIR, exist_ok=True)
_load_model_from_disk()
