from app import db
from sqlalchemy.sql import func

class StoryTopic(db.Model):
    __tablename__ = 'story_topics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False) # Action, Horror, Romance...
    cover_image = db.Column(db.String(255), default='default_cover.jpg')
    system_prompt = db.Column(db.Text, nullable=False) # Prompt nhồi vào AI để tạo bối cảnh
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<StoryTopic {self.title} - Genre: {self.genre}>"