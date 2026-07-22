from app import create_app, db
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from werkzeug.security import generate_password_hash

app = create_app()


def seed_database():
    with app.app_context():
        print("=== BẮT ĐẦU NẠP DỮ LIỆU MẪU VÀ TẠO ADMIN ===")

        # 1. Tạo tài khoản Admin
        admin_username = "admin"
        admin_password = "123456"

        existing_admin = User.query.filter_by(username=admin_username).first()
        if not existing_admin:
            hashed_pw = generate_password_hash(admin_password)
            admin_user = User(
                username=admin_username,
                password_hash=hashed_pw,
                role='admin',
                current_level='God Mode',
                coins=9999
            )
            db.session.add(admin_user)
            print(f"[+] Đã tạo tài khoản Admin -> User: {admin_username} | Pass: {admin_password}")
        else:
            # Cập nhật quyền Admin nếu tài khoản đã tồn tại
            existing_admin.role = 'admin'
            print("[*] Tài khoản Admin đã tồn tại. Đã đảm bảo phân quyền 'admin'.")

        # 2. Tạo một vài User mẫu (Player)
        dummy_users = ["player_one", "noob_master", "cyber_ninja"]
        for u in dummy_users:
            if not User.query.filter_by(username=u).first():
                db.session.add(User(
                    username=u,
                    password_hash=generate_password_hash("123456"),
                    role='user',
                    current_level='Beginner',
                    coins=50
                ))
        print(f"[+] Đã tạo {len(dummy_users)} tài khoản Player mẫu.")

        # 3. Tạo dữ liệu Từ vựng mẫu (Nếu DB trống)
        if Vocabulary.query.count() == 0:
            vocabs = [
                Vocabulary(word="Annihilate", meaning="Tiêu diệt hoàn toàn", theme="GAMING", is_unlocked=True),
                Vocabulary(word="Loot", meaning="Nhặt đồ, cướp bóc", theme="GAMING", is_unlocked=True),
                Vocabulary(word="Grind", meaning="Cày cuốc liên tục", theme="GAMING", is_unlocked=False),
                Vocabulary(word="Noob", meaning="Kẻ mới chơi, thiếu kinh nghiệm", theme="SLANG", is_unlocked=False),
                Vocabulary(word="Clutch", meaning="Tỏa sáng vào phút chót", theme="GAMING", is_unlocked=False)
            ]
            db.session.bulk_save_objects(vocabs)
            print("[+] Đã nạp 5 từ vựng mẫu.")

        # 4. Tạo dữ liệu Ngữ pháp mẫu (Nếu DB trống)
        if Grammar.query.count() == 0:
            grammars = [
                Grammar(structure="S + wish + S + V(past)", explanation="Câu điều ước không có thật ở hiện tại",
                        example="I wish I had a better weapon.", is_slang=False),
                Grammar(structure="It's high time + S + V(past)", explanation="Đã đến lúc ai đó phải làm gì",
                        example="It's high time you upgraded your armor.", is_slang=False)
            ]
            db.session.bulk_save_objects(grammars)
            print("[+] Đã nạp 2 cấu trúc ngữ pháp mẫu.")

        # Lưu toàn bộ thay đổi vào DB
        db.session.commit()
        print("=== NẠP DỮ LIỆU HOÀN TẤT! ===")


if __name__ == '__main__':
    seed_database()