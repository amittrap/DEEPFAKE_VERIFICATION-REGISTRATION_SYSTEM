from tensorflow.keras.models import load_model
from utils.predict import predict_image
from utils.hash_utils import get_image_hash
from blockchain.interact import store_image_hash, verify_image_hash

# Load the trained model
model_path = "model/Xception_deepfake_model.keras"
model = load_model(model_path)
print(f"Loaded model from: {model_path}")

# Image path to test
image_path = "images/sample.jpg"

# Step 1: Predict deepfake or real
confidence, label = predict_image(model, image_path)
print("\n[Model Prediction]")
print(f"Image: {image_path}")
print(f"Label: {label}")
print(f"Confidence: {confidence:.4f}")

# Step 2: Generate SHA-256 hash of the image
img_hash = get_image_hash(image_path)
print("\n[Image Hash]")
print(f"SHA-256: {img_hash}")

# Step 3: Store hash on blockchain
print("\n[Blockchain Interaction]")
store_image_hash(img_hash)

# Step 4: Verify hash from blockchain
verified = verify_image_hash(img_hash)
print(f"Verification Status: {'✅ Found' if verified else '❌ Not Found'}")
