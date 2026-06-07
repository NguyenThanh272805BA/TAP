from app import db
from sqlalchemy.sql import func


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    current_level = db.Column(db.String(20), default='Beginner')
    streak_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())

    # Thiết lập mối quan hệ 1-Nhiều với bảng test_logs
    tests = db.relationship('TestLog', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} - Level: {self.current_level}>"