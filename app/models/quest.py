from app import db
from sqlalchemy.sql import func


class Quest(db.Model):
    __tablename__ = 'quests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quest_code = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='NEWBIE')  # NEWBIE, VOCAB, GRAMMAR, ARENA, LEGEND
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)  # VOCAB_COUNT, STREAK_DAYS, EXAM_SCORE, ARENA_WINS, GRAMMAR_COUNT, STUDY_TIME, COINS_EARNED
    target_count = db.Column(db.Integer, default=1)
    reward_coins = db.Column(db.Integer, default=20)
    reward_exp = db.Column(db.Integer, default=50)
    badge_icon = db.Column(db.String(50), default='quest')
    order_index = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<Quest {self.quest_code}: {self.title}>"


class UserQuestProgress(db.Model):
    __tablename__ = 'user_quest_progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id', ondelete='CASCADE'), nullable=False)
    current_count = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    is_claimed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)

    quest = db.relationship('Quest', backref=db.backref('user_progress', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('quest_progress', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='uq_user_quest'),
    )

    def __repr__(self):
        return f"<UserQuestProgress User:{self.user_id} Quest:{self.quest_id} Done:{self.is_completed} Claimed:{self.is_claimed}>"
