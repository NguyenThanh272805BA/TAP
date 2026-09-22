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


def evaluate_strict_rank_tier(rp, vocab_count=0, streak_count=0):
    """
    Hệ thống phân tầng Rank khắt khe chuẩn thi đấu Esports & Học thuật:
    Yêu cầu kép cả về Rank Points (RP), số lượng từ vựng đã thuộc và chuỗi rèn luyện Streak.
    """
    if rp >= 5500 and vocab_count >= 1000 and streak_count >= 25:
        return {
            "tier_name": "Thách Đấu Huyền Thoại",
            "division": "Challenger",
            "tier_code": "CHALLENGER",
            "badge_color": "linear-gradient(135deg, #f59e0b, #ec4899, #8b5cf6)",
            "border_color": "#ec4899",
            "glow": "0 0 20px rgba(236, 72, 153, 0.8)",
            "tier_icon": "👑"
        }
    elif rp >= 4500 and vocab_count >= 700 and streak_count >= 18:
        return {
            "tier_name": "Đại Cao Thủ",
            "division": "Grandmaster",
            "tier_code": "GRANDMASTER",
            "badge_color": "linear-gradient(135deg, #ef4444, #f97316)",
            "border_color": "#ef4444",
            "glow": "0 0 15px rgba(239, 68, 68, 0.7)",
            "tier_icon": "🔥"
        }
    elif rp >= 3500 and vocab_count >= 400 and streak_count >= 12:
        return {
            "tier_name": "Cao Thủ",
            "division": "Master",
            "tier_code": "MASTER",
            "badge_color": "linear-gradient(135deg, #a855f7, #6366f1)",
            "border_color": "#a855f7",
            "glow": "0 0 15px rgba(168, 85, 247, 0.6)",
            "tier_icon": "⚡"
        }
    elif rp >= 2600 and vocab_count >= 200 and streak_count >= 6:
        div = "I" if rp >= 3200 else ("II" if rp >= 2900 else "III")
        return {
            "tier_name": f"Kim Cương {div}",
            "division": f"Diamond {div}",
            "tier_code": "DIAMOND",
            "badge_color": "linear-gradient(135deg, #06b6d4, #3b82f6)",
            "border_color": "#06b6d4",
            "glow": "0 0 12px rgba(6, 182, 212, 0.6)",
            "tier_icon": "💎"
        }
    elif rp >= 1800 and vocab_count >= 80:
        div = "I" if rp >= 2300 else ("II" if rp >= 2050 else "III")
        return {
            "tier_name": f"Bạch Kim {div}",
            "division": f"Platinum {div}",
            "tier_code": "PLATINUM",
            "badge_color": "linear-gradient(135deg, #10b981, #06b6d4)",
            "border_color": "#10b981",
            "glow": "0 0 10px rgba(16, 185, 129, 0.5)",
            "tier_icon": "🛡️"
        }
    elif rp >= 1000 and vocab_count >= 30:
        div = "I" if rp >= 1500 else ("II" if rp >= 1250 else "III")
        return {
            "tier_name": f"Vàng {div}",
            "division": f"Gold {div}",
            "tier_code": "GOLD",
            "badge_color": "linear-gradient(135deg, #f59e0b, #eab308)",
            "border_color": "#f59e0b",
            "glow": "0 0 8px rgba(245, 158, 11, 0.5)",
            "tier_icon": "⭐"
        }
    elif rp >= 500:
        div = "I" if rp >= 800 else ("II" if rp >= 650 else "III")
        return {
            "tier_name": f"Bạc {div}",
            "division": f"Silver {div}",
            "tier_code": "SILVER",
            "badge_color": "linear-gradient(135deg, #94a3b8, #cbd5e1)",
            "border_color": "#94a3b8",
            "glow": "0 0 5px rgba(148, 163, 184, 0.4)",
            "tier_icon": "🗡️"
        }
    else:
        div = "I" if rp >= 300 else ("II" if rp >= 150 else "III")
        return {
            "tier_name": f"Đồng {div}",
            "division": f"Bronze {div}",
            "tier_code": "BRONZE",
            "badge_color": "linear-gradient(135deg, #b45309, #78350f)",
            "border_color": "#b45309",
            "glow": "none",
            "tier_icon": "🥉"
        }


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

        # Đánh giá phân tầng Rank khắt khe đa chiều
        tier_info = evaluate_strict_rank_tier(rp, v_count, streak)

        # Công thức tính Điểm Thành Tích Toàn Diện (Composite Achievement Score)
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
            "current_level": tier_info["tier_name"],
            "rank_tier": tier_info,
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
