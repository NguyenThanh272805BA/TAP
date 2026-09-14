from app import db
from sqlalchemy.sql import func


class CosmeticItem(db.Model):
    __tablename__ = 'cosmetic_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(30), nullable=False, default='AVATAR_FRAME') # AVATAR_FRAME, PLAYER_TITLE, BADGE
    css_class = db.Column(db.String(50), nullable=False, default='frame-default')
    description = db.Column(db.String(255), nullable=True)
    price_coins = db.Column(db.Integer, default=0) # 0 = Độc quyền qua thành tựu/chặng, > 0 = Bán trong Shop
    required_achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id', ondelete='SET NULL'), nullable=True)
    required_band = db.Column(db.String(20), nullable=True) # Yêu cầu đạt Band tối thiểu để mở khóa
    icon_preview = db.Column(db.String(255), default='default_item.png')
    created_at = db.Column(db.DateTime, default=func.now())

    achievement = db.relationship('Achievement', backref=db.backref('cosmetic_rewards', lazy=True))

    def __repr__(self):
        return f"<CosmeticItem {self.name} [{self.type}]: {self.css_class}>"


class UserCosmetic(db.Model):
    __tablename__ = 'user_cosmetics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    cosmetic_id = db.Column(db.Integer, db.ForeignKey('cosmetic_items.id', ondelete='CASCADE'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    acquired_at = db.Column(db.DateTime, default=func.now())

    cosmetic = db.relationship('CosmeticItem', backref=db.backref('owners', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('owned_cosmetics', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<UserCosmetic User:{self.user_id} Item:{self.cosmetic_id} Equipped:{self.is_equipped}>"
