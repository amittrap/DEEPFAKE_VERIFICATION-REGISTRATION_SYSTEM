# convert_to_tflite.py
import pathlib
import tensorflow as tf

# Paths
MODEL_PATH = pathlib.Path("model") / "Xception_deepfake_model.keras"
OUT_DIR = pathlib.Path("model")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TFLITE_PATH = OUT_DIR / "xception_deepfake_quant.tflite"

print(f"[+] Loading Keras model from: {MODEL_PATH}")
model = tf.keras.models.load_model(str(MODEL_PATH))

# Dynamic-range quantization (smaller model, usually tiny accuracy drop)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

print("[+] Converting to quantized TFLite… this may take a few minutes")
tflite_model = converter.convert()

# Save TFLite model
with open(TFLITE_PATH, "wb") as f:
    f.write(tflite_model)

orig_size = MODEL_PATH.stat().st_size / (1024 * 1024)
tflite_size = TFLITE_PATH.stat().st_size / (1024 * 1024)

print(f"[✓] Saved TFLite model to: {TFLITE_PATH}")
print(f"    Original Keras: {orig_size:.1f} MB")
print(f"    TFLite (quant): {tflite_size:.1f} MB")
