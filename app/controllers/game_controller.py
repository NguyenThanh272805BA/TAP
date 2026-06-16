from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from app.models.user_vocabulary import UserVocabulary
from app.models.grammar import Grammar
from datetime import datetime, date
import random

game_bp = Blueprint('game', __name__, url_prefix='/api/game')


@game_bp.route('/checkin', methods=['POST'])
def checkin():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập hệ thống!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    # Tăng chuỗi điểm danh thực tế
    user.streak_count += 1

    # Cơ chế mở khóa tự động cá nhân hóa (Gamification)
    # Tìm các từ vựng chưa được người dùng này mở khóa (Chưa có bản ghi hoặc is_unlocked = False)
    unlocked_subquery = db.session.query(UserVocabulary.vocab_id).filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.is_unlocked == True
    )
    words_to_unlock = Vocabulary.query.filter(~Vocabulary.id.in_(unlocked_subquery)).limit(2).all()
    unlocked_words_list = []

    for word in words_to_unlock:
        uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=word.id).first()
        if not uv:
            uv = UserVocabulary(user_id=user_id, vocab_id=word.id, is_unlocked=True, memorization_level='CHUA_THUOC')
            db.session.add(uv)
        else:
            uv.is_unlocked = True
        unlocked_words_list.append(word.word)

    db.session.commit()

    return jsonify({
        "message": "Điểm danh thời gian thực thành công!",
        "current_streak": user.streak_count,
        "new_words_unlocked": unlocked_words_list
    }), 200


@game_bp.route('/vocabularies', methods=['GET'])
def get_vocabularies():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    # Sử dụng .outerjoin chuẩn của SQLAlchemy để lấy thông tin cá nhân hóa
    results = db.session.query(
        Vocabulary.id,
        Vocabulary.word,
        Vocabulary.meaning,
        Vocabulary.image_url,
        Vocabulary.theme,
        UserVocabulary.is_unlocked,
        UserVocabulary.memorization_level
    ).outerjoin(
        UserVocabulary,
        (Vocabulary.id == UserVocabulary.vocab_id) & (UserVocabulary.user_id == user_id)
    ).all()

    output = []
    for r in results:
        output.append({
            "id": r.id,
            "word": r.word,
            "meaning": r.meaning,
            "image_url": r.image_url,
            "theme": r.theme,
            "is_unlocked": r.is_unlocked if r.is_unlocked is not None else False,
            "is_memorized": True if r.memorization_level == 'DA_THUOC' else False
        })

    return jsonify({"vocabularies": output}), 200


@game_bp.route('/vocab/toggle_memorize', methods=['POST'])
def toggle_memorize():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    user_id = session.get('user_id')  # Lấy từ session bảo mật

    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    vocab = Vocabulary.query.get(vocab_id)
    user = User.query.get(user_id)

    if not vocab or not user:
        return jsonify({"error": "Không tìm thấy dữ liệu tương ứng!"}), 404

    # Đổi trạng thái trong bảng nối cá nhân UserVocabulary
    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
    if not uv:
        uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True, memorization_level='DA_THUOC')
        db.session.add(uv)
        is_memorized_now = True
    else:
        if uv.memorization_level == 'DA_THUOC':
            uv.memorization_level = 'CHUA_THUOC'
            is_memorized_now = False
        else:
            uv.memorization_level = 'DA_THUOC'
            is_memorized_now = True

    db.session.commit()

    # LOGIC GAMIFICATION: Tính toán mức độ hoàn thành chủ đề của RIÊNG user này
    current_theme = vocab.theme
    total_words_in_theme = Vocabulary.query.filter_by(theme=current_theme).count()

    memorized_words_in_theme = db.session.query(UserVocabulary).join(
        Vocabulary, Vocabulary.id == UserVocabulary.vocab_id
    ).filter(
        UserVocabulary.user_id == user_id,
        Vocabulary.theme == current_theme,
        UserVocabulary.memorization_level == 'DA_THUOC'
    ).count()

    level_upgraded = False
    if total_words_in_theme > 0 and total_words_in_theme == memorized_words_in_theme:
        if user.current_level == 'Beginner':
            user.current_level = 'Intermediate Explorer'
        elif user.current_level == 'Intermediate Explorer':
            user.current_level = 'Advanced Conqueror'

        level_upgraded = True
        db.session.commit()

    return jsonify({
        "message": "Cập nhật chiến tích từ vựng thành công!",
        "is_memorized": is_memorized_now,
        "theme_progress": f"{memorized_words_in_theme}/{total_words_in_theme}",
        "level_upgraded": level_upgraded,
        "current_level": user.current_level
    }), 200


@game_bp.route('/grammars', methods=['GET'])
def get_grammars():
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
    """Bốc ngẫu nhiên một từ vựng đang bị khóa đối với user này để đưa vào đấu trường"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    # Lọc ra các từ mà user này CHƯA mở khóa
    unlocked_subquery = db.session.query(UserVocabulary.vocab_id).filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.is_unlocked == True
    )
    locked_vocab = Vocabulary.query.filter(~Vocabulary.id.in_(unlocked_subquery)).all()

    if not locked_vocab:
        return jsonify({
            "status": "empty",
            "message": "[ SYSTEM ] Tuyệt vời! Bạn đã giải cứu và mở khóa thành công toàn bộ kho từ vựng cá nhân!"
        }), 200

    target = random.choice(locked_vocab)

    # Bốc thêm 3 từ khác bất kỳ làm phương án nhiễu
    distractors = Vocabulary.query.filter(Vocabulary.id != target.id).order_by(db.func.rand()).limit(3).all()

    options = [target.meaning] + [d.meaning for d in distractors]
    random.shuffle(options)

    return jsonify({
        "status": "success",
        "vocab_id": target.id,
        "word": target.word,
        "options": options
    }), 200


@game_bp.route('/gacha/verify', methods=['POST'])
def gacha_verify():
    """Xử lý kết quả thắng/thua thời gian thực dựa vào session"""
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    user_answer = data.get('answer')
    is_timeout = data.get('timeout', False)
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Phiên làm việc hết hạn!"}), 401

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

    if is_timeout:
        user.streak_count = 0
        db.session.commit()
        return jsonify({
            "correct": False,
            "message": "[ TIMEOUT ] HẾT GIỜ! " + random.choice(master_g_insults),
            "new_streak": 0
        }), 200

    if vocab.meaning.strip() == user_answer.strip():
        # Mở khóa từ vựng ĐỘC LẬP cho user trong bảng nối
        uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
        if not uv:
            uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True, memorization_level='CHUA_THUOC')
            db.session.add(uv)
        else:
            uv.is_unlocked = True

        user.streak_count += 1
        db.session.commit()

        return jsonify({
            "correct": True,
            "message": "[ KABOOM ] Kích nổ pháo hoa thành công! Bạn đã thu phục từ vựng này!",
            "new_streak": user.streak_count
        }), 200
    else:
        user.streak_count = 0
        db.session.commit()
        return jsonify({
            "correct": False,
            "message": "[ ERROR ] SAI RỒI! " + random.choice(master_g_insults),
            "new_streak": 0
        }), 200


@game_bp.route('/exam/generate', methods=['POST'])
def generate_exam():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập hệ thống!"}), 401

    needs_review = UserVocabulary.query.filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.memorization_level.in_(['CHUA_THUOC', 'HOI_THUOC'])
    ).all()

    review_vocab_ids = [uv.vocab_id for uv in needs_review]

    limit = 50
    exam_words = []

    if review_vocab_ids:
        review_vocabs = Vocabulary.query.filter(Vocabulary.id.in_(review_vocab_ids)).limit(limit).all()
        exam_words.extend(review_vocabs)

    if len(exam_words) < limit:
        needed = limit - len(exam_words)

        subquery = db.session.query(UserVocabulary.vocab_id).filter_by(user_id=user_id)
        new_vocabs = Vocabulary.query.filter(~Vocabulary.id.in_(subquery)).limit(needed).all()

        for nv in new_vocabs:
            new_uv = UserVocabulary(user_id=user_id, vocab_id=nv.id, is_unlocked=True, memorization_level='CHUA_THUOC')
            db.session.add(new_uv)
            exam_words.append(nv)
        db.session.commit()

    output = [{"id": w.id, "word": w.word, "meaning": w.meaning} for w in exam_words]
    random.shuffle(output)

    return jsonify({"exam": output, "count": len(output)}), 200


@game_bp.route('/exam/update_status', methods=['POST'])
def update_exam_status():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    level = data.get('level')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Hết phiên đăng nhập!"}), 401

    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
    if uv:
        uv.memorization_level = level
        db.session.commit()
        return jsonify({"success": True}), 200

    return jsonify({"error": "Không tìm thấy dữ liệu!"}), 400