from extensions import db
from datetime import datetime

class ImageRecord(db.Model):
    __tablename__ = 'image_record'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    image_hash = db.Column(db.String(64), unique=True, nullable=False)
    label = db.Column(db.String(10), nullable=False)  # "real" or "fake"
    confidence = db.Column(db.Float, nullable=False)  # confidence score between 0.0 and 1.0
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ImageRecord id={self.id}, hash={self.image_hash}, label={self.label}, confidence={self.confidence:.2f}>"
