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
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    today = date.today()
    is_checked_in = (user.last_checkin == today)

    return jsonify({
        "id": user.id,
        "username": user.username,
        "level": user.current_level,
        "streak": user.streak_count,
        "coins": user.coins,
        "is_checked_in": is_checked_in,
        "role": user.role,
        "avatar": getattr(user, 'avatar', 'default_avatar.png'),
        "equipped_frame": getattr(user, 'equipped_frame', 'frame-default'),
        "equipped_title": getattr(user, 'equipped_title', 'Tân Binh Ngơ Ngác'),
        "target_band": getattr(user, 'target_band', 'B2'),
        "current_band": getattr(user, 'current_band', 'A1')
    }), 200


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    today = date.today()
    is_checked_in = (user.last_checkin == today)

    return jsonify({
        "id": user.id,
        "username": user.username,
        "level": user.current_level,
        "streak": user.streak_count,
        "coins": user.coins,
        "is_checked_in": is_checked_in,
        "role": user.role,
        "avatar": getattr(user, 'avatar', 'default_avatar.png'),
        "equipped_frame": getattr(user, 'equipped_frame', 'frame-default'),
        "equipped_title": getattr(user, 'equipped_title', 'Tân Binh Ngơ Ngác'),
        "target_band": getattr(user, 'target_band', 'B2'),
        "current_band": getattr(user, 'current_band', 'A1')
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
        "achievements": achievements,
        "equipped_frame": getattr(user, 'equipped_frame', 'frame-default'),
        "equipped_title": getattr(user, 'equipped_title', 'Tân Binh Ngơ Ngác'),
        "target_band": getattr(user, 'target_band', 'B2'),
        "current_band": getattr(user, 'current_band', 'A1')
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


# ==========================================
# BIỂU ĐỒ RADAR NĂNG LỰC 6 CHIỀU (COMPETENCY MATRIX)
# ==========================================

def compute_user_competency_radar(user_id):
    """
    Tính toán Ma trận Năng lực 6 Chiều (Hexagonal Competency Matrix) chuẩn sư phạm quốc tế:
    1. Vốn Từ Vựng (Vocabulary): Tỷ lệ từ DA_THUOC nhân trọng số CEFR so với Target Band.
    2. Chuẩn Ngữ Pháp (Grammar): Độ chính xác các quy tắc ngữ pháp và chặng học thuật.
    3. Tốc Độ Phản Xạ (Fluency): Tốc độ xử lý ngôn ngữ trung bình (avg_response_time).
    4. Độ Bền Trí Nhớ (Retention): Khả năng lưu giữ dài hạn theo thuật toán FSRS.
    5. Cú Pháp Câu (Syntax): Năng lực lắp ráp cấu trúc câu phức, câu chẻ & đảo ngữ.
    6. Tính Kiên Trì (Grit): Kỷ luật học tập qua chuỗi Streak và thời gian rèn luyện.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    # 1. VỐN TỪ VỰNG (VOCABULARY - 0-100)
    target_band = getattr(user, 'target_band', 'B2') or 'B2'
    band_benchmarks = {'A1': 20, 'A2': 50, 'B1': 100, 'B2': 200, 'C1': 350, 'C2': 500}
    benchmark_needed = band_benchmarks.get(target_band, 200)

    cefr_weights = {'A1': 1.0, 'A2': 1.2, 'B1': 1.5, 'B2': 2.0, 'C1': 2.5, 'C2': 3.0}
    user_vocabs = db.session.query(Vocabulary.cefr_level, UserVocabulary.memorization_level)\
        .join(UserVocabulary, UserVocabulary.vocab_id == Vocabulary.id)\
        .filter(UserVocabulary.user_id == user_id, UserVocabulary.memorization_level == 'DA_THUOC').all()

    weighted_points = sum(cefr_weights.get(v[0], 1.0) for v in user_vocabs)
    raw_vocab_score = (weighted_points / max(1, benchmark_needed)) * 100.0
    vocab_score = round(max(20.0, min(100.0, raw_vocab_score + (len(user_vocabs) * 1.5))), 1)

    # 2. ĐỘ CHUẨN NGỮ PHÁP (GRAMMAR - 0-100)
    from app.models.user_grammar import UserGrammar
    from app.models.roadmap import UserMilestoneProgress

    user_grammars = UserGrammar.query.filter_by(user_id=user_id).all()
    grammar_score = 35.0
    if user_grammars:
        mastered_g = sum(1 for g in user_grammars if g.mastery_status == 'DA_NAM_VUNG')
        avg_g_score = sum(g.best_score for g in user_grammars) / len(user_grammars)
        grammar_score = (mastered_g / len(user_grammars) * 50.0) + (avg_g_score * 5.0)

    completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user_id, is_completed=True).count()
    grammar_score += min(35.0, completed_milestones * 5.0)
    grammar_score = round(max(25.0, min(100.0, grammar_score)), 1)

    # 3. TỐC ĐỘ PHẢN XẠ (FLUENCY - 0-100)
    avg_times = db.session.query(db.func.avg(UserVocabulary.avg_response_time))\
        .filter(UserVocabulary.user_id == user_id, UserVocabulary.avg_response_time > 0).scalar()

    if avg_times and float(avg_times) > 0:
        fluency_base = max(30.0, min(100.0, 110.0 - (float(avg_times) * 12.0)))
    else:
        fluency_base = 50.0

    arena_stage = getattr(user, 'arena_stage', 1) or 1
    infinity_score = getattr(user, 'infinity_score', 0) or 0
    arena_bonus = min(20.0, (arena_stage * 2.0) + (infinity_score / 50.0))
    fluency_score = round(max(25.0, min(100.0, fluency_base + arena_bonus)), 1)

    # 4. ĐỘ BỀN TRÍ NHỚ (RETENTION - FSRS - 0-100)
    unlocked_uv = UserVocabulary.query.filter_by(user_id=user_id, is_unlocked=True).all()
    if unlocked_uv:
        zero_fails = sum(1 for uv in unlocked_uv if (uv.fail_count or 0) == 0)
        retention_ratio = zero_fails / len(unlocked_uv)
        avg_interval = sum(uv.previous_interval or 0.0 for uv in unlocked_uv) / len(unlocked_uv)
        interval_bonus = min(35.0, (avg_interval / 72.0) * 35.0)
        retention_score = round(max(20.0, min(100.0, (retention_ratio * 65.0) + interval_bonus)), 1)
    else:
        retention_score = 40.0

    # 5. CÚ PHÁP CÂU (SYNTAX - 0-100)
    band_syntax_base = {'A1': 35.0, 'A2': 50.0, 'B1': 68.0, 'B2': 82.0, 'C1': 92.0, 'C2': 98.0}
    current_band = getattr(user, 'current_band', 'A1') or 'A1'
    base_syntax = band_syntax_base.get(current_band, 35.0)

    best_scores = db.session.query(db.func.avg(UserMilestoneProgress.best_score))\
        .filter_by(user_id=user_id).scalar()
    if best_scores and float(best_scores) > 0:
        syntax_score = round(max(25.0, min(100.0, (base_syntax * 0.7) + (float(best_scores) * 3.5))), 1)
    else:
        syntax_score = round(max(25.0, base_syntax), 1)

    # 6. TÍNH KIÊN TRÌ (GRIT - 0-100)
    streak_points = min(50.0, (user.streak_count or 0) * 8.0)
    study_mins = user.study_time_minutes or 0
    time_points = min(50.0, (study_mins / 90.0) * 50.0)
    grit_score = round(max(20.0, min(100.0, streak_points + time_points)), 1)

    dimensions = [
        {
            "key": "vocabulary",
            "name": "Vốn Từ Vựng",
            "english": "Vocabulary",
            "score": vocab_score,
            "desc": f"Độ dày kho từ ({len(user_vocabs)} từ đã thuộc) so với Target Band {target_band}."
        },
        {
            "key": "grammar",
            "name": "Chuẩn Ngữ Pháp",
            "english": "Grammar",
            "score": grammar_score,
            "desc": f"Độ chính xác quy tắc, mệnh đề và mức độ qua ải học thuật."
        },
        {
            "key": "fluency",
            "name": "Tốc Độ Phản Xạ",
            "english": "Fluency",
            "score": fluency_score,
            "desc": f"Tốc độ phản xạ từ vựng và xử lý câu trong tình huống thực tế."
        },
        {
            "key": "retention",
            "name": "Độ Bền Trí Nhớ",
            "english": "Retention",
            "score": retention_score,
            "desc": f"Khả năng duy trì trí nhớ dài hạn theo Spaced Repetition FSRS."
        },
        {
            "key": "syntax",
            "name": "Cú Pháp Câu",
            "english": "Syntax",
            "score": syntax_score,
            "desc": f"Năng lực sắp đặt khối từ, câu phức và câu đảo ngữ theo chuẩn CEFR."
        },
        {
            "key": "grit",
            "name": "Tính Kiên Trì",
            "english": "Grit",
            "score": grit_score,
            "desc": f"Kỷ luật học tập qua chuỗi Streak {user.streak_count} ngày và {study_mins} phút rèn luyện."
        }
    ]

    overall_score = round(sum(d["score"] for d in dimensions) / 6.0, 1)

    if overall_score >= 90:
        overall_grade = "S+"
        grade_title = "Huyền Thoại Ngôn Ngữ"
        grade_color = "var(--neon-pink)"
    elif overall_score >= 80:
        overall_grade = "S"
        grade_title = "Chiến Binh Xuất Sắc"
        grade_color = "var(--neon-cyan)"
    elif overall_score >= 70:
        overall_grade = "A"
        grade_title = "Thành Thạo Tiên Tiến"
        grade_color = "var(--pixel-green)"
    elif overall_score >= 55:
        overall_grade = "B"
        grade_title = "Vững Vàng Căn Bản"
        grade_color = "var(--neon-amber)"
    elif overall_score >= 40:
        overall_grade = "C"
        grade_title = "Đang Rèn Luyện"
        grade_color = "#94a3b8"
    else:
        overall_grade = "D"
        grade_title = "Tân Binh Tiềm Năng"
        grade_color = "#ef4444"

    sorted_dims = sorted(dimensions, key=lambda d: d["score"])
    weakest = sorted_dims[0]
    strongest = sorted_dims[-1]

    advice_map = {
        "vocabulary": f"Kho từ vựng hiện tại ({len(user_vocabs)} từ) cần bổ sung thêm để bắt kịp Target Band {target_band}. Hãy tích cực tham gia Lò Đúc để nạp 10 từ mới mỗi ngày.",
        "grammar": "Độ chuẩn ngữ pháp còn dao động. Hãy ôn lại các chuyên đề thì và cấu trúc câu điều kiện qua các bài Vi Học 30s trước khi thi chặng.",
        "fluency": "Bạn có nền tảng tốt nhưng tốc độ xử lý còn ngập ngừng. Hãy vào Đấu Trường Gacha Arena rèn phản xạ dưới 2.5s/từ.",
        "retention": "Tỷ lệ quên từ sau 48h còn khá cao. Bạn nên tận dụng tính năng Ôn Tập Spaced Repetition vào 'khung giờ vàng' mỗi sáng.",
        "syntax": "Cú pháp câu phức và câu chẻ còn lúng túng. Hãy thực hiện thêm các thử thách Lắp Ráp Cú Pháp trong Lộ Trình để hình thành phản xạ bản ngữ.",
        "grit": f"Tính kỷ luật rèn luyện cần được duy trì đều đặn. Hãy duy trì chuỗi Streak điểm danh và rèn luyện ít nhất 15 phút mỗi ngày."
    }
    pedagogical_advice = advice_map.get(weakest["key"], "Hãy tiếp tục cân bằng và nâng cao toàn diện 6 trục năng lực!")

    return {
        "user_id": user.id,
        "username": user.username,
        "target_band": target_band,
        "current_band": current_band,
        "overall_score": overall_score,
        "overall_grade": overall_grade,
        "grade_title": grade_title,
        "grade_color": grade_color,
        "dimensions": dimensions,
        "strongest": strongest,
        "weakest": weakest,
        "pedagogical_advice": pedagogical_advice
    }


@auth_bp.route('/profile/competency_radar', methods=['GET'])
def get_competency_radar():
    """
    API TRUY XUẤT BIỂU ĐỒ RADAR NĂNG LỰC 6 CHIỀU (HEXAGONAL COMPETENCY RADAR)
    Hỗ trợ cả xem hồ sơ của mình hoặc xem hồ sơ người khác qua query parameter ?user_id=...
    """
    req_user_id = request.args.get('user_id', type=int)
    current_user_id = session.get('user_id')

    target_user_id = req_user_id or current_user_id
    if not target_user_id:
        return jsonify({"error": "Yêu cầu đăng nhập hoặc chỉ định mã người dùng!"}), 401

    radar_data = compute_user_competency_radar(target_user_id)
    if not radar_data:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    return jsonify(radar_data), 200