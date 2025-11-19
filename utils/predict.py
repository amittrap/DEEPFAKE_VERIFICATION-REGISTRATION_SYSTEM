from tensorflow.keras.utils import load_img, img_to_array
import numpy as np

def preprocess_image(img_path: str, target_size=(299, 299)) -> np.ndarray:
    """
    Load and preprocess an image for the deepfake detection model.

    Args:
        img_path (str): Path to the image file.
        target_size (tuple): Expected input size for the model (default: (299, 299)).

    Returns:
        np.ndarray: Preprocessed image tensor with shape (1, height, width, channels).
    """
    img = load_img(img_path, target_size=target_size)
    img_array = img_to_array(img)
    img_array = img_array / 255.0  # normalize to [0, 1]
    return img_array.reshape(1, *target_size, 3)

def predict_image(model, img_path: str):
    """
    Predict whether an image is Real or Deepfake.

    Args:
        model: Trained Keras model for deepfake detection.
        img_path (str): Path to the image file.

    Returns:
        tuple: (label (str), confidence (float))
            - label: "real" or "fake"
            - confidence: Probability score (float between 0 and 1)
    """
    img = preprocess_image(img_path)
    pred = float(model.predict(img)[0][0])  # sigmoid output between 0 and 1

    label = "real" if pred > 0.5 else "fake"
    confidence = pred if label == "real" else 1 - pred

    return label, confidence
