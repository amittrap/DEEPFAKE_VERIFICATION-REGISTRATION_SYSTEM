# globals.py
import os
from tensorflow.keras.models import load_model

# Build an absolute path so it works in Linux containers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "Xception_deepfake_model.keras")

# Load the model globally once
model = load_model(MODEL_PATH)
