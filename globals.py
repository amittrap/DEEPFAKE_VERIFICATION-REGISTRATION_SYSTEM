import os
from tensorflow.keras.models import load_model

# Load the model once, globally
model_path = os.path.join('model', 'Xception_deepfake_model.keras')
model = load_model(model_path)
