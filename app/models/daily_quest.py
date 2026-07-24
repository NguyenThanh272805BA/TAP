from app import db
from datetime import date


class DailyQuest(db.Model):
    __tablename__ = 'daily_quests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    vocab_id = db.Column(db.Integer, db.ForeignKey('vocabularies.id', ondelete='CASCADE'), nullable=False)

    quest_type = db.Column(db.String(20), default='NEW')  # 'NEW' (Từ mới) hoặc 'REVIEW' (Từ đã thuộc)
    is_completed = db.Column(db.Boolean, default=False)
    assigned_date = db.Column(db.Date, default=date.today, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('daily_quests', lazy=True, cascade="all, delete-orphan"))
    vocab = db.relationship('Vocabulary')

    def __repr__(self):
        return f"<DailyQuest User:{self.user_id} - Vocab:{self.vocab_id} - Done:{self.is_completed}>"