# seed_data.py
from app import create_app, db
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar

app = create_app()

def seed_everything():
    with app.app_context():
        # 1. Clear dữ liệu cũ nếu cần để tránh trùng lặp
        db.session.query(Vocabulary).delete()
        db.session.query(Grammar).delete()

        # 2. Thêm từ vựng mẫu (Dùng tên ảnh Low-Poly giả định)
        vocabs = [
            Vocabulary(word="Annihilate", meaning="Tiêu diệt hoàn toàn (Game RPG hay xài)", image_url="annihilate.png", is_unlocked=True),
            Vocabulary(word="Cooldown", meaning="Thời gian hồi chiêu", image_url="cooldown.png", is_unlocked=True),
            Vocabulary(word="Immortal", meaning="Bất tử", image_url="immortal.png", is_unlocked=False),
            Vocabulary(word="Synergy", meaning="Sự phối hợp, kết hợp ăn ý", image_url="synergy.png", is_unlocked=False)
        ]

        # 3. Thêm cấu trúc ngữ pháp mẫu
        grammars = [
            Grammar(structure="S + wish + S + V(past)", explanation="Câu điều ước trái ngược với hiện tại.", example="I wish I had a high-tier gaming PC."),
            Grammar(structure="If + S + V(past), S + would + V-inf", explanation="Câu điều kiện loại 2 - Giả định không có thật ở hiện tại.", example="If I were an NPC, I would give you a legendary quest.")
        ]

        db.session.add_all(vocabs)
        db.session.add_all(grammars)
        db.session.commit()
        print(" Bơm dữ liệu mẫu cho Global Fluent thành công rồi nhé Thành!")

if __name__ == "__main__":
    seed_everything()