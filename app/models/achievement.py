from app import db

class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon_url = db.Column(db.String(255), default='default_badge.png')
    condition_type = db.Column(db.String(50), nullable=False) # STREAK, GACHA_COMBO, LEVEL
    condition_value = db.Column(db.Integer, nullable=False)
    reward_coins = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Achievement {self.title} - {self.condition_type}:{self.condition_value}>"