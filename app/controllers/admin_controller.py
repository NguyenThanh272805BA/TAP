import os
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, session, request, current_app
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.story_topic import StoryTopic
from app.models.grammar import Grammar
from app.models.test import TestLog
from app.models.user_vocabulary import UserVocabulary
from app.models.user_grammar import UserGrammar
from app.models.user_achievement import UserAchievement
from app.models.cosmetic import UserCosmetic
from app.models.roadmap import UserMilestoneProgress
from app.models.story_session import StorySession
from app.models.daily_quest import DailyQuest
from app.models.notification import Notification
from app import db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Cấu hình thư mục upload ảnh bìa (Sẽ tự động tạo nếu chưa tồn tại)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# MIDDLEWARE: Bảo vệ API, chỉ cho phép Admin truy cập
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({"error": "[ SECURITY BREACH ] Bạn không có quyền truy cập khu vực này!"}), 403

        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    users_count = User.query.count()
    vocab_count = Vocabulary.query.count()
    grammar_count = Grammar.query.count()
    tests_count = TestLog.query.count()

    return jsonify({
        "users": users_count,
        "vocab": vocab_count,
        "grammar": grammar_count,
        "tests": tests_count
    }), 200


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "level": u.current_level,
        "role": u.role,
        "coins": u.coins,
        "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A"
    } for u in users]), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        return jsonify({"error": "Lỗi: Không thể tự xóa tài khoản của chính mình!"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn player {user.username} khỏi máy chủ!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ CHỦ ĐỀ TEXT-RPG
# ==========================================
@admin_bp.route('/topics', methods=['GET'])
@admin_required
def get_topics():
    topics = StoryTopic.query.all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "genre": t.genre,
        "cover_image": t.cover_image,
        "system_prompt": t.system_prompt,
        "play_mode": getattr(t, 'play_mode', 'both')
    } for t in topics]), 200


@admin_bp.route('/topics', methods=['POST'])
@admin_required
def create_topic():
    title = request.form.get('title')
    genre = request.form.get('genre')
    system_prompt = request.form.get('system_prompt')
    play_mode = request.form.get('play_mode', 'both') # Phase 3: Đọc play_mode

    if not title or not system_prompt:
        return jsonify({"error": "Thiếu thông tin bắt buộc!"}), 400

    filename = 'default_cover.jpg'
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers')

            os.makedirs(upload_path, exist_ok=True)

            # Lưu file
            file.save(os.path.join(upload_path, filename))

    # Phase 3: Gắn thêm trường play_mode
    new_topic = StoryTopic(title=title, genre=genre, cover_image=filename, system_prompt=system_prompt, play_mode=play_mode)
    db.session.add(new_topic)
    db.session.commit()
    return jsonify({"message": "Đã ghi nhận Chủ đề Truyện mới vào Hệ thống Lõi!"}), 201


@admin_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@admin_required
def delete_topic(topic_id):
    topic = StoryTopic.query.get(topic_id)
    if not topic:
        return jsonify({"error": "Không tìm thấy chủ đề này!"}), 404
    if topic.cover_image and topic.cover_image != 'default_cover.jpg':
        base_dir = os.path.abspath(os.path.dirname(__file__))
        cover_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers', topic.cover_image)
        if os.path.exists(cover_path):
            try:
                os.remove(cover_path)
            except:
                pass

    # Xóa các StorySession thuộc topic này trước khi xóa topic
    StorySession.query.filter_by(topic_id=topic_id).delete()

    db.session.delete(topic)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn chủ đề '{topic.title}' khỏi hệ thống!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ TỪ VỰNG (VOCABULARY)
# ==========================================
@admin_bp.route('/vocabulary', methods=['GET'])
@admin_required
def get_vocabularies():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search = request.args.get('search', '', type=str).strip()
    level = request.args.get('level', '', type=str).strip().upper()

    query = Vocabulary.query
    if search:
        query = query.filter(
            (Vocabulary.word.ilike(f'%{search}%')) |
            (Vocabulary.meaning.ilike(f'%{search}%')) |
            (Vocabulary.theme.ilike(f'%{search}%'))
        )
    if level and level != 'ALL':
        query = query.filter(Vocabulary.cefr_level == level)

    total = query.count()
    items = query.order_by(Vocabulary.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
        "vocabularies": [{
            "id": v.id,
            "word": v.word,
            "meaning": v.meaning,
            "theme": v.theme or 'General',
            "cefr_level": v.cefr_level or 'A1',
            "is_unlocked": bool(v.is_unlocked),
            "is_memorized": bool(v.is_memorized)
        } for v in items]
    }), 200


@admin_bp.route('/vocabulary', methods=['POST'])
@admin_required
def create_vocabulary():
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    meaning = data.get('meaning', '').strip()
    theme = data.get('theme', 'General').strip() or 'General'
    cefr_level = data.get('cefr_level', 'A1').strip().upper() or 'A1'

    if not word or not meaning:
        return jsonify({"error": "Vui lòng nhập đầy đủ từ vựng và nghĩa!"}), 400

    existing = Vocabulary.query.filter_by(word=word).first()
    if existing:
        return jsonify({"error": f"Từ '{word}' đã tồn tại trong từ điển!"}), 400

    new_vocab = Vocabulary(word=word, meaning=meaning, theme=theme, cefr_level=cefr_level)
    db.session.add(new_vocab)
    db.session.commit()
    return jsonify({"message": f"Đã thêm thành công từ vựng '{word}'!", "id": new_vocab.id}), 201


@admin_bp.route('/vocabulary/<int:vocab_id>', methods=['DELETE'])
@admin_required
def delete_vocabulary(vocab_id):
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Không tìm thấy từ vựng này!"}), 404

    # Xóa liên kết trong UserVocabulary và DailyQuest nếu có
    UserVocabulary.query.filter_by(vocab_id=vocab_id).delete()
    DailyQuest.query.filter_by(vocab_id=vocab_id).delete()
    db.session.delete(vocab)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn từ vựng '{vocab.word}' khỏi từ điển!"}), 200


# ==========================================
# CÁC ROUTE TIẾN ĐỘ VÀ RESET DỮ LIỆU
# ==========================================
@admin_bp.route('/users/<int:user_id>/reset', methods=['POST'])
@admin_required
def reset_user_progress(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    try:
        UserVocabulary.query.filter_by(user_id=user_id).delete()
        UserGrammar.query.filter_by(user_id=user_id).delete()
        UserAchievement.query.filter_by(user_id=user_id).delete()
        UserCosmetic.query.filter_by(user_id=user_id).delete()
        UserMilestoneProgress.query.filter_by(user_id=user_id).delete()
        TestLog.query.filter_by(user_id=user_id).delete()
        DailyQuest.query.filter_by(user_id=user_id).delete()
        Notification.query.filter_by(user_id=user_id).delete()
        StorySession.query.filter_by(user_id=user_id).delete()

        user.coins = 0
        user.streak_count = 0
        user.current_level = 'Tân Binh Ngơ Ngác'
        user.current_band = 'A1'
        user.arena_stage = 1
        user.infinity_score = 0
        user.last_checkin = None
        user.last_quest_date = None
        user.equipped_frame = 'frame-default'
        user.equipped_title = 'Tân Binh Ngơ Ngác'

        db.session.commit()
        return jsonify({"message": f"Đã reset toàn bộ tiến độ của @{user.username} về mặc định!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi khi reset tiến độ: {str(e)}"}), 500


@admin_bp.route('/reset-data', methods=['DELETE'])
@admin_required
def reset_all_data():
    data = request.get_json() or {}
    confirm_code = data.get('confirm_code', '').strip()

    if confirm_code != "XAC_NHAN_XOA_TOAN_BO":
        return jsonify({"error": "Mã xác nhận không chính xác! Vui lòng nhập đúng 'XAC_NHAN_XOA_TOAN_BO'."}), 400

    try:
        deleted = {}
        deleted["StorySession"] = StorySession.query.delete()
        deleted["UserVocabulary"] = UserVocabulary.query.delete()
        deleted["UserGrammar"] = UserGrammar.query.delete()
        deleted["UserAchievement"] = UserAchievement.query.delete()
        deleted["UserCosmetic"] = UserCosmetic.query.delete()
        deleted["UserMilestoneProgress"] = UserMilestoneProgress.query.delete()
        deleted["TestLog"] = TestLog.query.delete()
        deleted["DailyQuest"] = DailyQuest.query.delete()
        deleted["Notification"] = Notification.query.delete()

        # Xóa tất cả user không phải admin
        non_admins = User.query.filter(User.role != 'admin').all()
        deleted["User (non-admin)"] = len(non_admins)
        for u in non_admins:
            db.session.delete(u)

        db.session.commit()
        admins = User.query.filter_by(role='admin').all()
        return jsonify({
            "message": "Dọn dẹp dữ liệu hoàn tất! Toàn bộ tiến độ và tài khoản người dùng thường đã bị xóa.",
            "deleted_stats": deleted,
            "admins_retained": [a.username for a in admins]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi khi dọn dẹp hệ thống: {str(e)}"}), 500