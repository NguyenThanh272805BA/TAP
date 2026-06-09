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
@game_bp.route('/vocab/toggle_memorize', methods=['POST'])
def toggle_memorize():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    user_id = data.get('user_id')

    vocab = Vocabulary.query.get(vocab_id)
    user = User.query.get(user_id)

    if not vocab or not user:
        return jsonify({"error": "Không tìm thấy dữ liệu mẫu!"}), 404

    # Đổi trạng thái tích dấu X (Nhớ / Quên từ)
    vocab.is_memorized = not vocab.is_memorized
    db.session.commit()

    # LOGIC GAMIFICATION: Kiểm tra xem đã hoàn thành 100% chủ đề này chưa
    current_theme = vocab.theme
    total_words_in_theme = Vocabulary.query.filter_by(theme=current_theme).count()
    memorized_words_in_theme = Vocabulary.query.filter_by(theme=current_theme, is_memorized=True).count()

    level_upgraded = False
    if total_words_in_theme > 0 and total_words_in_theme == memorized_words_in_theme:
        # Nếu nhớ hết từ trong chủ đề -> Thăng cấp Level cho người chơi
        if user.current_level == 'Beginner':
            user.current_level = 'Intermediate Explorer'
        elif user.current_level == 'Intermediate Explorer':
            user.current_level = 'Advanced Conqueror'

        level_upgraded = True
        db.session.commit()

    return jsonify({
        "message": "Cập nhật chiến tích từ vựng thành công!",
        "is_memorized": vocab.is_memorized,
        "theme_progress": f"{memorized_words_in_theme}/{total_words_in_theme}",
        "level_upgraded": level_upgraded,
        "current_level": user.current_level
    }), 200