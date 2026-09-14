from app import db
from sqlalchemy.sql import func
from datetime import date


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    current_level = db.Column(db.String(100), default='Tân Binh Ngơ Ngác')
    target_band = db.Column(db.String(20), default='B2')  # CEFR: A1, A2, B1, B2, C1, C2 hoặc IELTS tương đương
    current_band = db.Column(db.String(20), default='A1') # Trình độ xuất phát / hiện tại
    equipped_frame = db.Column(db.String(50), default='frame-default') # Tên class CSS khung avatar
    equipped_title = db.Column(db.String(100), default='Tân Binh Ngơ Ngác') # Danh hiệu đang đeo
    streak_count = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')
    coins = db.Column(db.Integer, default=0)
    last_checkin = db.Column(db.Date, nullable=True)
    arena_stage = db.Column(db.Integer, default=1)  # Ải hiện tại trong Gacha Arena (1-10)
    infinity_score = db.Column(db.Integer, default=0)  # Điểm cao nhất chế độ vô cực
    last_quest_date = db.Column(db.Date, nullable=True)  # Ngày giao quest gần nhất
    avatar = db.Column(db.String(255), default='default_avatar.png')
    bio = db.Column(db.Text, default='Kẻ lang thang trong thế giới ngôn ngữ...')

    created_at = db.Column(db.DateTime, default=func.now())
    tests = db.relationship('TestLog', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} - Level: {self.current_level}>"