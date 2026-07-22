import os
import json
import random
from google import genai
from flask import Blueprint, request, jsonify, session
from app.utils.gemini_helper import evaluate_english_skill
from app.models.test import TestLog
from app.models.user import User
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary  # <-- Bổ sung import Model
from app import db

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    user_input = data.get('text')
    mode = data.get('mode', 'grammar')

    if not user_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào hoặc phiên đăng nhập hết hạn!"}), 400

    try:
        # ==============================================================
        # NHÁNH 1: XỬ LÝ TEXT-RPG STORY (GỌI TRỰC TIẾP API GEMINI)
        # ==============================================================
        if mode == 'story':
            user = User.query.get(user_id)
            user_level = user.current_level if user else "Beginner"
            story_turn = data.get('turn', 1)
            story_history = data.get('history', '')
            is_final_turn = True if story_turn >= 10 else False

            prompt_story = f"""
            Ngữ cảnh: Bạn là Game Master xéo xắt, mỏ hỗn của game Text-RPG Sinh tồn hậu tận thế. 
            Trình độ người chơi: {user_level}. Đang ở LƯỢT {story_turn}/10.

            TÓM TẮT CỐT TRUYỆN TỪ TRƯỚC ĐẾN NAY: 
            {story_history}

            HÀNH ĐỘNG MỚI NHẤT CỦA NGƯỜI CHƠI: "{user_input}"

            YÊU CẦU BẮT BUỘC (Trọng tâm cốt truyện):
            1. Chấm điểm ngữ pháp (0-10) và đưa ra 'feedback' (Chửi thẳng mặt nếu sai ngữ pháp cơ bản, khen ngạo nghễ nếu đúng).
            2. Dựa vào hành động, sáng tạo tiếp cốt truyện kịch tính (scene_en, scene_vn). Nếu điểm < 5, cho nhân vật chịu hậu quả thê thảm.
            3. Tạo một gợi ý điền từ (hint_en, hint_vn) ẩn 1-2 từ khóa bằng dấu ___ cho lượt tới.
            4. LƯỢT 10: Tạo kết cục game, set is_end = true.

            TUYỆT ĐỐI CHỈ TRẢ VỀ ĐÚNG 1 JSON OBJECT:
            {{
                "score": <điểm_số>,
                "feedback": "<nhận_xét_ngữ_pháp>",
                "scene_en": "<Cốt_truyện_tiếp_diễn_tiếng_Anh>",
                "scene_vn": "<Dịch_Việt>",
                "hint_en": "<Gợi_ý_có_chỗ_trống>",
                "hint_vn": "<Dịch_gợi_ý>",
                "is_end": {"true" if is_final_turn else "false"}
            }}
            """
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_story)
            clean_json_str = response.text.strip().replace('```json', '').replace('```', '')
            result = json.loads(clean_json_str)

        # ==============================================================
        # NHÁNH 2: XỬ LÝ HỌC TẬP (GRAMMAR/VOCAB) DÙNG GEMINI HELPER
        # ==============================================================
        else:
            context_challenge = ""
            if mode == 'grammar':
                grammar_list = Grammar.query.all()
                if grammar_list:
                    chosen = random.choice(grammar_list)
                    context_challenge = f"Cấu trúc bắt buộc: {chosen.structure} ({chosen.explanation}). Ví dụ: {chosen.example}"
                else:
                    context_challenge = "Cấu trúc bắt buộc: S + wish + S + V(past) (Câu điều ước ở hiện tại)"
            elif mode == 'vocab':
                vocab_list = Vocabulary.query.filter_by(is_unlocked=True).all()
                if vocab_list:
                    chosen = random.choice(vocab_list)
                    context_challenge = f"Từ vựng bắt buộc phải dùng: '{chosen.word}' nghĩa là ({chosen.meaning})"

            ai_response_str = evaluate_english_skill(user_input, context_challenge)
            clean_json_str = ai_response_str.strip().replace('```json', '').replace('```', '')
            result = json.loads(clean_json_str)

            score = result.get("score", 0)
            if score >= 8.0:
                mine_new_data_via_ai(mode)

    except Exception as e:
        result = {
            "score": 4.0,
            "feedback": f"Hệ thống lõi gặp xung đột dữ liệu rồi! Lỗi: {str(e)}",
            "scene_en": "The system crashed. Reality is torn apart.",
            "scene_vn": "Hệ thống sụp đổ. Thực tại bị xé toạc.",
            "hint_en": "I must ___ the truth.",
            "hint_vn": "Tôi phải (tìm_ra) sự thật.",
            "is_end": False
        }

    new_log = TestLog(
        user_id=user_id,
        score=result.get("score", 0),
        ai_feedback=result.get("feedback", "")
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"message": "Master G đã xử lý xong!", "result": result}), 200


def mine_new_data_via_ai(current_mode):
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
    data = request.get_json(silent=True) or {}
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


@ai_bp.route('/generate_unit', methods=['POST'])
def generate_unit():
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip().upper()
    user_id = session.get('user_id')

    if not topic:
        return jsonify({"error": "Vui lòng nhập chủ đề muốn học!"}), 400
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    # [ VÁ LỖI ]: Kiểm tra xem Unit này đã từng được đúc trên hệ thống chưa
    existing_vocabs = Vocabulary.query.filter_by(theme=topic).all()
    if len(existing_vocabs) >= 10:
        added_to_user = 0
        for v in existing_vocabs:
            uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first()
            if not uv:
                new_uv = UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True)
                db.session.add(new_uv)
                added_to_user += 1
        db.session.commit()
        return jsonify({
            "message": f"[CACHE HIT] Đã nạp thành công {added_to_user} từ vựng Unit '{topic}' từ DB tổng vào thư viện cá nhân!",
            "added": added_to_user
        }), 200

    # Khởi tạo qua Gemini
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
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        items = json.loads(clean_json)

        added_count = 0
        for item in items:
            # 1. Thêm vào kho tổng
            v = Vocabulary.query.filter_by(word=item['word']).first()
            if not v:
                v = Vocabulary(
                    word=item['word'],
                    meaning=item['meaning'],
                    theme=topic,
                    image_url="default.png",
                    is_unlocked=True
                )
                db.session.add(v)
                db.session.flush()  # Để lấy ID ngay lập tức

            # 2. Gán quyền sở hữu vào thư viện User
            uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first()
            if not uv:
                new_uv = UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True)
                db.session.add(new_uv)
                added_count += 1

        db.session.commit()
        return jsonify({
            "message": f"[AI MINTED] Đã đúc & thêm {added_count} từ vựng Unit '{topic}' vào thư viện của bạn!",
            "added": added_count
        }), 200

    except Exception as e:
        return jsonify({"error": f"Lò đúc AI gặp sự cố kỹ thuật hoặc hết hạn ngạch: {str(e)}"}), 500


@ai_bp.route('/story/init', methods=['POST'])
def init_story():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    user_level = user.current_level if user else "Beginner"

    prompt = f"""
    Bạn là Game Master của một game Text-RPG Sinh tồn hậu tận thế.
    Trình độ người chơi: {user_level}. Đây là LƯỢT 1/10.

    Nhiệm vụ: Tạo bối cảnh mở màn ngầu, gai góc, ngắn gọn (2 câu).
    Và tạo ra một GỢI Ý HÀNH ĐỘNG tiếp theo dạng ĐIỀN VÀO CHỖ TRỐNG (ẩn đi 1-2 từ khóa quan trọng bằng dấu ___ để người chơi tự ghép thành câu hoàn chỉnh).

    CHỈ TRẢ VỀ ĐÚNG 1 OBJECT JSON, không dùng markdown (```json). Cấu trúc:
    {{
        "scene_en": "Cảnh báo hệ thống... Bạn tỉnh dậy giữa đống đổ nát.",
        "scene_vn": "Dịch tiếng Việt câu trên. Ngắn gọn, tăm tối.",
        "hint_en": "I need to ___ my ___.",
        "hint_vn": "Tôi cần (tìm) (vũ khí) của mình.",
        "is_end": false
    }}
    """

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        return jsonify(json.loads(clean_json)), 200
    except Exception as e:
        return jsonify({
            "scene_en": "System error. The world is collapsing.",
            "scene_vn": "Lỗi hệ thống. Thế giới đang sụp đổ.",
            "hint_en": "I ___ to ___ the system.",
            "hint_vn": "Tôi (cần) (khởi động lại) hệ thống.",
            "is_end": False
        }), 200