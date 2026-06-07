from app import db
from sqlalchemy.sql import func


class Grammar(db.Model):
    __tablename__ = 'grammars'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    structure = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    is_slang = db.Column(db.Boolean, default=False)
    example = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<Grammar {self.structure} - Slang: {self.is_slang}>"