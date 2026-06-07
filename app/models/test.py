from app import db
from sqlalchemy.sql import func


class TestLog(db.Model):
    __tablename__ = 'test_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Float)
    ai_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<TestLog UserID:{self.user_id} - Score: {self.score}>"