import tensorflow as tf

# 1. Load your existing Keras model
model = tf.keras.models.load_model("model/Xception_deepfake_model.keras")

# 2. Create converter
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# (optional) enable basic optimizations to reduce size
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# 3. Convert
tflite_model = converter.convert()

# 4. Save TFLite model
output_path = "model/deepfake_xception.tflite"
with open(output_path, "wb") as f:
    f.write(tflite_model)

print("Saved TFLite model to", output_path)
