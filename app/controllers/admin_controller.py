from flask import Blueprint, jsonify, session
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.models.test import TestLog
from app import db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


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