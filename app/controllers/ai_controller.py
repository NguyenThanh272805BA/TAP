import os
import json
import random
from datetime import date
from flask import Blueprint, request, jsonify, session

# Import helper cũ
from app.utils.gemini_helper import evaluate_english_skill, call_gemini_with_retry

# Import Models
from app.models.test import TestLog
from app.models.user import User
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.story_topic import StoryTopic
from app.models.story_session import StorySession
from app.models.daily_quest import DailyQuest
from app.models.notification import Notification  # [ BỔ SUNG NOTIFICATION ]
from app import db

# Import Module AI & Leveling mới (Phase 3)
from app.utils.level_manager import check_and_update_level
from app.ml_models.intent_classifier import LocalIntentClassifier
from app.ml_models.vocab_classifier import VocabCEFRClassifier  # [ ĐÃ BỔ SUNG CEFR ENGINE ]

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
intent_engine = LocalIntentClassifier()
cefr_engine = VocabCEFRClassifier()  # [ KHỞI TẠO CEFR ENGINE TRỰC TIẾP TẠI ĐÂY ]


def check_and_complete_quest(user_id, text_input):
    """Hàm phụ trợ: Kiểm tra xem user có hoàn thành nhiệm vụ đặt câu hôm nay không"""
    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today, is_completed=False).all()
    for q in quests:
        v = Vocabulary.query.get(q.vocab_id)
        if v and v.word.lower() in text_input.lower():
            q.is_completed = True
            user = User.query.get(user_id)
            user.coins += 20  # Thưởng 20 xu khi hoàn thành quest
            db.session.commit()
            return v.word
    return None


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    user_input = data.get('text')
    mode = data.get('mode', 'grammar')

    if not user_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào hoặc phiên đăng nhập hết hạn!"}), 400

    quest_completed_word = None

    # 1. AI ORCHESTRATOR: Phân tích Intent trước khi xử lý
    detected_intent = intent_engine.predict(user_input)
    print(f"\n[LOCAL AI ENGINE] Text: '{user_input}' ---> Intent: {detected_intent.upper()}")

    try:
        # ==============================================================
        # NHÁNH 1: XỬ LÝ TEXT-RPG STORY (HỖ TRỢ STORY CHOOSE)
        # ==============================================================
        if mode in ['story', 'story_choose']:
            user = User.query.get(user_id)
            user_level = user.current_level if user else "Beginner"
            story_turn = int(data.get('turn', 1))
            story_history = data.get('history', '')
            topic_id = data.get('topic_id', 1)  # Mặc định lấy topic 1

            topic = StoryTopic.query.get(topic_id)
            theme_context = topic.system_prompt if topic else "Bối cảnh sinh tồn hậu tận thế tàn khốc."

            # KIỂM TRA NẾU ĐÂY LÀ LƯỢT CUỐI CÙNG (LƯỢT 10)
            if story_turn >= 10:
                prompt_summary = f"""
                            Ngữ cảnh thế giới: {theme_context}
                            Toàn bộ lịch sử các quyết định của người chơi từ Lượt 1 đến 9: 
                            {story_history}

                            Hành động quyết định cuối cùng (Lượt 10): "{user_input}"

                            Nhiệm vụ của Game Master (AI):
                            1. Chấm điểm hành động cuối (0-10).
                            2. Dựa vào bối cảnh và TẤT CẢ các quyết định của người chơi trong lịch sử, hãy SÁNG TÁC MỘT CÂU CHUYỆN HOÀN CHỈNH VÀ ĐẬM CHẤT ĐIỆN ẢNH (Cinematic Ending).
                               - Yêu cầu phải có: Miêu tả bối cảnh chi tiết, Lời thoại nhân vật sinh động (nếu có tương tác), Sự giằng xé/Hành động dồn dập, và Kết cục rõ ràng.
                               - TUYỆT ĐỐI KHÔNG tóm tắt ngắn gọn. Hãy viết thành 3 đến 5 đoạn văn dài, có chiều sâu cảm xúc (khoảng 200 - 400 từ).
                               - Dùng ký tự \\n\\n để tách các đoạn văn cho đẹp mắt.
                            3. Đưa ra kết cục (Survived hoặc Dead) dựa vào điểm số và độ hợp lý của các quyết định.

                            TUYỆT ĐỐI CHỈ TRẢ VỀ JSON HỢP LỆ (Không dùng markdown):
                            {{
                                "score": <điểm_số>, 
                                "feedback": "<nhận_xét_cuối>", 
                                "scene_en": "<CÂU_TRUYỆN_ĐẦY_ĐỦ_TIẾNG_ANH>", 
                                "scene_vn": "<BẢN_DỊCH_TIẾNG_VIỆT_CÂU_TRUYỆN>", 
                                "status": "Survived" hoặc "Dead", 
                                "is_end": true
                            }}
                            """
                clean_json_str = call_gemini_with_retry(prompt_summary)
                result = json.loads(clean_json_str)

                new_session = StorySession(
                    user_id=user_id, topic_id=topic_id if topic else 1,
                    summary_en=result.get("scene_en", ""), summary_vn=result.get("scene_vn", ""),
                    status=result.get("status", "Survived")
                )
                db.session.add(new_session)

            else:
                # Đang chơi giữa chừng (Turn 1 - 9)
                if mode == 'story_choose':
                    prompt_story = f"""
                    Ngữ cảnh: {theme_context}
                    Bạn là Game Master. Trình độ: {user_level}. Đang ở LƯỢT {story_turn}/10.
                    LỊCH SỬ: {story_history}
                    LỰA CHỌN CỦA NGƯỜI CHƠI: "{user_input}"

                    YÊU CẦU:
                    1. Đánh giá lựa chọn của người chơi (score 0-10) và feedback xéo xắt.
                    2. Kể tiếp cốt truyện dựa trên lựa chọn đó.
                    3. Đưa ra 4 LỰA CHỌN HÀNH ĐỘNG MỚI (bằng tiếng Anh).

                    TUYỆT ĐỐI CHỈ TRẢ VỀ JSON OBJECT (Không markdown):
                    {{
                        "score": <điểm_số>,
                        "feedback": "<nhận_xét>",
                        "scene_en": "<truyện_tiếng_Anh>",
                        "scene_vn": "<truyện_tiếng_Việt>",
                        "choices": ["Lựa chọn 1", "Lựa chọn 2", "Lựa chọn 3", "Lựa chọn 4"],
                        "is_end": false
                    }}
                    """
                else:
                    prompt_story = f"""
                    Ngữ cảnh bối cảnh: {theme_context}
                    Bạn là Game Master xéo xắt, mỏ hỗn. Trình độ người chơi: {user_level}. Đang ở LƯỢT {story_turn}/10.

                    LỊCH SỬ TỪ TRƯỚC TỚI NAY: 
                    {story_history}

                    HÀNH ĐỘNG MỚI NHẤT CỦA NGƯỜI CHƠI: "{user_input}"

                    YÊU CẦU:
                    1. Chấm điểm ngữ pháp (0-10) và feedback thật xéo xắt (Chửi nếu sai, khen ngạo nghễ nếu đúng).
                    2. Dựa vào hành động, sáng tạo tiếp cốt truyện kịch tính (scene_en, scene_vn). Nếu điểm < 5, cho nhân vật chịu hậu quả thê thảm.
                    3. Tạo gợi ý điền từ (hint_en, hint_vn) ẩn 1-2 từ khóa bằng dấu ___ cho lượt tới.

                    TUYỆT ĐỐI CHỈ TRẢ VỀ JSON OBJECT (Không markdown):
                    {{
                        "score": <điểm_số>, 
                        "feedback": "<nhận_xét_ngữ_pháp>",
                        "scene_en": "<truyện_tiếng_Anh>", 
                        "scene_vn": "<truyện_tiếng_Việt>",
                        "hint_en": "<gợi_ý>", 
                        "hint_vn": "<dịch_gợi_ý>",
                        "is_end": false
                    }}
                    """

                clean_json_str = call_gemini_with_retry(prompt_story)
                result = json.loads(clean_json_str)

        # ==============================================================
        # NHÁNH 2: XỬ LÝ HỌC TẬP (GRAMMAR/VOCAB) & DAILY QUESTS
        # ==============================================================
        else:
            context_challenge = ""

            if mode == 'grammar':
                grammar_list = Grammar.query.all()
                if grammar_list:
                    chosen = random.choice(grammar_list)
                    context_challenge = f"Hãy ép người dùng phải dùng hoặc kiểm tra xem họ có dùng đúng cấu trúc này không: {chosen.structure} ({chosen.explanation})."
                else:
                    context_challenge = "Kiểm tra ngữ pháp chung."

            elif mode == 'vocab':
                context_challenge = "Hãy tập trung kiểm tra cách sử dụng từ vựng, collocation và chỉ ra lỗi dùng từ lóng/từ vựng (nếu có)."

            elif mode == 'free':
                context_challenge = "Đây là câu tự do. Hãy chấm điểm ngữ pháp tiếng Anh cơ bản. Khen ngạo nghễ nếu tốt, chê xéo xắt nếu sai."

            ai_response_str = evaluate_english_skill(user_input, context_challenge)
            clean_json_str = ai_response_str.strip().replace('```json', '').replace('```', '')
            result = json.loads(clean_json_str)

            score = result.get("score", 0)

            # LUÔN KIỂM TRA QUEST DÙ Ở MODE NÀO
            quest_completed_word = check_and_complete_quest(user_id, user_input)

            if score >= 8.0:
                if mode in ['vocab', 'grammar']:
                    mine_new_data_via_ai(mode)

    except Exception as e:
        result = {
            "score": 4.0,
            "feedback": f"Hệ thống lõi gặp xung đột dữ liệu rồi! Lỗi: {str(e)}",
            "scene_en": "The system crashed. Reality is torn apart.",
            "scene_vn": "Hệ thống sụp đổ. Thực tại bị xé toạc.",
            "choices": ["Reboot System", "Wait for death", "Cry", "Run"],
            "hint_en": "I must ___ the truth.",
            "hint_vn": "Tôi phải (tìm_ra) sự thật.",
            "is_end": False
        }

    # Lưu log kiểm tra
    new_log = TestLog(
        user_id=user_id,
        score=result.get("score", 0),
        ai_feedback=result.get("feedback", "")
    )
    db.session.add(new_log)
    db.session.commit()

    # [ PHASE 3 ] KÍCH HOẠT DYNAMIC LEVELING SAU KHI LƯU DB
    level_up, new_rank = check_and_update_level(user_id)
    if level_up:
        result['level_up_notification'] = f"ĐẲNG CẤP MỚI: BẠN VỪA THĂNG CẤP LÊN '{new_rank.upper()}'!"

        # Bắn Notification vào CSDL
        notif = Notification(
            user_id=user_id,
            title="THĂNG CẤP",
            message=f"Bản thân bạn đã đột phá giới hạn! Đẳng cấp mới: {new_rank.upper()}",
            type="LEVEL_UP"
        )
        db.session.add(notif)
        db.session.commit()

    if quest_completed_word:
        result['quest_notification'] = f"HOÀN THÀNH NHIỆM VỤ: Đặt câu với từ '{quest_completed_word}' (+20 Xu)"

    return jsonify({"message": "Master G đã xử lý xong!", "result": result, "intent_detected": detected_intent}), 200


def mine_new_data_via_ai(current_mode):
    try:
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
            clean_json = call_gemini_with_retry(prompt)
            item_data = json.loads(clean_json)

            exists = Vocabulary.query.filter_by(word=item_data['word']).first()
            if not exists:
                # [ ĐÃ VÁ CEFR ] Phân loại tự động cấp độ trước khi insert DB
                predicted_level = cefr_engine.predict_cefr(item_data['word'])
                new_vocab = Vocabulary(
                    word=item_data['word'],
                    meaning=item_data['meaning'],
                    theme=item_data['theme'],
                    cefr_level=predicted_level,
                    image_url="default_lowpoly.png",
                    is_unlocked=False
                )
                db.session.add(new_vocab)
                db.session.commit()

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
            clean_json = call_gemini_with_retry(prompt)
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

    except Exception as e:
        print(f"Lỗi tiến trình AI đào dữ liệu: {e}")


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
        clean_text = call_gemini_with_retry(prompt)
        formatted_guide = clean_text.replace('\n', '<br>')
        return jsonify({"guide": formatted_guide}), 200
    except Exception as e:
        return jsonify({
            "guide": f"[OFFLINE MODE] Lõi AI đang bận tản nhiệt do quá tải! Gợi ý tạm: Hãy thử đặt câu dạng 'S + V + {word}' xem sao đồ ngốc!"
        }), 200


@ai_bp.route('/grammar_guide', methods=['POST'])
def get_grammar_guide():
    data = request.get_json(silent=True) or {}
    structure = data.get('structure')

    if not structure:
        return jsonify({"error": "Thiếu cấu trúc ngữ pháp"}), 400

    prompt = f"""
    Bạn là Master G. Học trò đang học cấu trúc ngữ pháp: '{structure}'.
    Hãy giải thích siêu ngắn gọn, xéo xắt nhưng dễ hiểu nhất.
    Yêu cầu:
    1. Nói sơ qua cách dùng (1 câu).
    2. Cho 2 ví dụ (1 cái bình thường, 1 cái cực kỳ hài hước/genZ).
    3. Dịch 2 ví dụ đó.
    Tuyệt đối không dùng markdown phức tạp. Xuống dòng dùng kí tự <br>
    """

    try:
        clean_text = call_gemini_with_retry(prompt)
        formatted_guide = clean_text.replace('\n', '<br>')
        return jsonify({"guide": formatted_guide}), 200
    except Exception as e:
        return jsonify({"guide": "[OFFLINE MODE] Lõi API đang sập. Tự mở sách ra mà học tạm đi!"}), 200


@ai_bp.route('/generate_unit', methods=['POST'])
def generate_unit():
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip().upper()
    user_id = session.get('user_id')

    if not topic:
        return jsonify({"error": "Vui lòng nhập chủ đề muốn học!"}), 400
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

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

    prompt = f"""
    Bạn là hệ thống thiết kế bài giảng. Người dùng muốn học tiếng Anh về chủ đề: '{topic}'.
    Hãy tạo ra 50 tới 100 từ vựng tiếng Anh (hoặc cụm từ) liên quan mật thiết đến chủ đề này.
    Tuyệt đối chỉ trả về 1 mảng JSON hợp lệ, KHÔNG chứa ký hiệu markdown.
    Cấu trúc:
    [
        {{"word": "từ_vựng_1", "meaning": "nghĩa tiếng Việt", "theme": "{topic}"}}
    ]
    """

    try:
        clean_json = call_gemini_with_retry(prompt)
        items = json.loads(clean_json)

        added_count = 0
        for item in items:
            v = Vocabulary.query.filter_by(word=item['word']).first()
            if not v:
                # [ ĐÃ VÁ CEFR ] Tính toán CEFR và nhét vào DB
                predicted_level = cefr_engine.predict_cefr(item['word'])
                v = Vocabulary(
                    word=item['word'],
                    meaning=item['meaning'],
                    theme=topic,
                    cefr_level=predicted_level,
                    image_url="default.png",
                    is_unlocked=True
                )
                db.session.add(v)
                db.session.flush()

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
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    topic_id = data.get('topic_id', 1)
    story_mode = data.get('mode', 'write')  # 'write' hoặc 'choose'

    user = User.query.get(user_id) if user_id else None
    user_level = user.current_level if user else "Beginner"

    topic = StoryTopic.query.get(topic_id)
    theme_context = topic.system_prompt if topic else "Bối cảnh sinh tồn hậu tận thế tàn khốc."

    if story_mode == 'choose':
        prompt = f"""
        Bạn là Game Master của một game Text-RPG.
        Ngữ cảnh thế giới: {theme_context}
        Trình độ người chơi: {user_level}. Đây là LƯỢT 1/10.

        Nhiệm vụ: Dựa vào ngữ cảnh trên, tạo bối cảnh mở màn ngầu, gai góc, ngắn gọn (2 câu) và 4 LỰA CHỌN tiếng Anh.

        CHỈ TRẢ VỀ ĐÚNG 1 OBJECT JSON, không dùng markdown (```json). Cấu trúc:
        {{
            "scene_en": "Cảnh báo hệ thống... Bạn tỉnh dậy...",
            "scene_vn": "Dịch tiếng Việt câu trên. Ngắn gọn.",
            "choices": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "is_end": false
        }}
        """
    else:
        prompt = f"""
        Bạn là Game Master của một game Text-RPG.
        Ngữ cảnh thế giới: {theme_context}
        Trình độ người chơi: {user_level}. Đây là LƯỢT 1/10.

        Nhiệm vụ: Dựa vào ngữ cảnh trên, tạo bối cảnh mở màn ngầu, gai góc, ngắn gọn (2 câu).
        Và tạo ra một GỢI Ý HÀNH ĐỘNG tiếp theo dạng ĐIỀN VÀO CHỖ TRỐNG (ẩn đi 1-2 từ khóa quan trọng bằng dấu ___ để người chơi tự ghép thành câu hoàn chỉnh).

        CHỈ TRẢ VỀ ĐÚNG 1 OBJECT JSON, không dùng markdown (```json). Cấu trúc:
        {{
            "scene_en": "Cảnh báo hệ thống... Bạn tỉnh dậy...",
            "scene_vn": "Dịch tiếng Việt câu trên. Ngắn gọn.",
            "hint_en": "I need to ___ my ___.",
            "hint_vn": "Tôi cần (tìm) (vũ khí) của mình.",
            "is_end": false
        }}
        """

    try:
        clean_json = call_gemini_with_retry(prompt)
        return jsonify(json.loads(clean_json)), 200
    except Exception as e:
        return jsonify({
            "scene_en": "System error. The world is collapsing.",
            "scene_vn": "Lỗi hệ thống. Thế giới đang sụp đổ.",
            "choices": ["Fix error", "Reboot", "Wait", "Quit"],
            "is_end": False
        }), 200


@ai_bp.route('/hint', methods=['POST'])
def get_hint():
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'grammar')

    prompt = f"""
    Người dùng đang bí ý tưởng đặt câu trong chế độ '{mode}'.
    Hãy cung cấp MỘT câu gợi ý dang dở (fill-in-the-blank) bằng tiếng Anh kèm dịch nghĩa tiếng Việt. 
    Chỉ trả về Text ngắn gọn dạng: "Gợi ý: I usually ___ (đi dạo) in the morning."
    KHÔNG DÙNG MARKDOWN.
    """
    try:
        clean_text = call_gemini_with_retry(prompt)
        return jsonify({"hint": clean_text}), 200
    except Exception as e:
        return jsonify({"hint": "Master G đang bận, tự nghĩ đi đồ lười!"}), 200