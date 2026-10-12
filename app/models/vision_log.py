from app import db
from sqlalchemy.sql import func

class VisionDetectionLog(db.Model):
    __tablename__ = 'vision_detection_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    detected_object = db.Column(db.String(100), nullable=False)
    detected_parts = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<VisionDetectionLog id={self.id} object={self.detected_object}>"
