from app import db
from sqlalchemy.sql import func

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id', ondelete='CASCADE'), primary_key=True)
    unlocked_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship('User', backref=db.backref('achievements', lazy=True, cascade="all, delete-orphan"))
    achievement = db.relationship('Achievement')