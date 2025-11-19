from PIL import Image
import hashlib

def get_image_pixel_hash_from_stream(file_stream):
    """Generate a SHA-256 hash of image pixel data from an in-memory stream."""
    file_stream.seek(0)  # reset stream pointer before reading
    with Image.open(file_stream) as img:
        img = img.convert('RGB')
        pixels = img.tobytes()
        return hashlib.sha256(pixels).hexdigest()

def get_image_hash(image_path):
    """Generate a SHA-256 hash of image pixel data from an image file path."""
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        pixels = img.tobytes()
        return hashlib.sha256(pixels).hexdigest()
