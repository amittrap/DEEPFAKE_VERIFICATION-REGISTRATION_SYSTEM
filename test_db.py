from extensions import db
from models.user import User
from models.image_record import ImageRecord
from app import create_app  # or wherever your Flask app is created

app = create_app()
app.app_context().push()

print("Users in DB:")
for user in User.query.all():
    print(user.id, user.email, user.age, user.gender, user.occupation)

print("\nImage Records in DB:")
for image in ImageRecord.query.all():
    print(image.id, image.user_id, image.image_filename, image.image_hash, image.timestamp)
