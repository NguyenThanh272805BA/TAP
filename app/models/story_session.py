from app import db
from sqlalchemy.sql import func


class StorySession(db.Model):
    __tablename__ = 'story_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('story_topics.id', ondelete='CASCADE'), nullable=False)

    # Bản tóm tắt 10 turn thành một câu chuyện ngắn
    summary_en = db.Column(db.Text, nullable=False)
    summary_vn = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Survived')  # Survived hoặc Dead (Dựa vào điểm ngữ pháp)

    created_at = db.Column(db.DateTime, default=func.now())

    # Relationships
    user = db.relationship('User', backref=db.backref('story_sessions', lazy=True, cascade="all, delete-orphan"))
    topic = db.relationship('StoryTopic', backref='sessions')

    def __repr__(self):
        return f"<StorySession User:{self.user_id} - Topic:{self.topic_id} - Status:{self.status}>"