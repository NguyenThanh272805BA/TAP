import os
import json
import time
from google import genai  # Sử dụng SDK mới
from dotenv import load_dotenv
from app import create_app, db
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar

# Load cấu hình
load_dotenv()

# Khởi tạo Client theo chuẩn SDK google-genai mới
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = create_app()


def bulk_mine_vocab(amount=5):
    """Máy xúc đào hàng loạt từ vựng/từ lóng gen Z và RPG"""
    print(f"[*] Đang yêu cầu AI đào {amount} từ vựng mới...")
    prompt = f"""
    Hãy tạo ra một danh sách gồm đúng {amount} từ vựng tiếng Anh (có thể là từ nâng cao, từ lóng mạng, hoặc thuật ngữ game RPG).
    Tuyệt đối chỉ trả về 1 mảng JSON, KHÔNG CÓ markdown.
    Cấu trúc:
    [
        {{"word": "từ_vựng", "meaning": "nghĩa tiếng Việt (phong cách trẻ trung)", "theme": "Gaming"}}
    ]
    """

    try:
        # Gọi API bằng cú pháp Client mới
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        clean_json = response.text.strip().replace('```json', '').replace('```', '')

        items = json.loads(clean_json)
        with app.app_context():
            added = 0
            for item in items:
                # Tránh thêm trùng lặp
                if not Vocabulary.query.filter_by(word=item['word']).first():
                    new_v = Vocabulary(
                        word=item['word'],
                        meaning=item['meaning'],
                        theme=item['theme'],
                        image_url="default.png",
                        is_unlocked=False
                    )
                    db.session.add(new_v)
                    added += 1
            db.session.commit()
            print(f"[+] Đã đắp thành công {added} từ vựng vào Database!")
    except Exception as e:
        print(f"[-] Lỗi tiến trình đào từ vựng: {e}")


def bulk_mine_grammar(amount=3):
    """Máy xúc đào hàng loạt cấu trúc ngữ pháp"""
    print(f"[*] Đang yêu cầu AI đào {amount} cấu trúc ngữ pháp mới...")
    prompt = f"""
    Hãy tạo ra một danh sách gồm đúng {amount} cấu trúc câu/ngữ pháp tiếng Anh từ cơ bản đến nâng cao.
    Tuyệt đối chỉ trả về 1 mảng JSON, KHÔNG CÓ markdown.
    Cấu trúc:
    [
        {{"structure": "cấu_trúc", "explanation": "giải_thích", "example": "câu_ví_dụ"}}
    ]
    """

    try:
        # Gọi API bằng cú pháp Client mới
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        clean_json = response.text.strip().replace('```json', '').replace('```', '')

        items = json.loads(clean_json)
        with app.app_context():
            added = 0
            for item in items:
                if not Grammar.query.filter_by(structure=item['structure']).first():
                    new_g = Grammar(
                        structure=item['structure'],
                        explanation=item['explanation'],
                        example=item['example'],
                        is_slang=False
                    )
                    db.session.add(new_g)
                    added += 1
            db.session.commit()
            print(f"[+] Đã đắp thành công {added} ngữ pháp vào Database!")
    except Exception as e:
        print(f"[-] Lỗi tiến trình đào ngữ pháp: {e}")


if __name__ == "__main__":
    print("=== KÍCH HOẠT HỆ THỐNG MÁY ĐÀO DỮ LIỆU BẰNG AI ===")

    bulk_mine_vocab(10)

    # Cho máy nghỉ 40 giây để xả cooldown API (Tránh lỗi 429 Resource Exhausted)
    print("\n[!] Đang tản nhiệt hệ thống (đợi 40 giây để tránh sập API free)...")
    time.sleep(40)

    bulk_mine_grammar(5)
    print("\n=== HOÀN TẤT CHIẾN DỊCH ĐÀO DỮ LIỆU ===")