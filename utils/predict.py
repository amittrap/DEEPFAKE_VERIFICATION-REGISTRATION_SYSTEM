# utils/predict.py
import numpy as np
from tensorflow.keras.preprocessing import image

IMG_SIZE = (299, 299)  # Xception input size


def _preprocess_image(image_path: str) -> np.ndarray:
    """Load image from disk and prepare a batch of 1 for the model."""
    img = image.load_img(image_path, target_size=IMG_SIZE)
    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0).astype("float32")
    return x


def _predict_with_keras(model, x: np.ndarray) -> np.ndarray:
    preds = model.predict(x)[0]
    return np.array(preds)


def _predict_with_tflite(interpreter, x: np.ndarray) -> np.ndarray:
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    x_cast = x.astype(input_details[0]["dtype"])
    interpreter.set_tensor(input_details[0]["index"], x_cast)
    interpreter.invoke()

    preds = interpreter.get_tensor(output_details[0]["index"])[0]
    return np.array(preds)


def _decode_binary_preds(preds: np.ndarray):
    """
    Convert raw model output to (label, confidence).

    Your log says output is shape (None, 1), so it's a single sigmoid neuron:
      preds = [p_fake]
    """
    preds = preds.ravel()

    if preds.size == 1:
        p_fake = float(preds[0])
        if p_fake >= 0.5:
            return "fake", p_fake
        else:
            return "real", 1.0 - p_fake

    # Fallback if something unexpected happens
    return "fake", 0.5


def predict_image(model_obj, image_path: str):
    """
    Main API used by your routes.

    Returns:
        label: "real" or "fake"
        confidence: float in [0, 1]
    If model_obj is None, returns (None, None).
    """
    if model_obj is None:
        return None, None

    x = _preprocess_image(image_path)

    if hasattr(model_obj, "predict"):
        # Keras model
        preds = _predict_with_keras(model_obj, x)
    else:
        # TFLite Interpreter
        preds = _predict_with_tflite(model_obj, x)

    label, confidence = _decode_binary_preds(preds)
    return label, confidence
