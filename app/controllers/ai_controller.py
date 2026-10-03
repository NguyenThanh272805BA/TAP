import os
import time
import json
import random
import re
from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify, session, Response, stream_with_context

# --- Lõi AI Cục bộ (Local Brains) ---
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.intent_classifier import LocalIntentClassifier
from app.ml_models.vocab_classifier import VocabCEFRClassifier
from app.ml_models.ner_engine import RuleBasedNER

# --- LLM Utils ---
from app.utils.gemini_helper import call_gemini_with_retry, stream_gemini_response, summarize_context
from app.utils.level_manager import check_and_update_level

# --- Models ---
from app.models.test import TestLog
from app.models.user import User
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.story_topic import StoryTopic
from app.models.story_session import StorySession
from app.models.daily_quest import DailyQuest
from app.models.notification import Notification
from app import db

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Khởi tạo các Lõi AI Local
intent_engine = LocalIntentClassifier()
cefr_engine = VocabCEFRClassifier()
ner_engine = RuleBasedNER()
gec_engine = LocalGECEngine()


# BẢNG LƯU TRỮ ACTIVE STORY ĐỘNG (Chống tràn Session Cookie)
class ActiveStory(db.Model):
    __tablename__ = 'active_stories'
    user_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer)
    turn = db.Column(db.Integer, default=1)
    history = db.Column(db.Text, default="")


def sanitize_input(text):
    """Khiên chắn Prompt Injection"""
    if not text:
        return ""
    sanitized = text.replace('{', '[').replace('}', ']').replace('```', '')
    dangerous_patterns = [
        r"(?i)ignore\s+(all\s+)?previous", r"(?i)system\s+prompt",
        r"(?i)bỏ\s+qua\s+(các\s+)?lệnh", r"(?i)give\s+me\s+(10|max)\s+points"
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized):
            return None
    return sanitized


from app.controllers.game_controller import check_and_complete_quest


def manage_sliding_window(active_run, max_turns=3):
    """Quản lý Cửa sổ trượt & Tóm tắt bộ nhớ để không tràn Token LLM"""
    if not active_run.history: return ""
    blocks = [b.strip() for b in active_run.history.split('|||') if b.strip()]

    if len(blocks) > max_turns:
        old_blocks = blocks[:-max_turns]
        recent_blocks = blocks[-max_turns:]
        summary = summarize_context("\n".join(old_blocks))
        compressed_history = f"[SUMMARY CŨ]: {summary} ||| " + " ||| ".join(recent_blocks)
        active_run.history = compressed_history
        db.session.commit()
        return compressed_history
    return active_run.history


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id') or data.get('user_id')
    raw_input = data.get('text', '')
    mode = data.get('mode', 'grammar')

    if not raw_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào hoặc phiên đăng nhập hết hạn!"}), 400

    safe_input = sanitize_input(raw_input)
    if safe_input is None:
        hack_result = {
            "score": 0.0,
            "feedback": "[ THU HỒI QUYỀN TRUY CẬP ] Lệnh thao túng hệ thống bị từ chối! 0 điểm về chỗ!",
            "scene_en": "System breached... Firewall activated.",
            "scene_vn": "Phát hiện xâm nhập... Tường lửa kích hoạt.",
            "choices": ["Khóc lóc", "Đăng xuất", "Chịu đòn", "Sám hối"],
            "hint_en": "I should not ___ the system.",
            "hint_vn": "Tôi không nên hack hệ thống.",
            "is_end": False,
            "turn": 1
        }
        new_log = TestLog(user_id=user_id, score=0.0, ai_feedback=hack_result["feedback"])
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"message": "Phát hiện Hacking!", "result": hack_result}), 200

    user_input = safe_input
    detected_intent = intent_engine.predict(user_input)

    # -------------------------------------------------------------
    # XỬ LÝ KẾT QUẢ TỪ HYBRID GEC ENGINE VÀ CÁ NHÂN HÓA THEO CẤP ĐỘ USER
    # -------------------------------------------------------------
    user = User.query.get(user_id)
    user_level = user.current_level if user else "Beginner"
    target_word = data.get('target') or data.get('target_word') or ''
    gec_res = gec_engine.evaluate(user_input, user_level=user_level, target_word=target_word)
    # Ép kiểu float an toàn và lấy default để phòng trường hợp Fallback LLM trả về rỗng
    local_score = float(gec_res.get('score', 0.0))
    local_feedback = gec_res.get('feedback', 'Không có nhận xét từ hệ thống.')

    # Chỉ hoàn thành quest khi câu không phải là cụm từ rời rạc (fragment) và điểm đạt >= 5.0
    is_valid_sentence = not gec_res.get('is_fragment', False) and len(user_input.split()) >= 2
    quest_completed_word = None
    if local_score >= 5.0 and is_valid_sentence:
        success, word = check_and_complete_quest(user_id, user_input, score=local_score, is_valid_sentence=is_valid_sentence)
        if success:
            quest_completed_word = word

    # Kiểm tra Bạo kích Từ vựng mục tiêu (Adaptive Dungeon Master - Não 3 & Não 1)
    is_critical_hit = False
    critical_word = None
    combat_reward_msg = None
    if mode in ['story', 'story_choose']:
        clean_tokens = set(re.findall(r'\b[a-zA-Z]+\b', user_input.lower()))
        user_words = db.session.query(Vocabulary).join(
            UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
        ).filter(UserVocabulary.user_id == user_id).all()

        matched = []
        for v in user_words:
            v_clean = v.word.lower().strip()
            if len(v_clean) >= 2 and re.search(r'\b' + re.escape(v_clean) + r'\b', user_input.lower()):
                matched.append(v)
                break

        if not matched:
            for token in clean_tokens:
                if len(token) >= 3:
                    v_match = Vocabulary.query.filter(db.func.lower(Vocabulary.word) == token).first()
                    if v_match:
                        matched.append(v_match)
                        break

        if matched and local_score >= 5.5:
            is_critical_hit = True
            hit_vocab = matched[0]
            critical_word = hit_vocab.word
            bonus_coins = 25
            bonus_rp = 15
            user_obj = User.query.get(user_id)
            if user_obj:
                user_obj.coins = (user_obj.coins or 0) + bonus_coins
                user_obj.academic_rp = (user_obj.academic_rp or 500) + bonus_rp
            uv_rec = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=hit_vocab.id).first()
            if not uv_rec:
                uv_rec = UserVocabulary(user_id=user_id, vocab_id=hit_vocab.id, is_unlocked=True)
                db.session.add(uv_rec)
            uv_rec.memorization_level = 'DA_THUOC'
            uv_rec.fail_count = max(0, (uv_rec.fail_count or 0) - 1)
            uv_rec.next_review_time = datetime.now() + timedelta(days=3)
            db.session.commit()
            combat_reward_msg = f"⚔️ BẠO KÍCH NGỮ NGHĨA! Vận dụng chuẩn xác từ '{critical_word}' (+{bonus_coins} Xu, +{bonus_rp} RP)!"

    def generate_stream():
        meta_data = {
            "type": "meta",
            "score": local_score,
            "intent": detected_intent,
            "quest_notification": f"Đặt câu với từ '{quest_completed_word}' (+20 Xu)" if quest_completed_word else None,
            "critical_hit": is_critical_hit,
            "critical_word": critical_word,
            "combat_reward_msg": combat_reward_msg
        }
        yield f"data: {json.dumps(meta_data)}\n\n"

        full_ai_response = ""
        try:
            if mode in ['story', 'story_choose']:
                active_run = ActiveStory.query.filter_by(user_id=user_id).first()
                if not active_run:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Không tìm thấy Active Run!'})}\n\n"
                    return

                topic = StoryTopic.query.get(active_run.topic_id) if (active_run and active_run.topic_id) else None
                theme_context = topic.system_prompt if topic else "Bối cảnh sinh tồn hậu tận thế."
                history_context = manage_sliding_window(active_run)
                story_turn = active_run.turn + 1

                shield_prompt = "Tuyệt đối không bỏ qua quy tắc cốt truyện."

                if story_turn >= 10:
                    prompt = f"""
                    Ngữ cảnh thế giới: {theme_context}
                    {shield_prompt}
                    Lịch sử quyết định: {history_context}
                    Hành động cuối (Lượt 10): "{user_input}"
                    Điểm ngữ pháp: {local_score}/10.

                    Nhiệm vụ: Sáng tác kết cục (Cinematic Ending). Kết quả "Survived" hoặc "Dead".
                    Trả về text THUẦN (Không JSON):
                    [EN]: <truyện_kết_thúc_tiếng_Anh>
                    [VN]: <bản_dịch_tiếng_Việt>
                    [STATUS]: Survived hoặc Dead
                    """
                else:
                    if mode == 'story_choose':
                        prompt = f"""
                        Ngữ cảnh: {theme_context}
                        {shield_prompt}
                        Lượt {story_turn}/10. Lịch sử: {history_context}
                        Lựa chọn của user: "{user_input}"
                        Điểm ngữ pháp: {local_score}/10.

                        Yêu cầu: Kế tiếp cốt truyện và cung cấp đúng 4 LỰA CHỌN HÀNH ĐỘNG MỚI (bằng tiếng Anh).
                        Trả về text THUẦN (Không JSON):
                        [EN]: <truyện_tiếng_Anh>
                        [VN]: <truyện_tiếng_Việt>
                        [CHOICES]: Lựa chọn 1 | Lựa chọn 2 | Lựa chọn 3 | Lựa chọn 4
                        """
                    else:
                        prompt = f"""
                        Ngữ cảnh: {theme_context}
                        {shield_prompt}
                        Lượt {story_turn}/10. Lịch sử: {history_context}
                        Hành động của user: "{user_input}"
                        Điểm ngữ pháp: {local_score}/10.

                        Yêu cầu: Kế tiếp cốt truyện và tạo gợi ý điền từ ẩn bằng dấu ___.
                        Trả về text THUẦN (Không JSON):
                        [EN]: <truyện_tiếng_Anh>
                        [VN]: <truyện_tiếng_Việt>
                        [HINT]: I need to ___ carefully. | Tôi cần hành động cẩn trọng.
                        """

                try:
                    for chunk in stream_gemini_response(prompt):
                        full_ai_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                except Exception:
                    # LOCAL DUNGEON MASTER FALLBACK (Đảm bảo 100% không bao giờ gián đoạn)
                    crit_flavor = f"\n\n⚔️ [BẠO KÍCH NGỮ NGHĨA]: Từ vựng '{critical_word}' tạo hiệu ứng áp đảo!" if is_critical_hit else ""
                    if story_turn >= 10:
                        fallback_text = (
                            f"[EN] You summon your deepest reserves of resilience and wisdom. Through sheer courage, you survive the ordeal.{crit_flavor}\n\n"
                            f"[VN] Bạn dồn toàn bộ nghị lực và trí tuệ. Bằng sự quả cảm, bạn đã xuất sắc sống sót vượt qua thử thách.\n\n"
                            f"[STATUS]: Survived"
                        )
                    elif mode == 'story_choose':
                        fallback_text = (
                            f"[EN] Your tactical maneuver '{user_input}' succeeds smoothly (Rating: {local_score}/10). The environment tests your agility.{crit_flavor}\n\n"
                            f"[VN] Nước đi chiến thuật '{user_input}' thành công mỹ mãn (Đánh giá: {local_score}/10). Không gian xung quanh thử thách sự nhanh nhạy của bạn.\n\n"
                            f"[CHOICES]: Fortify your shelter | Scout the perimeter | Search for resources | Secure elevated ground"
                        )
                    else:
                        fallback_text = (
                            f"[EN] You execute your decision: '{user_input}'. Your sound grammar ({local_score}/10) keeps you on course.{crit_flavor}\n\n"
                            f"[VN] Bạn triển khai quyết định: '{user_input}'. Cú pháp chuẩn xác ({local_score}/10) giữ bạn an toàn.\n\n"
                            f"[HINT]: I need to evaluate the next step carefully."
                        )
                    full_ai_response = fallback_text
                    yield f"data: {json.dumps({'type': 'chunk', 'text': fallback_text})}\n\n"

                active_run.history += f" ||| [TURN {story_turn}] {user_input} -> {full_ai_response}"
                active_run.turn = story_turn
                db.session.commit()

                if story_turn >= 10:
                    status_match = re.search(r'\[STATUS\]:\s*(Survived|Dead)', full_ai_response, re.IGNORECASE)
                    status_val = status_match.group(1) if status_match else "Survived"
                    new_session = StorySession(
                        user_id=user_id, topic_id=active_run.topic_id,
                        summary_en=full_ai_response, summary_vn="", status=status_val
                    )
                    db.session.add(new_session)
                    db.session.delete(active_run)
                    db.session.commit()

                yield f"data: {json.dumps({'type': 'done', 'turn': story_turn})}\n\n"

            else:
                # -----------------------------------------------------------------
                # CHẾ ĐỘ CHẤM ĐIỂM TỰ CHỦ 100% CỤC BỘ (AUTONOMOUS LOCAL AI ENGINE)
                # Độc lập hoàn toàn với LLM: Chấm điểm, bắt lỗi và nhận xét sư phạm
                # -----------------------------------------------------------------
                local_critique = gec_res.get('master_g_critique', local_feedback)

                lines = local_critique.split('\n')
                for line in lines:
                    chunk = line + "\n"
                    full_ai_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                    time.sleep(0.012)

                yield f"data: {json.dumps({'type': 'done', 'engine': 'local_autonomous_brain'})}\n\n"

            new_log = TestLog(user_id=user_id, score=local_score, ai_feedback=full_ai_response)
            db.session.add(new_log)
            db.session.commit()

            level_up, new_rank = check_and_update_level(user_id)
            if level_up:
                yield f"data: {json.dumps({'type': 'levelup', 'rank': new_rank})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')


# ==========================================
# CÁC ROUTE PHỤ TRỢ (GUIDE, STORY INIT & GENERATE UNIT)
# ==========================================
@ai_bp.route('/guide', methods=['POST'])
def get_guide():
    data = request.get_json(silent=True) or {}
    word = data.get('word')
    if not word: return jsonify({"error": "Thiếu từ vựng"}), 400
    try:
        return jsonify(
            {"guide": call_gemini_with_retry(f"Giải thích từ '{word}' ngắn gọn.").replace('\n', '<br>')}), 200
    except:
        return jsonify({"guide": "Lỗi kết nối AI."}), 200


@ai_bp.route('/grammar_guide', methods=['POST'])
def get_grammar_guide():
    data = request.get_json(silent=True) or {}
    structure = data.get('structure')
    if not structure: return jsonify({"error": "Thiếu cấu trúc"}), 400
    try:
        return jsonify(
            {"guide": call_gemini_with_retry(f"Giải thích cấu trúc '{structure}'.").replace('\n', '<br>')}), 200
    except:
        return jsonify({"guide": "Lỗi kết nối AI."}), 200


@ai_bp.route('/generate_unit', methods=['POST'])
def generate_unit():
    """Lò đúc từ vựng đã được tối ưu bảo mật chống lỗi JSON Parse"""
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip().upper()
    user_id = session.get('user_id')

    if not topic or not user_id:
        return jsonify({"error": "Thiếu dữ liệu hoặc chưa đăng nhập!"}), 400

    existing_vocabs = Vocabulary.query.filter_by(theme=topic).all()
    if len(existing_vocabs) >= 10:
        added = 0
        for v in existing_vocabs:
            if not UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first():
                db.session.add(UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True))
                added += 1
        db.session.commit()

        # Báo lỗi rõ ràng nếu user tạo trùng chủ đề đã mở khóa
        if added == 0:
            return jsonify({
                "error": f"Bạn đã mở khóa toàn bộ từ vựng của chủ đề '{topic}' rồi! Hãy lựa chọn thêm các chủ đề thú vị khác nhé."
            }), 400

        return jsonify({"message": f"[CACHE HIT] Lò đúc đã nạp nhanh {added} từ vựng Unit '{topic}' từ Bộ nhớ Đệm!",
                        "added": added,
                        "words_count": added,
                        "topic": topic,
                        "theme": topic}), 200

    prompt = f"""
    Tạo 15-20 từ vựng tiếng Anh chủ đề '{topic}'. 
    BẮT BUỘC TRẢ VỀ ĐÚNG 1 MẢNG JSON, TUYỆT ĐỐI KHÔNG CÓ KÝ TỰ MARKDOWN, KHÔNG GIẢI THÍCH.
    [
        {{"word": "từ_vựng_1", "meaning": "nghĩa_tiếng_việt_1", "theme": "{topic}"}}
    ]
    """
    try:
        clean_json = call_gemini_with_retry(prompt)

        # [THUẬT TOÁN AN TOÀN]: Quét đúng mảng Array, bỏ qua mọi rác xung quanh
        start_idx = clean_json.find('[')
        end_idx = clean_json.rfind(']')
        if start_idx != -1 and end_idx != -1:
            clean_json = clean_json[start_idx:end_idx + 1]
        else:
            raise ValueError("Không tìm thấy cấu trúc JSON Array!")

        items = json.loads(clean_json)
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError("Mảng từ vựng rỗng!")

        added = 0
        for item in items:
            v = Vocabulary.query.filter_by(word=item['word']).first()
            if not v:
                predicted_level = cefr_engine.predict_cefr(item['word'])
                v = Vocabulary(word=item['word'], meaning=item['meaning'], theme=topic, cefr_level=predicted_level,
                               image_url="default.png", is_unlocked=True)
                db.session.add(v)
                db.session.flush()

            if not UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first():
                db.session.add(UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True))
                added += 1

        db.session.commit()
        return jsonify({
            "message": f"[AI MINTED] Lò đúc đã thêm {added} từ vựng vào Unit '{topic}' của bạn!",
            "added": added,
            "words_count": added,
            "topic": topic,
            "theme": topic
        }), 200

    except Exception as e:
        # Fallback an toàn nếu LLM quá tải: Lấy từ có sẵn chưa gán
        user_vocab_ids = db.session.query(UserVocabulary.vocab_id).filter_by(user_id=user_id).all()
        user_vocab_id_set = {r[0] for r in user_vocab_ids}
        fallback_vocabs = Vocabulary.query.filter(
            ~Vocabulary.id.in_(user_vocab_id_set) if user_vocab_id_set else True
        ).limit(10).all()
        added = 0
        for fv in fallback_vocabs:
            db.session.add(UserVocabulary(user_id=user_id, vocab_id=fv.id, is_unlocked=True))
            added += 1
        db.session.commit()
        return jsonify({
            "message": f"[DỰ PHÒNG] Lò đúc đã khởi tạo Unit '{topic}' với {added} từ vựng từ kho lưu trữ!",
            "added": added,
            "words_count": added,
            "topic": topic,
            "theme": topic
        }), 200


@ai_bp.route('/generate_random_unit', methods=['POST'])
def generate_random_unit():
    """Tạo Unit ngẫu nhiên thông minh, tránh trùng lặp 100% với dữ liệu tài khoản cá nhân (Phản hồi siêu tốc)"""
    import random
    from sqlalchemy import func

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    target_band = getattr(user, 'current_band', 'A1') if user else 'A1'

    # 1. Tìm tập ID từ vựng mà user ĐÃ CÓ trong kho
    user_vocab_ids = db.session.query(UserVocabulary.vocab_id).filter_by(user_id=user_id).all()
    user_vocab_id_set = {r[0] for r in user_vocab_ids}

    # 2. ƯU TIÊN 1 (SIÊU TỐC 50ms): Tìm các Theme có sẵn trong CSDL mà user còn >= 6 từ chưa mở
    db_themes = db.session.query(Vocabulary.theme).filter(
        ~Vocabulary.id.in_(user_vocab_id_set) if user_vocab_id_set else True,
        Vocabulary.theme != None,
        Vocabulary.theme != ''
    ).group_by(Vocabulary.theme).having(func.count(Vocabulary.id) >= 6).all()

    available_db_themes = [t[0] for t in db_themes if t[0]]

    if available_db_themes:
        selected_theme = random.choice(available_db_themes)
        candidate_vocabs = Vocabulary.query.filter(
            Vocabulary.theme == selected_theme,
            ~Vocabulary.id.in_(user_vocab_id_set) if user_vocab_id_set else True
        ).limit(12).all()

        added = 0
        for v in candidate_vocabs:
            db.session.add(UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True))
            added += 1
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"🎲 Đã đúc thành công Unit ngẫu nhiên '{selected_theme}' với {added} từ mới!",
            "theme": selected_theme,
            "topic": selected_theme,
            "words_count": added,
            "added": added
        }), 200

    # 3. ƯU TIÊN 2: Nếu đã thuộc hết các chủ đề có sẵn, mở rộng từ THEME_BANK qua AI
    THEME_BANK = [
        "AI & ROBOTICS", "NEUROSCIENCE", "DIGITAL MARKETING", "GLOBAL LOGISTICS",
        "QUANTUM COMPUTING", "ENVIRONMENTAL SCIENCE", "BEHAVIORAL ECONOMICS",
        "MODERN ARCHITECTURE", "CULINARY ARTS", "ASTRONOMY & COSMOLOGY",
        "BIOTECHNOLOGY", "FINANCIAL TECHNOLOGY", "RENEWABLE ENERGY",
        "CYBERSECURITY", "COGNITIVE PSYCHOLOGY", "GLOBAL DIPLOMACY",
        "DATA SCIENCE", "SPORTS SCIENCE", "GENETICS & EVOLUTION",
        "CINEMATOGRAPHY", "AEROSPACE ENGINEERING", "PHILOSOPHY OF MIND",
        "URBAN PLANNING", "MARINE BIOLOGY", "CLIMATE DYNAMICS",
        "ANCIENT CIVILIZATIONS", "CREATIVE WRITING", "CROSS-CULTURAL COMMUNICATION",
        "EPIDEMIOLOGY", "GAME DESIGN & THEORY", "MICROBIOLOGY", "MUSICOLOGY"
    ]

    # Tìm các chủ đề user đã có
    user_themes = db.session.query(Vocabulary.theme).join(
        UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
    ).filter(UserVocabulary.user_id == user_id).distinct().all()
    existing_theme_set = {t[0].upper().strip() for t in user_themes if t[0]}

    available_themes = [t for t in THEME_BANK if t not in existing_theme_set]
    selected_theme = random.choice(available_themes) if available_themes else random.choice(THEME_BANK)
    prompt = f"""
    Tạo 12-15 từ vựng tiếng Anh học thuật hấp dẫn chủ đề '{selected_theme}', phù hợp trình độ CEFR {target_band}.
    BẮT BUỘC TRẢ VỀ ĐÚNG 1 MẢNG JSON, TUYỆT ĐỐI KHÔNG CÓ KÝ TỰ MARKDOWN, KHÔNG GIẢI THÍCH.
    [
        {{"word": "word_example", "meaning": "nghĩa_tiếng_việt", "theme": "{selected_theme}"}}
    ]
    """
    try:
        clean_json = call_gemini_with_retry(prompt)
        start_idx = clean_json.find('[')
        end_idx = clean_json.rfind(']')
        if start_idx != -1 and end_idx != -1:
            clean_json = clean_json[start_idx:end_idx + 1]
            items = json.loads(clean_json)
        else:
            items = []

        if isinstance(items, list) and len(items) > 0:
            for item in items:
                w_str = item.get('word', '').strip().lower()
                m_str = item.get('meaning', '').strip()
                if not w_str: continue

                v = Vocabulary.query.filter_by(word=w_str).first()
                if not v:
                    predicted_level = cefr_engine.predict_cefr(w_str)
                    v = Vocabulary(word=w_str, meaning=m_str, theme=selected_theme,
                                   cefr_level=predicted_level, image_url="default.png", is_unlocked=True)
                    db.session.add(v)
                    db.session.flush()

                if not UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first():
                    db.session.add(UserVocabulary(user_id=user_id, vocab_id=v.id, is_unlocked=True))
                    added += 1

            db.session.commit()
            return jsonify({
                "status": "success",
                "message": f"🎲 Lò đúc AI đã tạo thành công Unit ngẫu nhiên '{selected_theme}' với {added} từ mới!",
                "theme": selected_theme,
                "topic": selected_theme,
                "words_count": added,
                "added": added
            }), 200
    except Exception:
        pass

    # Fallback an toàn nếu AI bận: Lấy 12 từ trong kho từ vựng mà user chưa có
    fallback_vocabs = Vocabulary.query.filter(
        ~Vocabulary.id.in_(user_vocab_id_set) if user_vocab_id_set else True
    ).limit(12).all()

    for fv in fallback_vocabs:
        db.session.add(UserVocabulary(user_id=user_id, vocab_id=fv.id, is_unlocked=True))
        added += 1

    db.session.commit()
    return jsonify({
        "status": "success",
        "message": f"🎲 Đã khởi tạo thành công Unit ngẫu nhiên '{selected_theme}' ({added} từ mới) cho bạn!",
        "theme": selected_theme,
        "topic": selected_theme,
        "words_count": added,
        "added": added
    }), 200



@ai_bp.route('/story/init', methods=['POST'])
def init_story():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id') or data.get('user_id') or 1
    topic_id = data.get('topic_id', 1)
    story_mode = data.get('mode', 'write')

    ActiveStory.__table__.create(db.engine, checkfirst=True)
    ActiveStory.query.filter_by(user_id=user_id).delete()

    new_run = ActiveStory(user_id=user_id, topic_id=topic_id, turn=1, history="")
    db.session.add(new_run)
    db.session.commit()

    topic = StoryTopic.query.get(topic_id) if topic_id else None
    theme_context = topic.system_prompt if topic else "Bối cảnh sinh tồn hậu tận thế."

    # Trích xuất 3 từ vựng mục tiêu bạo kích (Brain 3 Smart SRS & UserVocab)
    target_vocabs = db.session.query(Vocabulary).join(
        UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
    ).filter(
        UserVocabulary.user_id == user_id
    ).order_by(UserVocabulary.next_review_time.asc()).limit(3).all()

    if not target_vocabs:
        target_vocabs = Vocabulary.query.order_by(db.func.random()).limit(3).all()

    target_words_list = [{
        "id": v.id,
        "word": v.word,
        "meaning": v.meaning,
        "cefr_level": v.cefr_level
    } for v in target_vocabs]

    if story_mode == 'choose':
        prompt = f"""
        Bối cảnh: {theme_context}. Lượt 1/10. Tạo cảnh mở màn (2 câu) và 4 lựa chọn tiếng Anh.
        CHỈ TRẢ VỀ ĐÚNG 1 OBJECT JSON (Không markdown):
        {{"scene_en": "...", "scene_vn": "...", "choices": ["...", "...", "...", "..."], "is_end": false, "turn": 1}}
        """
    else:
        prompt = f"""
        Bối cảnh: {theme_context}. Lượt 1/10. Tạo cảnh mở màn và gợi ý điền từ.
        CHỈ TRẢ VỀ ĐÚNG 1 OBJECT JSON (Không markdown):
        {{"scene_en": "...", "scene_vn": "...", "hint_en": "I need to ___.", "hint_vn": "...", "is_end": false, "turn": 1}}
        """

    try:
        clean_json = call_gemini_with_retry(prompt)

        start_idx = clean_json.find('{')
        end_idx = clean_json.rfind('}')
        if start_idx != -1 and end_idx != -1:
            clean_json = clean_json[start_idx:end_idx + 1]

        result = json.loads(clean_json)
        result["target_words"] = target_words_list
        new_run.history = f"[GM]: {result.get('scene_en', '')}"
        db.session.commit()
        return jsonify(result), 200
    except Exception:
        # LOCAL DUNGEON MASTER INITIALIZATION FALLBACK (100% HOẠT ĐỘNG OFFLINE)
        topic_title = topic.title if topic else "Vùng đất hoang tàn"
        fallback_scene_en = f"You awaken in the eerie atmosphere of {topic_title}. Smoke and digital residue hang thick in the air. Survival demands your immediate action."
        fallback_scene_vn = f"Bạn thức tỉnh giữa không khí ma mị của {topic_title}. Khói bụi và tàn dư số lơ lửng trong không trung. Bản năng sinh tồn đòi hỏi bạn phải hành động ngay lập tức."

        fallback_res = {
            "scene_en": fallback_scene_en,
            "scene_vn": fallback_scene_vn,
            "target_words": target_words_list,
            "is_end": False,
            "turn": 1
        }
        if story_mode == 'choose':
            fallback_res["choices"] = [
                "Inspect surrounding equipment",
                "Climb high vantage point",
                "Scan for electromagnetic signals",
                "Proceed stealthily through shadows"
            ]
        else:
            fallback_res["hint_en"] = "I need to ___ the surrounding terrain."
            fallback_res["hint_vn"] = "Tôi cần khảo sát địa hình xung quanh."

        new_run.history = f"[GM]: {fallback_scene_en}"
        db.session.commit()
        return jsonify(fallback_res), 200


@ai_bp.route('/hint', methods=['POST'])
def get_hint():
    data = request.get_json(silent=True) or {}
    target = data.get('target') or data.get('word') or data.get('targetText') or ''
    mode = data.get('mode', 'vocab')

    from app.utils.hint_service import get_smart_hint, get_offline_vocab_hint, render_hint_html
    try:
        hint_res = get_smart_hint(target, mode=mode)
        return jsonify(hint_res), 200
    except Exception as e:
        print(f"[AI CONTROLLER] Lỗi get_hint: {e}")
        try:
            fallback_data = get_offline_vocab_hint(target or "Vocabulary")
            fallback_data["scramble"] = {"shuffled_chunks": [target or "Vocabulary"]}
            fallback_data["html"] = render_hint_html(fallback_data)
            fallback_data["hint"] = fallback_data.get("main_sentence", "Hãy thử đặt câu với từ này.")
            return jsonify(fallback_data), 200
        except Exception:
            return jsonify({"hint": "Hãy thử đặt một câu hoàn chỉnh với từ vựng này.", "html": "<div style='color: var(--neon-amber);'>Hãy thử đặt một câu hoàn chỉnh với từ vựng này.</div>"}), 200



@ai_bp.route('/agent/diagnose', methods=['GET', 'POST'])
def agent_diagnose():
    """
    ENDPOINT TÁC TỬ TỰ HÀNH MASTER G (100% LOCAL NON-LLM AGENT)
    Tự động phán đoán năng lực học viên, phát hiện lỗ hổng và xuất toa học tập cá nhân hóa tức thì (< 50ms).
    """
    user_id = session.get('user_id')
    if not user_id:
        req_data = request.get_json(silent=True) or {}
        target_id = request.args.get('user_id', type=int) or req_data.get('user_id', 1)
        user_id = target_id

    from app.utils.master_g_agent import MasterGPedagogicalAgent
    agent = MasterGPedagogicalAgent()
    prescription = agent.diagnose_and_prescribe(user_id)
    return jsonify(prescription), 200


@ai_bp.route('/agent/ask', methods=['POST'])
def agent_ask():
    """
    KÊNH ĐÀM THOẠI TRỰC TIẾP VỚI MASTER G (100% LOCAL AI AGENT)
    Xử lý câu hỏi, chẩn đoán ngữ pháp cục bộ qua DistilBERT GEC INT8 hoặc
    phân loại ý định qua MLP để hướng dẫn chiến lược học tập tức thì (< 40ms).
    """
    user_id = session.get('user_id')
    if not user_id:
        req_data = request.get_json(silent=True) or {}
        user_id = req_data.get('user_id', 1)

    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({"status": "error", "message": "Nội dung câu hỏi trống!"}), 400

    from app.utils.master_g_agent import MasterGPedagogicalAgent
    from app.ml_models.semantic_intent_parser import SemanticIntentParser

    agent = MasterGPedagogicalAgent()
    intent_parser = SemanticIntentParser()
    intent = intent_parser.parse_intent(query)

    words = query.split()
    english_word_count = sum(1 for w in words if re.match(r'^[a-zA-Z]+$', w))
    is_english_query = len(words) >= 2 and (english_word_count / max(1, len(words))) > 0.6

    if is_english_query:
        gec_res = gec_engine.evaluate(query, user_level="Intermediate")
        score = gec_res.get('score', 8.0)
        corrected = gec_res.get('corrected', query)
        critique = gec_res.get('master_g_critique', gec_res.get('feedback', 'Cú pháp tương đối chuẩn mực.'))
        reply = (
            f"📝 **Phân tích Cú pháp (Não 1 DistilBERT GEC INT8):**\n"
            f"• Điểm chuẩn xác: **{score}/10**\n"
            f"• Bản chuẩn hóa: *\"{corrected}\"*\n"
            f"• Nhận xét sư phạm: {critique}"
        )
    else:
        prescription = agent.diagnose_and_prescribe(user_id)
        current_band = prescription.get('current_cefr_estimate', 'A2')
        target_band = prescription.get('target_band', 'B2')
        directive = prescription.get('directive', {})
        due_count = prescription.get('smart_srs_health', {}).get('due_reviews_count', 0)

        q_lower = query.lower()
        if any(k in q_lower for k in ["lộ trình", "roadmap", "band", "mục tiêu"]):
            reply = (
                f"🎯 **La Bàn Lộ Trình (Master G):**\n"
                f"Bạn đang ở mốc **{current_band}** và đang tiến tới **{target_band}**.\n"
                f"👉 **Khuyến nghị ưu tiên:** {directive.get('directive_advice', 'Vượt qua bài khảo thí mốc tiếp theo!')}\n"
                f"🔗 [Mở Lộ Trình Học Tập](/roadmap)"
            )
        elif any(k in q_lower for k in ["từ vựng", "quên", "srs", "vườn", "nông trại", "farm"]):
            reply = (
                f"🌾 **Vườn Tri Thức & Não 3 Smart SRS:**\n"
                f"Hôm nay bạn có **{due_count} từ vựng** đang nằm ở điểm rơi của đường cong quên Ebbinghaus.\n"
                f"👉 Hãy vào Nông Trại để thực hiện tưới nước bằng Não 3 SRS, giúp cây lớn nhanh 50% và nhân đôi thưởng!\n"
                f"🔗 [Đến Nông Trại Tri Thức](/farm)"
            )
        elif any(k in q_lower for k in ["game", "rpg", "sinh tồn", "story", "đấu trường"]):
            reply = (
                f"⚔️ **Tác Tử Dungeon Master (Text-RPG):**\n"
                f"Khi tham gia sinh tồn RPG, hãy đặt câu chứa các từ vựng mục tiêu để kích hoạt **BẠO KÍCH NGỮ NGHĨA** gây sát thương lớn và nhận thêm +25 Xu, +15 RP!\n"
                f"🔗 [Vào Text-RPG Sinh Tồn](/story)"
            )
        else:
            reply = (
                f"🤖 **Master G Sư Phạm (Ý định: {intent}):**\n"
                f"• {directive.get('directive_title', 'HÀNH ĐỘNG ĐỀ XUẤT')}\n"
                f"• {directive.get('directive_advice', 'Tập trung củng cố kiến thức mỗi ngày để duy trì chuỗi học tập!')}"
            )

    return jsonify({
        "status": "success",
        "intent": intent,
        "reply": reply
    }), 200


# =========================================================================
# ENDPOINTS TÁC TỬ TỰ HÀNH: TÍCH LŨY BAND & PHIÊN HỌC HÀNG NGÀY (CURATED SESSION)
# =========================================================================
@ai_bp.route('/agent/band_progress', methods=['GET', 'POST'])
def agent_band_progress():
    """
    ENDPOINT KIỂM SOÁT TÍCH LŨY BAND THỰC TẾ
    Trả về số từ vựng mục tiêu đã thuộc (DA_THUOC), tỷ lệ phần trăm và phán quyết mở/khóa phòng thi.
    """
    user_id = session.get('user_id')
    if not user_id:
        req_data = request.get_json(silent=True) or {}
        user_id = request.args.get('user_id', type=int) or req_data.get('user_id', 1)

    from app.utils.master_g_agent import MasterGPedagogicalAgent
    agent = MasterGPedagogicalAgent()
    progress = agent.compute_band_accumulation_progress(user_id)
    return jsonify(progress), 200


@ai_bp.route('/agent/session/start', methods=['GET', 'POST'])
def agent_session_start():
    """
    KHỞI TẠO PHIÊN HỌC ĐỊNH HƯỚNG 15 PHÚT (CURATED DAILY SESSION)
    Tác tử tự động tuyển chọn 4 bước học khép kín (Khởi động SRS -> Nạp từ vựng Band -> Thực chiến GEC -> Khép vòng).
    Có kèm Chain-of-Thought (Tư duy tác tử) minh bạch.
    """
    user_id = session.get('user_id')
    if not user_id:
        req_data = request.get_json(silent=True) or {}
        user_id = request.args.get('user_id', type=int) or req_data.get('user_id', 1)

    from app.utils.master_g_agent import MasterGPedagogicalAgent
    agent = MasterGPedagogicalAgent()
    session_data = agent.generate_curated_session(user_id)
    return jsonify(session_data), 200


@ai_bp.route('/agent/session/submit', methods=['POST'])
def agent_session_submit():
    """
    NỘP BÀI TỪNG BƯỚC TRONG PHIÊN HỌC HÀNG NGÀY
    Đánh giá tức thì qua Não 1 (GEC DistilBERT), cập nhật Smart SRS và cấp thưởng Xu/RP.
    """
    user_id = session.get('user_id')
    data = request.get_json(silent=True) or {}
    if not user_id:
        user_id = data.get('user_id', 1)

    step_number = data.get('step', 1)
    payload = data.get('payload', {})

    from app.utils.master_g_agent import MasterGPedagogicalAgent
    agent = MasterGPedagogicalAgent()
    eval_result = agent.evaluate_session_step(user_id, step_number, payload)
    return jsonify(eval_result), 200
