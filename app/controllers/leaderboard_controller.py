from flask import Blueprint, jsonify, request, session
from app import db
from app.models.user import User
from app.models.user_vocabulary import UserVocabulary
from app.models.roadmap import UserMilestoneProgress
from app.models.vocabulary import Vocabulary
from sqlalchemy.sql import func
import math

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/api/leaderboard')


def get_precomputed_user_metrics():
    """Truy vấn gom nhóm tối ưu hóa (O(1) lookup, loại bỏ N+1 query) các chỉ số phụ của người dùng."""
    # 1. Đếm số từ vựng ĐÃ THUỘC của mỗi user
    vocab_counts = dict(
        db.session.query(
            UserVocabulary.user_id,
            func.count(UserVocabulary.vocab_id)
        ).filter(
            UserVocabulary.memorization_level == 'DA_THUOC'
        ).group_by(UserVocabulary.user_id).all()
    )

    # 2. Đếm số chặng Lộ trình đã hoàn thành của mỗi user
    milestone_counts = dict(
        db.session.query(
            UserMilestoneProgress.user_id,
            func.count(UserMilestoneProgress.milestone_id)
        ).filter(
            UserMilestoneProgress.is_completed == True
        ).group_by(UserMilestoneProgress.user_id).all()
    )

    return vocab_counts, milestone_counts


@leaderboard_bp.route('', methods=['GET'])
@leaderboard_bp.route('/', methods=['GET'])
def get_leaderboard():
    category = request.args.get('category', 'overall').lower().strip()
    limit = min(int(request.args.get('limit', 50)), 100)
    current_user_id = session.get('user_id')

    # Lấy dữ liệu gom nhóm
    vocab_counts, milestone_counts = get_precomputed_user_metrics()

    users = User.query.all()
    user_records = []

    for u in users:
        v_count = vocab_counts.get(u.id, 0)
        m_count = milestone_counts.get(u.id, 0)
        study_mins = getattr(u, 'study_time_minutes', 0) or 0
        study_hours = round(study_mins / 60.0, 1)
        infinity = getattr(u, 'infinity_score', 0) or 0
        stage = getattr(u, 'arena_stage', 1) or 1
        rp = getattr(u, 'academic_rp', 500) or 500
        streak = getattr(u, 'streak_count', 0) or 0

        # Công thức tính Điểm Thành Tích Toàn Diện (Composite Achievement Score)
        # RP (1.0x) + Từ vựng đã thuộc (15x) + Điểm game vô cực (10x) + Ải arena (25x) + Chặng lộ trình (40x) + Giờ học (20x) + Streak (15x)
        composite_score = int(
            (rp * 1.0) +
            (v_count * 15) +
            (infinity * 10) +
            (stage * 25) +
            (m_count * 40) +
            (study_hours * 20) +
            (streak * 15)
        )

        user_records.append({
            "user_id": u.id,
            "username": u.username,
            "avatar": getattr(u, 'avatar', 'default_avatar.png') or 'default_avatar.png',
            "equipped_frame": getattr(u, 'equipped_frame', 'frame-default') or 'frame-default',
            "equipped_title": getattr(u, 'equipped_title', 'Tân Binh Ngơ Ngác') or 'Tân Binh Ngơ Ngác',
            "current_level": getattr(u, 'current_level', 'Tân Binh A1 (Bronze I)') or 'Tân Binh A1 (Bronze I)',
            "current_band": getattr(u, 'current_band', 'A1') or 'A1',
            "target_band": getattr(u, 'target_band', 'B2') or 'B2',
            "coins": getattr(u, 'coins', 0) or 0,
            # Các metrics cốt lõi
            "composite_score": composite_score,
            "infinity_score": infinity,
            "arena_stage": stage,
            "academic_rp": rp,
            "milestone_count": m_count,
            "vocab_count": v_count,
            "study_time_minutes": study_mins,
            "study_hours": study_hours,
            "streak_count": streak
        })

    # Sắp xếp danh sách theo Category được yêu cầu
    if category == 'game':
        # Tiêu chí: Điểm Vô Cực cao nhất, tiếp đến là Cấp Ải Đấu Trường
        user_records.sort(key=lambda x: (x['infinity_score'], x['arena_stage'], x['composite_score']), reverse=True)
        primary_metric_key = 'infinity_score'
        metric_label = 'Điểm Vô Cực'
        unit = 'pts'
    elif category == 'academic':
        # Tiêu chí: Điểm RP Học Thuật cao nhất, tiếp đến là Số Chặng Lộ Trình Đỗ
        user_records.sort(key=lambda x: (x['academic_rp'], x['milestone_count'], x['composite_score']), reverse=True)
        primary_metric_key = 'academic_rp'
        metric_label = 'Rank Points'
        unit = 'RP'
    elif category == 'vocabulary':
        # Tiêu chí: Số từ vựng đã chinh phục/thuộc lòng
        user_records.sort(key=lambda x: (x['vocab_count'], x['academic_rp'], x['composite_score']), reverse=True)
        primary_metric_key = 'vocab_count'
        metric_label = 'Từ Đã Thuộc'
        unit = 'từ'
    elif category == 'time':
        # Tiêu chí: Tổng thời gian học tập & Chuỗi rèn luyện Streak
        user_records.sort(key=lambda x: (x['study_time_minutes'], x['streak_count'], x['composite_score']), reverse=True)
        primary_metric_key = 'study_hours'
        metric_label = 'Thời Gian Học'
        unit = 'giờ'
    else: # 'overall' (Mặc định)
        category = 'overall'
        user_records.sort(key=lambda x: (x['composite_score'], x['academic_rp'], x['vocab_count']), reverse=True)
        primary_metric_key = 'composite_score'
        metric_label = 'Điểm Thành Tích'
        unit = 'EXP'

    # Gán thứ tự Rank chuẩn (1, 2, 3...)
    formatted_list = []
    my_rank_info = None

    for idx, item in enumerate(user_records, 1):
        item_copy = dict(item)
        item_copy['rank'] = idx
        item_copy['primary_value'] = item[primary_metric_key]
        item_copy['metric_label'] = metric_label
        item_copy['unit'] = unit

        if idx <= limit:
            formatted_list.append(item_copy)

        if current_user_id and item['user_id'] == current_user_id:
            my_rank_info = item_copy

    # Nếu user chưa vào top limit thì vẫn có my_rank_info đầy đủ
    if not my_rank_info and current_user_id:
        for idx, item in enumerate(user_records, 1):
            if item['user_id'] == current_user_id:
                item_copy = dict(item)
                item_copy['rank'] = idx
                item_copy['primary_value'] = item[primary_metric_key]
                item_copy['metric_label'] = metric_label
                item_copy['unit'] = unit
                my_rank_info = item_copy
                break

    # Phân loại Top 3 (Podium) và Danh sách Rank từ 4 trở đi
    podium = formatted_list[:3]
    rest_ranks = formatted_list[3:]

    return jsonify({
        "status": "success",
        "category": category,
        "primary_metric": primary_metric_key,
        "metric_label": metric_label,
        "unit": unit,
        "total_players": len(user_records),
        "podium": podium,
        "leaderboard": formatted_list,
        "rest_ranks": rest_ranks,
        "my_rank": my_rank_info
    }), 200


@leaderboard_bp.route('/categories', methods=['GET'])
def get_categories():
    """Trả về danh mục và thông tin mô tả của từng loại bảng xếp hạng."""
    return jsonify({
        "categories": [
            {
                "id": "overall",
                "name": "Tổng Hợp Toàn Diện",
                "icon": "🌟",
                "desc": "Điểm Thành Tích Toàn Năng tổng hợp từ cả 4 trụ cột rèn luyện"
            },
            {
                "id": "game",
                "name": "Chiến Tích Đấu Trường",
                "icon": "🎮",
                "desc": "Xếp hạng theo Kỷ lục Điểm Vô Cực và Cấp ải Gacha Arena"
            },
            {
                "id": "academic",
                "name": "Tiến Độ Học Thuật",
                "icon": "🎓",
                "desc": "Xếp hạng theo Điểm Rank RP và Số chặng Lộ Trình Milestone đã đỗ"
            },
            {
                "id": "vocabulary",
                "name": "Kho Từ Vựng Làm Chủ",
                "icon": "📚",
                "desc": "Xếp hạng theo Số lượng từ vựng học thuật CEFR đã ghi nhớ bền vững"
            },
            {
                "id": "time",
                "name": "Thời Gian & Kiên Trì",
                "icon": "⏱️",
                "desc": "Xếp hạng theo Tổng thời lượng học tập tích lũy và Chuỗi rèn luyện liên tục"
            }
        ]
    }), 200
