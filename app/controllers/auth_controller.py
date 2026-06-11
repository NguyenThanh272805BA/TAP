from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

# Khởi tạo Blueprint cho Auth
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"}), 400

    # Kiểm tra xem user đã tồn tại chưa
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Tên tài khoản này đã có người sử dụng!"}), 409

    # Mã hóa mật khẩu và lưu vào DB
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Đăng ký tài khoản thành công!", "user_id": new_user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Tìm user trong DB
    user = User.query.filter_by(username=username).first()

    # Kiểm tra user có tồn tại và mật khẩu đã hash có khớp không
    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            "message": "Đăng nhập thành công!",
            "user": {
                "id": user.id,
                "username": user.username,
                "level": user.current_level,
                "streak": user.streak_count
            }
        }), 200
    else:
        return jsonify({"error": "Tài khoản hoặc mật khẩu không chính xác!"}), 401

@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người chơi!"}), 404

    return jsonify({
        "username": user.username,
        "level": user.current_level,
        "streak": user.streak_count
    }), 200