import os
import json
import random
from google import genai
from flask import Blueprint, request, jsonify
from app.utils.gemini_helper import evaluate_english_skill
from app.models.test import TestLog
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app import db

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_input = data.get('text')
    mode = data.get('mode', 'grammar')

    if not user_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào!"}), 400

    context_challenge = ""
    try:
        if mode == 'grammar':
            grammar_list = Grammar.query.all()
            if grammar_list:
                chosen = random.choice(grammar_list)
                context_challenge = f"Cấu trúc bắt buộc: {chosen.structure} ({chosen.explanation}). Ví dụ mẫu: {chosen.example}"
            else:
                context_challenge = "Cấu trúc bắt buộc: S + wish + S + V(past) (Câu điều ước ở hiện tại)"

        elif mode == 'vocab':
            vocab_list = Vocabulary.query.filter_by(is_unlocked=True).all()
            if vocab_list:
                chosen = random.choice(vocab_list)
                context_challenge = f"Từ vựng/Từ lóng bắt buộc phải dùng: '{chosen.word}' nghĩa là ({chosen.meaning})"
            else:
                context_challenge = "Từ vựng bắt buộc phải dùng: 'Annihilate' (Tiêu diệt hoàn toàn)"

        elif mode == 'story':
            context_challenge = "Ngữ cảnh nhập vai RPG: Người dùng đang đối thoại với một NPC hấp hối..."

        # Gọi AI chấm điểm
        ai_response_str = evaluate_english_skill(user_input, context_challenge)
        result = json.loads(ai_response_str)

        # --- TỰ ĐỘNG ĐÀO DATA TỪ BÊN NGOÀI BẰNG AI (AUTOMATIC DATA MINING) ---
        score = result.get("score", 0)
        if score >= 8.0:
            mine_new_data_via_ai(mode)

    except Exception as e:
        result = {
            "score": 4.0,
            "feedback": f"Hệ thống lõi gặp xung đột dữ liệu rồi! Lỗi: {str(e)}"
        }

    # Lưu vết kết quả vào Database
    new_log = TestLog(
        user_id=user_id,
        score=result.get("score", 0),
        ai_feedback=result.get("feedback", "")
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        "message": "Master G đã chấm điểm xong!",
        "result": result
    }), 200


def mine_new_data_via_ai(current_mode):
    """
    Hàm nội bộ tự động đào sâu kiến thức tiếng Anh trên Internet/AI tri thức
    để nạp thêm tài nguyên mới cho game.
    """
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        if current_mode == 'vocab':
            prompt = """
            Bạn là máy đào dữ liệu. Hãy tìm và xuất bản đúng 1 từ vựng tiếng Anh độc đáo thuộc chủ đề Gaming RPG hoặc Internet Slang hoặc đời thực.
            Trả về CHUẨN định dạng JSON sau (không chứa markdown thương hiệu ```json):
            {
                "word": "tên từ tiếng Anh",
                "meaning": "ý nghĩa ngắn gọn tiếng Việt kèm ngữ cảnh",
                "theme": "Gaming, Đời thực"
            }
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            clean_json = response.text.strip().replace('```json', '').replace('```', '')
            item_data = json.loads(clean_json)

            exists = Vocabulary.query.filter_by(word=item_data['word']).first()
            if not exists:
                new_vocab = Vocabulary(
                    word=item_data['word'],
                    meaning=item_data['meaning'],
                    theme=item_data['theme'],
                    image_url="default_lowpoly.png",
                    is_unlocked=False
                )
                db.session.add(new_vocab)
                db.session.commit()
                print(f"-> [AI Data Miner]: Đã đào thành công từ vựng mới: {item_data['word']}")

        elif current_mode == 'grammar':
            prompt = """
            Hãy cung cấp 1 cấu trúc ngữ pháp tiếng Anh từ cơ bản tới cốt lõi hoặc nâng cao.
            Trả về CHUẨN định dạng JSON sau (không chứa markdown):
            {
                "structure": "Công thức cấu trúc",
                "explanation": "Giải thích ngắn gọn bằng tiếng Việt",
                "example": "Câu ví dụ minh họa bằng tiếng Anh"
            }
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            clean_json = response.text.strip().replace('```json', '').replace('```', '')
            item_data = json.loads(clean_json)

            exists = Grammar.query.filter_by(structure=item_data['structure']).first()
            if not exists:
                new_grammar = Grammar(
                    structure=item_data['structure'],
                    explanation=item_data['explanation'],
                    example=item_data['example'],
                    is_slang=False
                )
                db.session.add(new_grammar)
                db.session.commit()
                print(f"-> [AI Data Miner]: Đã đào thành công cấu trúc ngữ pháp mới: {item_data['structure']}")

    except Exception as e:
        print(f" lỗi tiến trình AI đào dữ liệu: {e}")


@ai_bp.route('/guide', methods=['POST'])
def get_guide():
    data = request.get_json()
    word = data.get('word')

    if not word:
        return jsonify({"error": "Thiếu từ vựng"}), 400

    prompt = f"""
    Bạn là Master G. Học trò đang không biết cách dùng từ '{word}', hãy hướng dẫn nhanh.
    Trả về một đoạn văn bản ngắn gọn (khoảng 3-4 câu, KHÔNG dùng markdown định dạng phức tạp) gồm:
    1. Một câu ví dụ minh họa mang phong cách cực chất (lời nói thẳng thắn có phần cục súc).
    2. Dịch nghĩa câu đó ra tiếng Việt.
    3. Phân tích siêu nhanh cấu trúc ngữ pháp vừa dùng trong câu.
    Giọng điệu: Hơi xéo xắt, mỏ hỗn nhưng thực tâm rất muốn học trò hiểu bài.
    """

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        formatted_guide = response.text.replace('\n', '<br>')
        return jsonify({"guide": formatted_guide}), 200
    except Exception as e:
        return jsonify({
            "guide": f"[OFFLINE MODE] Lõi AI đang bận tản nhiệt! Gợi ý tạm: Hãy thử đặt câu dạng 'S + V + {word}' xem sao đồ ngốc!"
        }), 200


# =================================================================
# ĐÃ FIX LỖI: ĐƯA HÀM RA NGOÀI VÀ CĂN SÁT LỀ TRÁI
# =================================================================
@ai_bp.route('/generate_unit', methods=['POST'])
def generate_unit():
    data = request.get_json()
    topic = data.get('topic')

    if not topic:
        return jsonify({"error": "Vui lòng nhập chủ đề muốn học!"}), 400

    prompt = f"""
    Bạn là hệ thống thiết kế bài giảng. Người dùng muốn học tiếng Anh về chủ đề: '{topic}'.
    Hãy tạo ra 50 từ vựng tiếng Anh (hoặc cụm từ) liên quan mật thiết đến chủ đề này.
    Tuyệt đối chỉ trả về 1 mảng JSON hợp lệ, KHÔNG chứa ký hiệu markdown.
    Cấu trúc:
    [
        {{"word": "từ_vựng_1", "meaning": "nghĩa tiếng Việt", "theme": "{topic}"}}
    ]
    """

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        items = json.loads(clean_json)
        is_offline = False

    except Exception as e:
        print(f"[-] AI Tạm ngưng do Quota/Lỗi: {e}")
        items = [
            {"word": f"Basic {topic}", "meaning": f"Kiến thức cơ bản về {topic}", "theme": topic},
            {"word": f"Advanced {topic}", "meaning": f"Kỹ năng nâng cao trong {topic}", "theme": topic},
            {"word": f"{topic} Master", "meaning": f"Bậc thầy trong lĩnh vực {topic}", "theme": topic}
        ]
        is_offline = True

    try:
        added_count = 0
        for item in items:
            if not Vocabulary.query.filter_by(word=item['word']).first():
                new_v = Vocabulary(
                    word=item['word'],
                    meaning=item['meaning'],
                    theme=item['theme'].upper(),
                    image_url="default.png",
                    is_unlocked=True
                )
                db.session.add(new_v)
                added_count += 1

        db.session.commit()

        msg = f"Đã đúc thành công Unit '{topic}' với {added_count} từ vựng mới!"
        if is_offline:
            msg = f"[OFFLINE MODE] Server bận, hệ thống tự cấp phát Unit dự phòng cho '{topic}'!"

        return jsonify({
            "message": msg,
            "added": added_count
        }), 200

    except Exception as db_err:
        return jsonify({"error": f"Lỗi lưu trữ Database: {str(db_err)}"}), 500