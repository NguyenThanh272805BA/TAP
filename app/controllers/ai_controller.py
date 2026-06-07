from flask import Blueprint, request, jsonify
from app.utils.gemini_helper import evaluate_english_skill
from app.models.test import TestLog
from app import db
import json

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    user_id = data.get('user_id')
    user_input = data.get('text')

    # Ở bản hoàn thiện, ta có thể query DB để lấy ra 1 cấu trúc ngữ pháp ngẫu nhiên
    # trong bảng 'grammars' để ép người dùng phải xài. Tạm thời hardcode để test.
    target_grammar = "S + wish + S + V(past) (Câu điều ước ở hiện tại)"

    if not user_input or not user_id:
        return jsonify({"error": "Thiếu dữ liệu đầu vào!"}), 400

    # Gọi AI
    ai_response_str = evaluate_english_skill(user_input, target_grammar)

    try:
        # Ép kiểu chuỗi text thành Object JSON
        result = json.loads(ai_response_str)
    except Exception as e:
        return jsonify({"error": "AI trả về dữ liệu không đúng chuẩn JSON", "raw_data": ai_response_str}), 500

    # Lưu kết quả chấm điểm vào Database
    new_log = TestLog(
        user_id=user_id,
        score=result.get("score", 0),
        ai_feedback=result.get("feedback", "")
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        "message": "Đã chấm điểm xong!",
        "result": result
    }), 200