from app import db
from sqlalchemy.sql import func
from datetime import datetime


class FarmCrop(db.Model):
    """Bảng lưu trữ thông số 20 loại cây trồng trong Nông Trại Tri Thức"""
    __tablename__ = 'farm_crops'

    code = db.Column(db.String(50), primary_key=True) # e.g. crop_radish, crop_carrot
    name = db.Column(db.String(100), nullable=False) # Tên cây tiếng Việt
    name_en = db.Column(db.String(100), nullable=False) # Tên cây tiếng Anh
    rarity = db.Column(db.String(20), nullable=False, default='COMMON') # COMMON, UNCOMMON, RARE, EPIC, LEGENDARY
    cefr_level = db.Column(db.String(10), nullable=False, default='A1') # A1, A2, B1, B2, C1, C2
    seed_price = db.Column(db.Integer, default=10) # Giá mua hạt giống (Xu)
    harvest_coins = db.Column(db.Integer, default=25) # Xu thưởng khi thu hoạch
    harvest_rp = db.Column(db.Integer, default=10) # Điểm RP/Kinh nghiệm học thuật thưởng
    growth_seconds = db.Column(db.Integer, default=60) # Thời gian sinh trưởng mặc định (giây)
    vocab_count = db.Column(db.Integer, default=1) # Số lượng từ vựng thu hoạch được
    description = db.Column(db.Text, nullable=True) # Mô tả cây trồng & chủ đề kiến thức

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "name_en": self.name_en,
            "rarity": self.rarity,
            "cefr_level": self.cefr_level,
            "seed_price": self.seed_price,
            "harvest_coins": self.harvest_coins,
            "harvest_rp": self.harvest_rp,
            "growth_seconds": self.growth_seconds,
            "vocab_count": self.vocab_count,
            "description": self.description
        }


class FarmPlot(db.Model):
    """Bảng quản lý các ô đất nông trại của người dùng"""
    __tablename__ = 'farm_plots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plot_index = db.Column(db.Integer, nullable=False, default=0) # 0 đến 5 (hoặc 8)
    is_unlocked = db.Column(db.Boolean, default=True) # Ô 0, 1, 2 mở sẵn, ô 3+ mở bằng Xu
    unlock_cost = db.Column(db.Integer, default=0) # Chi phí mở ô đất

    # Trạng thái trồng trọt
    crop_code = db.Column(db.String(50), db.ForeignKey('farm_crops.code', ondelete='SET NULL'), nullable=True)
    planted_at = db.Column(db.DateTime, nullable=True)
    harvest_ready_at = db.Column(db.DateTime, nullable=True)
    watered_count = db.Column(db.Integer, default=0) # Mỗi lần tưới giảm thời gian
    is_golden = db.Column(db.Boolean, default=False) # Bón phân hoàng kim (nhân đôi thưởng)

    crop = db.relationship('FarmCrop', lazy=True)
    user = db.relationship('User', backref=db.backref('farm_plots', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        now = datetime.now()
        is_growing = bool(self.crop_code and self.planted_at)
        is_ready = False
        remaining_seconds = 0
        progress_percent = 0

        if is_growing and self.harvest_ready_at:
            if now >= self.harvest_ready_at:
                is_ready = True
                progress_percent = 100
            else:
                total_duration = (self.harvest_ready_at - self.planted_at).total_seconds()
                elapsed = (now - self.planted_at).total_seconds()
                remaining_seconds = max(0, int((self.harvest_ready_at - now).total_seconds()))
                progress_percent = min(99, max(0, int((elapsed / total_duration) * 100))) if total_duration > 0 else 100

        stage = 'empty'
        if is_growing:
            if is_ready:
                stage = 'mature'
            elif progress_percent < 40:
                stage = 'seed'
            else:
                stage = 'sprout'

        return {
            "id": self.id,
            "plot_index": self.plot_index,
            "is_unlocked": self.is_unlocked,
            "unlock_cost": self.unlock_cost,
            "crop_code": self.crop_code,
            "crop_name": self.crop.name if self.crop else None,
            "crop_rarity": self.crop.rarity if self.crop else None,
            "cefr_level": self.crop.cefr_level if self.crop else None,
            "stage": stage,
            "is_ready": is_ready,
            "is_growing": is_growing,
            "is_golden": self.is_golden,
            "remaining_seconds": remaining_seconds,
            "progress_percent": progress_percent,
            "watered_count": self.watered_count
        }


class FarmInventory(db.Model):
    """Kho nông sản, hạt giống và vật phẩm tăng tốc của người chơi"""
    __tablename__ = 'farm_inventory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False) # 'SEED', 'FERTILIZER', 'BOOSTER'
    item_code = db.Column(db.String(50), nullable=False) # e.g. seed_crop_carrot, fert_speed_50
    quantity = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    user = db.relationship('User', backref=db.backref('farm_inventory', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            "id": self.id,
            "item_type": self.item_type,
            "item_code": self.item_code,
            "quantity": self.quantity
        }
