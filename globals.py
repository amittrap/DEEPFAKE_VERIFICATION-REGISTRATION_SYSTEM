# globals.py
import os
import logging

# We only need TensorFlow Lite Interpreter
try:
    import tensorflow as tf
except ImportError:
    tf = None

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

# Path to the quantized TFLite model
TFLITE_PATH = os.path.join(MODEL_DIR, "xception_deepfake_quant.tflite")

# Optional: URL where TFLITE model could be downloaded from (future use)
MODEL_URL = os.getenv("MODEL_URL")

# This variable will hold the loaded TFLite interpreter
model = None


def _load_tflite_model():
    """Load TFLite quantized model if available."""
    global model

    if tf is None:
        logger.error("[globals] TensorFlow is not installed — TFLite model cannot load.")
        model = None
        return

    if not os.path.exists(TFLITE_PATH):
        logger.warning(f"[globals] TFLite model not found at {TFLITE_PATH}")
        model = None
        return

    try:
        logger.info(f"[globals] Loading TFLite model from {TFLITE_PATH}...")
        interpreter = tf.lite.Interpreter(model_path=TFLITE_PATH)
        interpreter.allocate_tensors()
        model = interpreter
        logger.info("[globals] TFLite model loaded successfully.")
    except Exception as e:
        logger.error(f"[globals] Failed to load TFLite model: {e}")
        model = None


# Ensure model folder exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Load the TFLite model on startup
_load_tflite_model()
