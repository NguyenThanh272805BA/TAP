from app import db

class UserVocabulary(db.Model):
    __tablename__ = 'user_vocabularies'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    vocab_id = db.Column(db.Integer, db.ForeignKey('vocabularies.id', ondelete='CASCADE'), primary_key=True)
    is_unlocked = db.Column(db.Boolean, default=False)

    # Trạng thái tĩnh 
    memorization_level = db.Column(db.String(20), default='CHUA_THUOC')
    last_tested_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Các trường Features mới phục vụ Machine Learning chuẩn SM-2
    fail_count = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float, default=0.0) # Thời gian phản xạ trung bình (giây)
    previous_interval = db.Column(db.Float, default=0.0) # [ THÊM MỚI ] Khoảng thời gian ôn tập trước đó (giờ)
    next_review_time = db.Column(db.DateTime, default=db.func.current_timestamp())