from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from app.models.grammar import Grammar
from datetime import datetime, date
import random
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
    vocab_list = Vocabulary.query.all()

    output = []
    for vocab in vocab_list:
        output.append({
            "id": vocab.id,
            "word": vocab.word,
            "meaning": vocab.meaning,
            "image_url": vocab.image_url,
            "is_unlocked": vocab.is_unlocked,
            "is_memorized": getattr(vocab, 'is_memorized', False)
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

# ... (Các đoạn code cũ giữ nguyên) ...

@game_bp.route('/grammars', methods=['GET'])
def get_grammars():
    # Lấy toàn bộ kho ngữ pháp đẩy lên giao diện
    grammar_list = Grammar.query.all()

    output = []
    for g in grammar_list:
        output.append({
            "id": g.id,
            "structure": g.structure,
            "explanation": g.explanation,
            "example": g.example,
            "is_slang": g.is_slang
        })

    return jsonify({"grammars": output}), 200
@game_bp.route('/gacha/roll', methods=['POST'])
def gacha_roll():
    """Bốc ngẫu nhiên một từ vựng đang bị khóa để đưa vào đấu trường"""
    locked_vocab = Vocabulary.query.filter_by(is_unlocked=False).all()

    if not locked_vocab:
        return jsonify({
            "status": "empty",
            "message": "🎉 Tuyệt vời! Bạn đã giải cứu và mở khóa thành công toàn bộ kho từ vựng!"
        }), 200

    # Chọn ngẫu nhiên từ mục tiêu
    target = random.choice(locked_vocab)

    # Bốc thêm 3 từ khác bất kỳ trong DB làm phương án nhiễu (Distractors)
    distractors = Vocabulary.query.filter(Vocabulary.id != target.id).order_by(db.func.rand()).limit(3).all()

    options = [target.meaning] + [d.meaning for d in distractors]
    random.shuffle(options)  # Trộn đều vị trí đáp án

    return jsonify({
        "status": "success",
        "vocab_id": target.id,
        "word": target.word,
        "options": options
    }), 200


@game_bp.route('/gacha/verify', methods=['POST'])
def gacha_verify():
    """Xử lý kết quả thắng/thua thời gian thực"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    vocab_id = data.get('vocab_id')
    user_answer = data.get('answer')
    is_timeout = data.get('timeout', False)

    user = User.query.get(user_id)
    vocab = Vocabulary.query.get(vocab_id)

    if not user or not vocab:
        return jsonify({"error": "Dữ liệu không hợp lệ!"}), 400

    master_g_insults = [
        "Tốc độ phản xạ quá chậm! Bộ não của bạn đóng băng rồi à?",
        "Master G nhìn bạn bằng nửa con mắt. Học hành thế đấy à đồ ngốc!",
        "Chuỗi Streak của bạn đã vỡ vụn như bong bóng xà phòng!",
        "Chọn bừa cũng sai, bạn cần phải rèn luyện thêm nhiều vào!"
    ]

    # Trường hợp hết giờ
    if is_timeout:
        user.streak_count = 0
        db.session.commit()
        return jsonify({
            "correct": False,
            "message": "⏱️ HẾT GIỜ! " + random.choice(master_g_insults),
            "new_streak": 0
        }), 200

    # Trường hợp người dùng chọn đáp án
    if vocab.meaning.strip() == user_answer.strip():
        vocab.is_unlocked = True
        user.streak_count += 1
        db.session.commit()

        return jsonify({
            "correct": True,
            "message": "💥 BOOM! Kích nổ pháo hoa thành công! Bạn đã thu phục từ vựng này!",
            "new_streak": user.streak_count
        }), 200
    else:
        user.streak_count = 0
        db.session.commit()
        return jsonify({
            "correct": False,
            "message": "❌ SAI RỒI! " + random.choice(master_g_insults),
            "new_streak": 0
        }), 200