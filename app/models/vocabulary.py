from app import db
from sqlalchemy.sql import func


class Vocabulary(db.Model):
    __tablename__ = 'vocabularies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))  # Đường dẫn file .png/.jpg
    is_unlocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<Vocab {self.word} - Unlocked: {self.is_unlocked}>"