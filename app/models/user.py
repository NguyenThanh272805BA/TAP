from app import db
from sqlalchemy.sql import func
from datetime import date


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    current_level = db.Column(db.String(20), default='Beginner')
    streak_count = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')
    coins = db.Column(db.Integer, default=0)
    last_checkin = db.Column(db.Date, nullable=True)
    arena_stage = db.Column(db.Integer, default=1)  # Ải hiện tại trong Gacha Arena (1-10)
    infinity_score = db.Column(db.Integer, default=0)  # Điểm cao nhất chế độ vô cực
    last_quest_date = db.Column(db.Date, nullable=True)  # Ngày giao quest gần nhất

    created_at = db.Column(db.DateTime, default=func.now())
    tests = db.relationship('TestLog', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} - Level: {self.current_level}>"