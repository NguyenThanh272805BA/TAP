# app/controllers/ai_controller.py
from flask import Blueprint, request, jsonify
from app.utils.gemini_helper import evaluate_english_skill
from app.models.test import TestLog
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app import db
import json
import random

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_input = data.get('text')
    mode = data.get('mode', 'grammar')  # Nhận mode từ Frontend (vocab, grammar, story, game)

    if not user_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào!"}), 400

    # THAY ĐỔI BỐI CẢNH DỰA TRÊN DYNAMIC MODE
    context_challenge = ""

    try:
        if mode == 'grammar':
            # Bốc ngẫu nhiên một cấu trúc ngữ pháp từ MySQL để ép người dùng làm bài
            grammar_list = Grammar.query.all()
            if grammar_list:
                chosen = random.choice(grammar_list)
                context_challenge = f"Cấu trúc bắt buộc: {chosen.structure} ({chosen.explanation}). Ví dụ mẫu: {chosen.example}"
            else:
                context_challenge = "Cấu trúc bắt buộc: S + wish + S + V(past) (Câu điều ước ở hiện tại)"

        elif mode == 'vocab':
            # Bốc ngẫu nhiên từ vựng đã mở khóa để kiểm tra
            vocab_list = Vocabulary.query.filter_by(is_unlocked=True).all()
            if vocab_list:
                chosen = random.choice(vocab_list)
                context_challenge = f"Từ vựng/Từ lóng bắt buộc phải dùng: '{chosen.word}' nghĩa là ({chosen.meaning})"
            else:
                context_challenge = "Từ vựng bắt buộc phải dùng: 'Annihilate' (Tiêu diệt hoàn toàn)"

        elif mode == 'story':
            context_challenge = "Ngữ cảnh nhập vai RPG: Người dùng đang đối thoại với một NPC hấp hối trong không gian hoang dã để hỏi đường hoặc cứu giúp. Đánh giá tính hợp lý và ngữ pháp của lời thoại."

        elif mode == 'game':
            context_challenge = "Đấu trường phản xạ nhanh Gacha: Kiểm tra câu trả lời ngắn giải đố từ vựng."

        # Gọi "não bộ" Gemini 2.5 Flash chấm điểm
        ai_response_str = evaluate_english_skill(user_input, context_challenge)
        result = json.loads(ai_response_str)

    except Exception as e:
        # Cơ chế dự phòng nếu DB trống hoặc JSON lỗi
        result = {
            "score": 4.0,
            "feedback": f"Hệ thống lõi gặp xung đột dữ liệu rồi! Bản thiết lập lỗi: {str(e)}"
        }

    # Lưu vết kết quả vào Database MySQL để lưu giữ chiến tích
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