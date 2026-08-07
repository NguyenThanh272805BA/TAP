import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app import db
from datetime import date

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Cấu hình file upload cho Avatar
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

    # [ VÁ LỖI ]: Cấp Starter Pack (5 từ vựng mẫu đầu tiên) cho User mới để thư viện không bị trống
    starter_vocabs = Vocabulary.query.limit(5).all()
    for v in starter_vocabs:
        uv = UserVocabulary(user_id=new_user.id, vocab_id=v.id, is_unlocked=True)
        db.session.add(uv)
    db.session.commit()

    session['user_id'] = new_user.id
    return jsonify({"message": "Đăng ký thành công!", "user_id": new_user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
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
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập hệ thống!"}), 401

    user = User.query.get(user_id)
    today = date.today()
    is_checked_in = (user.last_checkin == today)

    return jsonify({
        "username": user.username,
        "level": user.current_level,
        "streak": user.streak_count,
        "coins": user.coins,
        "is_checked_in": is_checked_in,
        "role": user.role
    }), 200


# ==========================================
# CÁC ROUTE PHỤC VỤ TRANG PROFILE CÁ NHÂN
# ==========================================

@auth_bp.route('/profile/stats', methods=['GET'])
def get_profile_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)

    # Tính tổng từ vựng ĐÃ THUỘC
    learned_count = UserVocabulary.query.filter_by(user_id=user_id, memorization_level='DA_THUOC').count()

    # Thuật toán tìm Cấp CEFR cao nhất đã chạm tới
    highest_cefr = 'A1'
    cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    # Join bảng để lấy nhãn CEFR của các từ đã thuộc
    learned_vocabs = db.session.query(Vocabulary.cefr_level).join(UserVocabulary).filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.memorization_level == 'DA_THUOC'
    ).all()

    if learned_vocabs:
        levels_achieved = [v[0] for v in learned_vocabs if v[0] in cefr_levels]
        if levels_achieved:
            highest_cefr = sorted(levels_achieved, key=lambda x: cefr_levels.index(x))[-1]

    #Quét danh sách Thành tựu
    user_achs = UserAchievement.query.filter_by(user_id=user_id).order_by(UserAchievement.unlocked_at.desc()).all()
    achievements = []
    for ua in user_achs:
        ach = Achievement.query.get(ua.achievement_id)
        if ach:
            achievements.append({
                "title": ach.title,
                "description": ach.description,
                "icon": ach.icon_url
            })

    return jsonify({
        "username": user.username,
        "avatar": getattr(user, 'avatar', 'default_avatar.png'),
        "bio": getattr(user, 'bio', 'Kẻ lang thang trong thế giới ngôn ngữ...'),
        "level": user.current_level,
        "coins": user.coins,
        "streak": user.streak_count,
        "learned_count": learned_count,
        "highest_cefr": highest_cefr,
        "achievements": achievements
    }), 200


@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)

    # 1. Cập nhật Bio (Châm ngôn)
    bio = request.form.get('bio')
    if bio is not None:
        user.bio = bio

    # 2. Cập nhật Avatar (Tải ảnh lên)
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'avatars')
            os.makedirs(upload_path, exist_ok=True)

            file.save(os.path.join(upload_path, filename))
            user.avatar = filename

    db.session.commit()
    return jsonify(
        {"message": "Hồ sơ đã được đồng bộ lên mạng lưới!", "new_avatar": getattr(user, 'avatar', None)}), 200