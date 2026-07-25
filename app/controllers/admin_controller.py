import os
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, session, request, current_app
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.story_topic import StoryTopic
from app.models.grammar import Grammar
from app.models.test import TestLog
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
# CÁC ROUTE QUẢN LÝ CHỦ ĐỀ TEXT-RPG (PHASE 2)
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
        "system_prompt": t.system_prompt
    } for t in topics]), 200


@admin_bp.route('/topics', methods=['POST'])
@admin_required
def create_topic():
    title = request.form.get('title')
    genre = request.form.get('genre')
    system_prompt = request.form.get('system_prompt')

    if not title or not system_prompt:
        return jsonify({"error": "Thiếu thông tin bắt buộc!"}), 400

    filename = 'default_cover.jpg'
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Khởi tạo đường dẫn tuyệt đối an toàn trỏ về thư mục views/static/uploads/covers
            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers')

            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(upload_path, exist_ok=True)

            # Lưu file
            file.save(os.path.join(upload_path, filename))

    new_topic = StoryTopic(title=title, genre=genre, cover_image=filename, system_prompt=system_prompt)
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

    db.session.delete(topic)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn chủ đề '{topic.title}' khỏi hệ thống!"}), 200