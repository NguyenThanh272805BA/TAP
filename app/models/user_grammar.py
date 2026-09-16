from app import db
from sqlalchemy.sql import func


class UserGrammar(db.Model):
    __tablename__ = 'user_grammars'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    grammar_id = db.Column(db.Integer, db.ForeignKey('grammars.id', ondelete='CASCADE'), nullable=False)
    mastery_status = db.Column(db.String(20), default='CHUA_HOC')  # CHUA_HOC, DANG_LUYEN, DA_NAM_VUNG
    practice_count = db.Column(db.Integer, default=0)
    best_score = db.Column(db.Float, default=0.0)
    last_practiced_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    user = db.relationship('User', backref=db.backref('user_grammars', lazy=True, cascade='all, delete-orphan'))
    grammar = db.relationship('Grammar', backref=db.backref('user_records', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'grammar_id', name='uq_user_grammar'),
    )

    def __repr__(self):
        return f"<UserGrammar User:{self.user_id} Grammar:{self.grammar_id} Status:{self.mastery_status}>"
