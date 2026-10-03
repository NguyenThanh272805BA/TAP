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
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

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
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

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
    5. Cú Pháp Câu (Syntax): Năng lực lắp ráp cấu trúc câu qua bài thi và chặng thử thách.
    6. Tính Kiên Trì (Grit): Kỷ luật học tập qua chuỗi Streak và thời gian rèn luyện.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    from app.models.user_grammar import UserGrammar
    from app.models.roadmap import UserMilestoneProgress
    from app.models.test import TestLog

    target_band = getattr(user, 'target_band', 'B2') or 'B2'
    current_band = getattr(user, 'current_band', 'A1') or 'A1'
    band_benchmarks = {'A1': 20, 'A2': 50, 'B1': 100, 'B2': 200, 'C1': 350, 'C2': 500}
    benchmark_needed = band_benchmarks.get(target_band, 200)
    cefr_weights = {'A1': 1.0, 'A2': 1.2, 'B1': 1.5, 'B2': 2.0, 'C1': 2.5, 'C2': 3.0}

    # 1. Quét dữ liệu học thuật thực tế
    user_vocabs = db.session.query(Vocabulary.cefr_level, UserVocabulary.memorization_level)\
        .join(UserVocabulary, UserVocabulary.vocab_id == Vocabulary.id)\
        .filter(UserVocabulary.user_id == user_id, UserVocabulary.memorization_level == 'DA_THUOC').all()

    unlocked_uv = UserVocabulary.query.filter_by(user_id=user_id, is_unlocked=True).all()
    # Lọc những từ thực sự có tương tác/học tập (loại bỏ starter pack chưa đụng đến)
    tested_uv = [
        uv for uv in unlocked_uv
        if (uv.memorization_level and uv.memorization_level != 'CHUA_THUOC')
        or ((uv.fail_count or 0) > 0)
        or ((uv.avg_response_time or 0) > 0)
        or ((uv.previous_interval or 0) > 0)
    ]

    user_grammars = UserGrammar.query.filter_by(user_id=user_id).all()
    completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user_id, is_completed=True).count()
    test_logs_count = TestLog.query.filter_by(user_id=user_id).count()
    study_mins = getattr(user, 'study_time_minutes', 0) or 0
    streak_count = getattr(user, 'streak_count', 0) or 0
    arena_stage = getattr(user, 'arena_stage', 1) or 1
    infinity_score = getattr(user, 'infinity_score', 0) or 0

    avg_times = db.session.query(db.func.avg(UserVocabulary.avg_response_time))\
        .filter(UserVocabulary.user_id == user_id, UserVocabulary.avg_response_time > 0).scalar()

    # Kiểm tra xem người dùng đã có bất kỳ hành vi học tập nào chưa
    has_learning_activity = (
        len(user_vocabs) > 0 or
        len(tested_uv) > 0 or
        len(user_grammars) > 0 or
        completed_milestones > 0 or
        test_logs_count > 0 or
        study_mins > 0 or
        streak_count > 0 or
        infinity_score > 0 or
        arena_stage > 1 or
        (avg_times and float(avg_times) > 0)
    )

    if not has_learning_activity:
        # TRẠNG THÁI EMPTY STATE: TÀI KHOẢN MỚI CHƯA CÓ HOẠT ĐỘNG
        dimensions = [
            {
                "key": "vocabulary",
                "name": "Vốn Từ Vựng",
                "english": "Vocabulary",
                "score": 0.0,
                "desc": f"Chưa học từ vựng nào. Hãy vào Lò Đúc để tích lũy {benchmark_needed} từ chuẩn Band {target_band}."
            },
            {
                "key": "grammar",
                "name": "Chuẩn Ngữ Pháp",
                "english": "Grammar",
                "score": 0.0,
                "desc": "Chưa có dữ liệu làm bài ngữ pháp. Hãy hoàn thành các chặng thử thách trong Lộ Trình."
            },
            {
                "key": "fluency",
                "name": "Tốc Độ Phản Xạ",
                "english": "Fluency",
                "score": 0.0,
                "desc": "Chưa ghi nhận thời gian phản xạ thực tế. Hãy thử sức trong Đấu Trường Arena hoặc Luyện Nói."
            },
            {
                "key": "retention",
                "name": "Độ Bền Trí Nhớ",
                "english": "Retention",
                "score": 0.0,
                "desc": "Chưa kích hoạt thuật toán FSRS. Cần lưu giữ và ôn tập ít nhất 1 từ theo chu kỳ Spaced Repetition."
            },
            {
                "key": "syntax",
                "name": "Cú Pháp Câu",
                "english": "Syntax",
                "score": 0.0,
                "desc": "Chưa làm bài kiểm tra cấu trúc câu. Hãy thi Placement Test hoặc thực hành lắp ráp câu."
            },
            {
                "key": "grit",
                "name": "Tính Kiên Trì",
                "english": "Grit",
                "score": 0.0,
                "desc": "Chuỗi Streak 0 ngày & 0 phút học tập. Hãy duy trì thói quen học mỗi ngày."
            }
        ]

        return {
            "user_id": user.id,
            "username": user.username,
            "target_band": target_band,
            "current_band": current_band,
            "has_data": False,
            "is_unranked": True,
            "overall_score": 0.0,
            "overall_grade": "N/A",
            "grade_title": "Chưa Khảo Thí",
            "grade_color": "#94a3b8",
            "dimensions": dimensions,
            "strongest": {"key": "none", "name": "Chưa xác định", "score": 0.0},
            "weakest": {"key": "none", "name": "Chưa xác định", "score": 0.0},
            "pedagogical_advice": "Chào mừng tân binh! Hãy hoàn thành Bài Khảo Thí Đầu Vào (Placement Test) để hệ thống đo lường và kích hoạt Ma Trận Năng Lực 6 Chiều của bạn."
        }

    # NẾU ĐÃ CÓ DỮ LIỆU HOẠT ĐỘNG THẬT -> TÍNH TOÁN MINH BẠCH, KHÔNG GÁN ĐIỂM SÀN ẢO

    # 1. VỐN TỪ VỰNG (VOCABULARY - 0-100)
    weighted_points = sum(cefr_weights.get(v[0], 1.0) for v in user_vocabs)
    raw_vocab_score = (weighted_points / max(1, benchmark_needed)) * 100.0
    vocab_score = round(min(100.0, raw_vocab_score), 1)

    # 2. ĐỘ CHUẨN NGỮ PHÁP (GRAMMAR - 0-100)
    grammar_score = 0.0
    if user_grammars:
        mastered_g = sum(1 for g in user_grammars if g.mastery_status == 'DA_NAM_VUNG')
        avg_g_score = sum(g.best_score for g in user_grammars) / len(user_grammars)
        grammar_score = (mastered_g / len(user_grammars) * 55.0) + (avg_g_score * 4.5)

    if completed_milestones > 0:
        grammar_score += min(35.0, completed_milestones * 5.0)

    grammar_score = round(min(100.0, grammar_score), 1)

    # 3. TỐC ĐỘ PHẢN XẠ (FLUENCY - 0-100)
    fluency_score = 0.0
    if avg_times and float(avg_times) > 0:
        avg_sec = float(avg_times)
        fluency_base = max(15.0, min(100.0, 115.0 - (avg_sec * 15.0)))
        arena_bonus = min(15.0, (max(0, arena_stage - 1) * 2.0) + (infinity_score / 100.0))
        fluency_score = round(min(100.0, fluency_base + arena_bonus), 1)
        fluency_desc = f"Tốc độ phản xạ thực tế {round(avg_sec, 2)}s/từ (Ải Đấu Trường: {arena_stage})."
    elif arena_stage > 1 or infinity_score > 0:
        fluency_score = round(min(60.0, ((arena_stage - 1) * 6.0) + (infinity_score / 50.0)), 1)
        fluency_desc = f"Ghi nhận từ Đấu Trường (Ải {arena_stage}, Kỷ lục Vô cực: {infinity_score}đ)."
    else:
        fluency_desc = "Chưa ghi nhận thời gian phản xạ câu hỏi thực tế."

    # 4. ĐỘ BỀN TRÍ NHỚ (RETENTION - FSRS - 0-100)
    if tested_uv:
        zero_fails = sum(1 for uv in tested_uv if (uv.fail_count or 0) == 0)
        retention_ratio = zero_fails / len(tested_uv)
        avg_interval = sum(uv.previous_interval or 0.0 for uv in tested_uv) / len(tested_uv)
        interval_bonus = min(35.0, (avg_interval / 72.0) * 35.0)
        retention_score = round(min(100.0, (retention_ratio * 65.0) + interval_bonus), 1)
        retention_desc = f"Độ bền trí nhớ FSRS: {round(retention_ratio * 100, 1)}% ghi nhớ tốt trên {len(tested_uv)} từ đã luyện."
    else:
        retention_score = 0.0
        retention_desc = "Chưa có từ vựng nào trong chu kỳ Spaced Repetition."

    # 5. CÚ PHÁP CÂU (SYNTAX - 0-100)
    latest_test = TestLog.query.filter_by(user_id=user_id).order_by(TestLog.created_at.desc()).first()
    best_milestone_scores = db.session.query(db.func.avg(UserMilestoneProgress.best_score))\
        .filter_by(user_id=user_id).scalar()

    syntax_score = 0.0
    test_pts = (latest_test.score * 10.0) if (latest_test and latest_test.score is not None) else 0.0
    ms_pts = (float(best_milestone_scores) * 10.0) if (best_milestone_scores and float(best_milestone_scores) > 0) else 0.0

    if test_pts > 0 and ms_pts > 0:
        syntax_score = round(min(100.0, (test_pts * 0.5) + (ms_pts * 0.5)), 1)
    elif test_pts > 0:
        syntax_score = round(min(100.0, test_pts), 1)
    elif ms_pts > 0:
        syntax_score = round(min(100.0, ms_pts), 1)

    if syntax_score > 0:
        syntax_desc = f"Năng lực cú pháp đạt {syntax_score}đ qua bài thi và chặng thử thách."
    else:
        syntax_desc = "Chưa hoàn thành bài kiểm tra hoặc thử thách lắp ráp câu."

    # 6. TÍNH KIÊN TRÌ (GRIT - 0-100)
    streak_points = min(50.0, streak_count * 7.0)
    time_points = min(50.0, (study_mins / 90.0) * 50.0)
    grit_score = round(min(100.0, streak_points + time_points), 1)

    dimensions = [
        {
            "key": "vocabulary",
            "name": "Vốn Từ Vựng",
            "english": "Vocabulary",
            "score": vocab_score,
            "desc": f"Đã nắm vững {len(user_vocabs)}/{benchmark_needed} từ vựng mục tiêu Band {target_band}."
        },
        {
            "key": "grammar",
            "name": "Chuẩn Ngữ Pháp",
            "english": "Grammar",
            "score": grammar_score,
            "desc": f"Đã học {len(user_grammars)} quy tắc, vượt qua {completed_milestones} chặng học thuật."
        },
        {
            "key": "fluency",
            "name": "Tốc Độ Phản Xạ",
            "english": "Fluency",
            "score": fluency_score,
            "desc": fluency_desc
        },
        {
            "key": "retention",
            "name": "Độ Bền Trí Nhớ",
            "english": "Retention",
            "score": retention_score,
            "desc": retention_desc
        },
        {
            "key": "syntax",
            "name": "Cú Pháp Câu",
            "english": "Syntax",
            "score": syntax_score,
            "desc": syntax_desc
        },
        {
            "key": "grit",
            "name": "Tính Kiên Trì",
            "english": "Grit",
            "score": grit_score,
            "desc": f"Kỷ luật học tập qua chuỗi Streak {streak_count} ngày và {study_mins} phút rèn luyện."
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
    elif overall_score >= 50:
        overall_grade = "B"
        grade_title = "Vững Vàng Căn Bản"
        grade_color = "var(--neon-amber)"
    elif overall_score >= 30:
        overall_grade = "C"
        grade_title = "Đang Rèn Luyện"
        grade_color = "#94a3b8"
    elif overall_score > 0:
        overall_grade = "D"
        grade_title = "Tân Binh Tiềm Năng"
        grade_color = "#ef4444"
    else:
        overall_grade = "N/A"
        grade_title = "Chưa Khảo Thí"
        grade_color = "#94a3b8"

    sorted_dims = sorted(dimensions, key=lambda d: d["score"])
    weakest = sorted_dims[0]
    strongest = sorted_dims[-1]

    advice_map = {
        "vocabulary": f"Kho từ vựng hiện tại ({len(user_vocabs)}/{benchmark_needed} từ) cần bổ sung thêm. Hãy tích cực tham gia Lò Đúc để nạp 10 từ mới mỗi ngày.",
        "grammar": "Độ chuẩn ngữ pháp còn dao động. Hãy ôn lại các chuyên đề thì và cấu trúc câu qua các bài Vi Học 30s.",
        "fluency": "Tốc độ xử lý còn ngập ngừng. Hãy vào Đấu Trường Gacha Arena rèn phản xạ dưới 2.0s/từ.",
        "retention": "Tỷ lệ quên từ sau 48h còn khá cao. Bạn nên tận dụng tính năng Ôn Tập Spaced Repetition vào mỗi sáng.",
        "syntax": "Cú pháp câu còn lúng túng. Hãy thực hiện thêm các thử thách Lắp Ráp Cú Pháp trong Lộ Trình để hình thành phản xạ bản ngữ.",
        "grit": f"Tính kỷ luật rèn luyện cần được duy trì đều đặn. Hãy duy trì chuỗi Streak điểm danh và rèn luyện ít nhất 15 phút mỗi ngày."
    }
    pedagogical_advice = advice_map.get(weakest["key"], "Hãy tiếp tục cân bằng và nâng cao toàn diện 6 trục năng lực!")

    return {
        "user_id": user.id,
        "username": user.username,
        "target_band": target_band,
        "current_band": current_band,
        "has_data": True,
        "is_unranked": False,
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