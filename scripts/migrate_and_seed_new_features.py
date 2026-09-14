import os
import sys

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.roadmap import RoadmapMilestone, UserMilestoneProgress
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.controllers.roadmap_controller import ensure_default_milestones
from app.controllers.game_controller import ensure_default_cosmetics
from sqlalchemy import text

app = create_app()

def migrate_and_seed():
    with app.app_context():
        print("=== BẮT ĐẦU CẬP NHẬT DATABASE & SEED DỮ LIỆU TÍNH NĂNG MỚI ===")
        
        # 1. Tự động tạo các bảng mới chưa tồn tại
        db.create_all()
        print("[+] db.create_all() hoàn tất.")

        # 2. Thêm các cột mới vào bảng users nếu chưa có
        engine = db.engine
        with engine.connect() as conn:
            # Kiểm tra các cột trong users
            columns_to_add = [
                ("target_band", "VARCHAR(20) DEFAULT 'B2'"),
                ("current_band", "VARCHAR(20) DEFAULT 'A1'"),
                ("equipped_frame", "VARCHAR(50) DEFAULT 'frame-default'"),
                ("equipped_title", "VARCHAR(100) DEFAULT 'Tân Binh Ngơ Ngác'")
            ]

            for col_name, col_def in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    print(f"[+] Đã thêm cột '{col_name}' vào bảng users.")
                except Exception as e:
                    # Cột có thể đã tồn tại, an toàn bỏ qua
                    print(f"[*] Cột '{col_name}' đã tồn tại hoặc: {e}")

        # 3. Nạp dữ liệu giáo trình Milestone mặc định
        ensure_default_milestones()
        print(f"[+] Tổng số Chặng Milestone hiện tại: {RoadmapMilestone.query.count()}")

        # 4. Nạp dữ liệu vật phẩm trang trí mặc định
        ensure_default_cosmetics()
        print(f"[+] Tổng số Vật phẩm Trang trí hiện tại: {CosmeticItem.query.count()}")

        # 5. Cấp mặc định khung chuẩn cho tất cả User hiện có nếu chưa có
        default_frame = CosmeticItem.query.filter_by(css_class='frame-default').first()
        users = User.query.all()
        for u in users:
            if not u.equipped_frame:
                u.equipped_frame = 'frame-default'
            if not u.target_band:
                u.target_band = 'B2'
            if not u.current_band:
                u.current_band = 'A1'
            if default_frame and not UserCosmetic.query.filter_by(user_id=u.id, cosmetic_id=default_frame.id).first():
                db.session.add(UserCosmetic(user_id=u.id, cosmetic_id=default_frame.id, is_equipped=True))

        db.session.commit()
        print("=== HOÀN TẤT CẬP NHẬT DATABASE THÀNH CÔNG! ===")

if __name__ == '__main__':
    migrate_and_seed()
