import os
import json
import random
import re
from datetime import date
from flask import Blueprint, request, jsonify, session, Response, stream_with_context

# --- Lõi AI Cục bộ (Local Brains) ---
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.intent_classifier import LocalIntentClassifier
from app.ml_models.vocab_classifier import VocabCEFRClassifier
from app.ml_models.ner_engine import RuleBasedNER

# --- LLM Utils ---
from app.utils.gemini_helper import stream_gemini_response, call_gemini_with_retry, summarize_context
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

# Khởi tạo các Lõi (O(1) time complexity)
gec_engine = LocalGECEngine()
intent_engine = LocalIntentClassifier()
cefr_engine = VocabCEFRClassifier()
ner_engine = RuleBasedNER()


# [ BẢO MẬT HIỆU NĂNG ] BẢNG LƯU TRỮ ACTIVE STORY ĐỘNG (Chống tràn Session)
class ActiveStory(db.Model):
    __tablename__ = 'active_stories'
    user_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer)
    turn = db.Column(db.Integer, default=1)
    history = db.Column(db.Text, default="")


def sanitize_input(text):
    """Khiên chắn Prompt Injection"""
    if not text: return ""
    sanitized = text.replace('{', '[').replace('}', ']').replace('```', '')
    dangerous_patterns = [
        r"(?i)ignore\s+(all\s+)?previous", r"(?i)system\s+prompt",
        r"(?i)bỏ\s+qua\s+(các\s+)?lệnh", r"(?i)give\s+me\s+(10|max)\s+points"
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized): return None
    return sanitized


def check_and_complete_quest(user_id, text_input):
    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today, is_completed=False).all()
    for q in quests:
        v = Vocabulary.query.get(q.vocab_id)
        if v and v.word.lower() in text_input.lower():
            q.is_completed = True
            user = User.query.get(user_id)
            user.coins += 20
            db.session.commit()
            return v.word
    return None


def manage_sliding_window(active_run, max_turns=3):
    """[ TỐI ƯU TOKEN ] Quản lý Cửa sổ trượt (Sliding Window) & Bộ nhớ Đệm (Summary Buffer)"""
    if not active_run.history: return ""
    blocks = [b.strip() for b in active_run.history.split('|||') if b.strip()]

    if len(blocks) > max_turns:
        old_blocks = blocks[:-max_turns]
        recent_blocks = blocks[-max_turns:]
        summary = summarize_context("\n".join(old_blocks))  # Trích xuất ý chính
        compressed_history = f"[SUMMARY CŨ]: {summary} ||| " + " ||| ".join(recent_blocks)
        active_run.history = compressed_history
        db.session.commit()
        return compressed_history
    return active_run.history


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """Endpoint Chủ lực: Phân luồng Local Scoring và Streaming LLM"""
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    raw_input = data.get('text', '')
    mode = data.get('mode', 'grammar')

    if not raw_input or not user_id:
        return jsonify({"error": "Dữ liệu không hợp lệ!"}), 400

    safe_input = sanitize_input(raw_input)
    if safe_input is None:
        return jsonify({"error": "Lệnh thao túng hệ thống bị từ chối! Bị trừ 0 điểm!"}), 403

    # 1. ĐOẠT QUYỀN CHẤM ĐIỂM: Xử lý 100% tại Local Brain
    detected_intent = intent_engine.predict(safe_input)
    gec_result = gec_engine.evaluate(safe_input)
    local_score = gec_result['score']
    local_feedback = gec_result['feedback']

    quest_completed_word = check_and_complete_quest(user_id, safe_input)

    def generate_stream():
        """Generator đẩy luồng Server-Sent Events (SSE)"""
        # Bước A: Bắn điểm số về Client NGAY LẬP TỨC để chốt hạ UI
        meta_data = {
            "type": "meta",
            "score": local_score,
            "intent": detected_intent,
            "quest_notification": f"Đặt câu với từ '{quest_completed_word}' (+20 Xu)" if quest_completed_word else None
        }
        yield f"data: {json.dumps(meta_data)}\n\n"

        full_ai_response = ""
        try:
            # Bước B: Xử lý RPG Story
            if mode in ['story', 'story_choose']:
                active_run = ActiveStory.query.filter_by(user_id=user_id).first()
                if not active_run:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Không tìm thấy dữ liệu Active Run!'})}\n\n"
                    return

                history_context = manage_sliding_window(active_run)

                if active_run.turn >= 10:
                    prompt = f"""
                    Bối cảnh: {history_context}. Hành động LƯỢT CUỐI: "{safe_input}". 
                    Điểm ngữ pháp người chơi: {local_score}/10. Lỗi: {local_feedback}
                    Dựa vào điểm này, hãy kết thúc câu chuyện (Sống hoặc Chết). 
                    Trả về định dạng text THUẦN (Không JSON):
                    [EN]: (Truyện tiếng Anh)
                    [VN]: (Truyện tiếng Việt)
                    [STATUS]: Survived hoặc Dead
                    """
                else:
                    prompt = f"""
                    Bối cảnh: {history_context}. Hành động người chơi: "{safe_input}".
                    Điểm ngữ pháp: {local_score}/10. Lỗi: {local_feedback}
                    Kể tiếp truyện dựa vào điểm. Nếu <5, cho nhân vật bị thương/mất đồ.
                    Trả về text THUẦN (Không JSON):
                    [EN]: (Truyện tiếng Anh)
                    [VN]: (Dịch)
                    {'[CHOICES]: Lựa chọn 1 | Lựa chọn 2 | Lựa chọn 3' if mode == 'story_choose' else '[HINT]: (Gợi ý hành động bằng tiếng Anh)'}
                    """

                for chunk in stream_gemini_response(prompt):
                    full_ai_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

                # Ghi lịch sử
                active_run.history += f" ||| [TURN {active_run.turn}] {safe_input} -> {full_ai_response}"
                active_run.turn += 1
                db.session.commit()

                yield f"data: {json.dumps({'type': 'done', 'turn': active_run.turn - 1})}\n\n"

            # Bước C: Xử lý Giao tiếp thông thường (Grammar / Vocab)
            else:
                prompt = f"""
                Học trò nhập: "{safe_input}".
                Hệ thống máy học chấm điểm được: {local_score}/10. Lỗi chi tiết: {local_feedback}
                Bạn là Master G mỏ hỗn, hãy chửi nếu lỗi quá nhiều, khen nếu điểm cao. 
                Giữ nguyên bản chất xéo xắt. Trả về text thường, không JSON.
                """
                for chunk in stream_gemini_response(prompt):
                    full_ai_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Bước D: Hậu xử lý (Lưu Log & Level Up)
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
# CÁC ROUTE PHỤ (Giữ nguyên luồng JSON siêu tốc)
# ==========================================
@ai_bp.route('/story/init', methods=['POST'])
def init_story():
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    topic_id = data.get('topic_id', 1)

    ActiveStory.__table__.create(db.engine, checkfirst=True)
    ActiveStory.query.filter_by(user_id=user_id).delete()

    new_run = ActiveStory(user_id=user_id, topic_id=topic_id, turn=1, history="")
    db.session.add(new_run)
    db.session.commit()

    topic = StoryTopic.query.get(topic_id)
    theme = topic.system_prompt if topic else "Sinh tồn hậu tận thế."

    prompt = f"Bối cảnh: {theme}. Viết cảnh mở màn ngầu (2 câu). Trả về JSON: {{\"scene_en\": \"...\", \"scene_vn\": \"...\", \"hint_en\": \"I need to ___.\", \"hint_vn\": \"...\"}}"
    try:
        res = json.loads(call_gemini_with_retry(prompt, enforce_json=True))
        new_run.history = f"[GM]: {res.get('scene_en', '')}"
        db.session.commit()
        return jsonify(res), 200
    except:
        return jsonify({"scene_en": "System crashed.", "scene_vn": "Hệ thống sập.", "hint_en": "I must ___.",
                        "hint_vn": "..."}), 200


@ai_bp.route('/hint', methods=['POST'])
def get_hint():
    try:
        return jsonify({"hint": call_gemini_with_retry(
            "Cho 1 câu tiếng Anh điền vào chỗ trống dạng 'I usually ___.' KHÔNG dùng markdown.")}), 200
    except:
        return jsonify({"hint": "Hệ thống bận, tự nghĩ đi!"}), 200