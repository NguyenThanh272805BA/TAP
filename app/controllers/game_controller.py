from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from datetime import datetime, date

game_bp = Blueprint('game', __name__, url_prefix='/api/game')


@game_bp.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    # Logic giả lập kiểm tra ngày điểm danh gần nhất (Real-time)
    # Trong một app thực tế, ta sẽ so sánh ngày hiện tại với ngày check-in cuối cùng lưu trong DB.
    # Ở đây chúng ta sẽ tăng streak lên 1 và cập nhật trực tiếp để phục vụ kiểm thử logic.
    user.streak_count += 1

    # Cơ chế mở khóa tự động (Gamification):
    # Ví dụ: Cứ đạt thêm 1 chuỗi streak thì hệ thống sẽ tự động mở khóa thêm 2 từ vựng mới trong DB
    words_to_unlock = Vocabulary.query.filter_by(is_unlocked=False).limit(2).all()
    unlocked_words_list = []

    for word in words_to_unlock:
        word.is_unlocked = True
        unlocked_words_list.append(word.word)

    db.session.commit()

    return jsonify({
        "message": "Điểm danh thời gian thực thành công!",
        "current_streak": user.streak_count,
        "new_words_unlocked": unlocked_words_list
    }), 200


@game_bp.route('/vocabularies', methods=['GET'])
def get_vocabularies():
    # Lấy toàn bộ kho từ vựng từ database để đẩy lên giao diện Bento Grid
    vocab_list = Vocabulary.query.all()

    output = []
    for vocab in vocab_list:
        output.append({
            "id": vocab.id,
            "word": vocab.word,
            "meaning": vocab.meaning,
            "image_url": vocab.image_url,
            "is_unlocked": vocab.is_unlocked
        })

    return jsonify({"vocabularies": output}), 200