from app import db


class UserVocabulary(db.Model):
    __tablename__ = 'user_vocabularies'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    vocab_id = db.Column(db.Integer, db.ForeignKey('vocabularies.id', ondelete='CASCADE'), primary_key=True)
    is_unlocked = db.Column(db.Boolean, default=False)

    # 3 Cấp độ: CHUA_THUOC, HOI_THUOC, DA_THUOC
    memorization_level = db.Column(db.String(20), default='CHUA_THUOC')
    last_tested_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())