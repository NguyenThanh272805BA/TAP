from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Tên tài khoản này đã có người sử dụng!"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    # Tự động đăng nhập sau khi đăng ký thành công
    session['user_id'] = new_user.id
    return jsonify({"message": "Đăng ký thành công!", "user_id": new_user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # Lưu user_id vào session bảo mật của Flask
        session['user_id'] = user.id
        return jsonify({
            "message": "Đăng nhập thành công!",
            "user": {
                "username": user.username,
                "level": user.current_level,
                "streak": user.streak_count
            }
        }), 200
    else:
        return jsonify({"error": "Tài khoản hoặc mật khẩu không chính xác!"}), 401

@auth_bp.route('/user/me', methods=['GET'])
def get_current_user_profile():
    # Lấy user_id trực tiếp từ session, không tin tưởng vào id từ frontend gửi lên
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập hệ thống!"}), 401

    user = User.query.get(user_id)
    return jsonify({
        "username": user.username,
        "level": user.current_level,
        "streak": user.streak_count
    }), 200