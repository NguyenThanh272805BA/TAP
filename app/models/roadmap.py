from app import db
from sqlalchemy.sql import func
import json


class RoadmapMilestone(db.Model):
    __tablename__ = 'roadmap_milestones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    band_level = db.Column(db.String(10), nullable=False, default='A1')  # A1, A2, B1, B2, C1, C2
    step_order = db.Column(db.Integer, nullable=False, default=1)        # 1, 2, 3... trong cùng band
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    grammar_id = db.Column(db.Integer, db.ForeignKey('grammars.id', ondelete='SET NULL'), nullable=True)
    target_vocab_ids = db.Column(db.Text, default='[]')                 # JSON Array string: "[1, 2, 3]"
    pass_score = db.Column(db.Float, default=7.0)                       # Điểm tối thiểu qua ải
    reward_coins = db.Column(db.Integer, default=50)                    # Xu thưởng khi hoàn thành
    reward_cosmetic_id = db.Column(db.Integer, nullable=True)           # Quà tặng kèm (Khung avatar / danh hiệu)
    created_at = db.Column(db.DateTime, default=func.now())

    grammar = db.relationship('Grammar', backref=db.backref('milestones', lazy=True))

    def get_vocab_ids(self):
        try:
            return json.loads(self.target_vocab_ids or '[]')
        except Exception:
            return []

    def __repr__(self):
        return f"<Milestone {self.band_level} Step {self.step_order}: {self.title}>"


class UserMilestoneProgress(db.Model):
    __tablename__ = 'user_milestone_progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('roadmap_milestones.id', ondelete='CASCADE'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    best_score = db.Column(db.Float, default=0.0)
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)

    milestone = db.relationship('RoadmapMilestone', backref=db.backref('user_progress', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('milestone_progress', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<UserMilestone User:{self.user_id} Milestone:{self.milestone_id} Done:{self.is_completed}>"
