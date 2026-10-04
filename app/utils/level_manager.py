from datetime import datetime
from app.models.user import User
from app.models.user_vocabulary import UserVocabulary
from app.models.test import TestLog
from app.models.roadmap import UserMilestoneProgress, RoadmapMilestone
from app import db

# BẢNG ÁNH XẠ RANK HỌC THUẬT THEO KHUNG CEFR & ĐIỂM RP (MỐC CHUẨN ĐƯỢC ĐIỀU CHỈNH GẦN GŨI VỚI NỖ LỰC HỌC THỰC TẾ)
ACADEMIC_TIERS = [
    {
        "band": "C2",
        "rank_name": "ĐỘC CÔ CẦU BẠI (Diamond)",
        "min_milestones": 16,
        "min_rp": 530,
        "req_vocab": 1800,
        "req_sentence": 1200,
        "icon": "👑",
        "color": "#ec4899",
        "badge_class": "c2",
        "description": "Tinh hoa Độc Cô Cầu Bại: Cú pháp học thuật phức hợp, từ vựng triết học & học thuật đỉnh cao."
    },
    {
        "band": "C1",
        "rank_name": "Kiến Trúc Sư C1 (Platinum)",
        "min_milestones": 12,
        "min_rp": 370,
        "req_vocab": 1100,
        "req_sentence": 700,
        "icon": "💎",
        "color": "#06b6d4",
        "badge_class": "c1",
        "description": "Cao cấp học thuật: Đảo ngữ nâng cao, Câu chẻ nhấn mạnh, Giả định thức, Chuẩn IELTS 7.5+."
    },
    {
        "band": "B2",
        "rank_name": "Pháp Sư B2 (Gold)",
        "min_milestones": 8,
        "min_rp": 240,
        "req_vocab": 700,
        "req_sentence": 450,
        "icon": "🥇",
        "color": "#f59e0b",
        "badge_class": "b2",
        "description": "Trung cao cấp: Câu điều kiện loại 2, Quá khứ hoàn thành, Câu tường thuật gián tiếp."
    },
    {
        "band": "B1",
        "rank_name": "Chiến Binh B1 (Silver)",
        "min_milestones": 5,
        "min_rp": 140,
        "req_vocab": 400,
        "req_sentence": 250,
        "icon": "🥈",
        "color": "#a855f7",
        "badge_class": "b1",
        "description": "Trung cấp: Hiện tại hoàn thành, Câu bị động, Câu điều kiện loại 1, Mệnh đề quan hệ xác định."
    },
    {
        "band": "A2",
        "rank_name": "Thợ Săn A2 (Bronze II)",
        "min_milestones": 3,
        "min_rp": 60,
        "req_vocab": 160,
        "req_sentence": 90,
        "icon": "🥉",
        "color": "#38bdf8",
        "badge_class": "a2",
        "description": "Sơ cấp: Quá khứ đơn, Be going to, So sánh hơn & hơn nhất, Động từ khuyết thiếu cơ bản."
    },
    {
        "band": "A1",
        "rank_name": "Tân Binh A1 (Bronze I)",
        "min_milestones": 0,
        "min_rp": 0,
        "req_vocab": 0,
        "req_sentence": 0,
        "icon": "🥉",
        "color": "#94a3b8",
        "badge_class": "a1",
        "description": "Tân binh nhập môn: Ngữ pháp cơ bản S-V-O, Hiện tại đơn, Đại từ nhân xưng, Từ vựng thường nhật."
    }
]

def get_user_daily_exam_info(user):
    """
    Quản lý hạn mức làm bài kiểm tra theo ngày (Daily Exam Limit):
    - Mỗi ngày có 3 lượt thi miễn phí.
    - Reset lượt miễn phí khi sang ngày mới.
    - Cho phép mua thêm vé thi bằng Xu Vàng (15 Xu/lượt).
    """
    from datetime import date
    today = date.today()
    if not user:
        return {
            "free_limit": 3,
            "used_today": 0,
            "remaining_free": 3,
            "extra_tickets": 0,
            "total_available": 3,
            "can_take_exam": True,
            "ticket_price": 15,
            "user_coins": 0
        }

    # Reset lượt nếu sang ngày mới
    if getattr(user, 'last_exam_date', None) != today:
        user.daily_exams_used = 0
        user.last_exam_date = today
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    used = user.daily_exams_used or 0
    free_limit = 3
    remaining_free = max(0, free_limit - used)
    extra = user.extra_exam_tickets or 0
    total_available = remaining_free + extra
    can_take = total_available > 0

    return {
        "free_limit": free_limit,
        "used_today": used,
        "remaining_free": remaining_free,
        "extra_tickets": extra,
        "total_available": total_available,
        "can_take_exam": can_take,
        "ticket_price": 15,
        "user_coins": user.coins or 0
    }

SECTION_NAMES = {
    "vocab_mcq": "Nhận Diện Từ Vựng (MCQ)",
    "word_scramble": "Gỡ Bom Ký Tự (Scramble)",
    "syntax": "Lắp Ráp Cú Pháp (Syntax)",
    "grammar_cloze": "Vận Dụng Ngữ Pháp (Cloze)"
}

BAND_HIERARCHY = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}


def compute_user_academic_tier(user):
    """
    Tính toán Rank học thuật của người dùng dựa trên:
    1. Điểm uy tín học thuật (Academic RP).
    2. Đạt chuẩn thông qua chặng Lộ trình HOẶC Kỳ thi chuẩn hóa CEFR.
    Nếu RP tụt sâu dưới ngưỡng an toàn, người dùng sẽ bị GIÁNG HẠNG (Demotion)!
    """
    if not user:
        return "Tân Binh A1 (Bronze I)", "A1"

    completed_milestones = 0
    try:
        completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user.id, is_completed=True).count()
    except Exception:
        pass

    user_rp = user.academic_rp if user.academic_rp is not None else 0
    user_band = getattr(user, 'current_band', 'A1') or 'A1'
    user_band_val = BAND_HIERARCHY.get(user_band.upper(), 1)

    target_tier = ACADEMIC_TIERS[-1]  # Mặc định A1

    for tier in ACADEMIC_TIERS:
        tier_band_val = BAND_HIERARCHY.get(tier["band"], 1)
        # Thăng/giữ hạng nếu đủ điểm RP VÀ (hoàn thành đủ mốc chặng HOẶC đã đạt chuẩn Band tương ứng qua kỳ thi CEFR)
        is_qualified = (completed_milestones >= tier["min_milestones"] or user_band_val >= tier_band_val)
        if is_qualified and user_rp >= tier["min_rp"]:
            target_tier = tier
            break

    return target_tier["rank_name"], target_tier["band"]


def get_user_rank_progress(user):
    """
    Tính toán chi tiết tiến trình Rank học thuật của người dùng:
    - Rank hiện tại & Band hiện tại
    - Điểm RP hiện tại & Số chặng đã hoàn thành
    - Mốc thăng hạng kế tiếp (Next Rank, Next RP, Next Milestones)
    - Tỷ lệ % tiến độ thanh Progress Bar và số RP còn thiếu
    - Danh sách 6 cấp bậc chuẩn CEFR
    """
    tiers_asc = list(reversed(ACADEMIC_TIERS))  # A1 -> C2

    if not user:
        return {
            "current_rank": tiers_asc[0]["rank_name"],
            "current_band": tiers_asc[0]["band"],
            "current_icon": tiers_asc[0].get("icon", "🥉"),
            "current_color": tiers_asc[0].get("color", "#94a3b8"),
            "current_rp": 0,
            "completed_milestones": 0,
            "tier_min_rp": 0,
            "next_rank": tiers_asc[1]["rank_name"],
            "next_band": tiers_asc[1]["band"],
            "next_icon": tiers_asc[1].get("icon", "🥉"),
            "next_rp": tiers_asc[1]["min_rp"],
            "next_milestones": tiers_asc[1]["min_milestones"],
            "progress_percent": 0,
            "rp_needed": tiers_asc[1]["min_rp"],
            "is_max": False,
            "all_tiers": tiers_asc
        }

    user_rp = user.academic_rp if user.academic_rp is not None else 0
    user_band = getattr(user, 'current_band', 'A1') or 'A1'
    user_band_val = BAND_HIERARCHY.get(user_band.upper(), 1)

    try:
        completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user.id, is_completed=True).count()
    except Exception:
        completed_milestones = 0

    current_tier_idx = 0
    for idx, tier in enumerate(tiers_asc):
        tier_band_val = BAND_HIERARCHY.get(tier["band"], 1)
        is_qualified = (completed_milestones >= tier["min_milestones"] or user_band_val >= tier_band_val)
        if user_rp >= tier["min_rp"] and is_qualified:
            current_tier_idx = idx

    current_tier = tiers_asc[current_tier_idx]

    if current_tier_idx < len(tiers_asc) - 1:
        next_tier = tiers_asc[current_tier_idx + 1]
        rp_span = max(1, next_tier["min_rp"] - current_tier["min_rp"])
        current_in_tier = max(0, user_rp - current_tier["min_rp"])
        progress_pct = min(100, int((current_in_tier / rp_span) * 100))
        rp_needed = max(0, next_tier["min_rp"] - user_rp)
        is_max = False
    else:
        next_tier = current_tier
        progress_pct = 100
        rp_needed = 0
        is_max = True

    return {
        "current_rank": current_tier["rank_name"],
        "current_band": current_tier["band"],
        "current_icon": current_tier.get("icon", "🥉"),
        "current_color": current_tier.get("color", "#94a3b8"),
        "current_rp": user_rp,
        "completed_milestones": completed_milestones,
        "tier_min_rp": current_tier["min_rp"],
        "next_rank": next_tier["rank_name"],
        "next_band": next_tier["band"],
        "next_icon": next_tier.get("icon", "🥉"),
        "next_rp": next_tier["min_rp"],
        "next_milestones": next_tier["min_milestones"],
        "progress_percent": progress_pct,
        "rp_needed": rp_needed,
        "is_max": is_max,
        "all_tiers": tiers_asc
    }



def check_and_update_level(user_id):
    """
    Kiểm tra và cập nhật trạng thái Rank/Level học thuật cho người dùng.
    Hỗ trợ cả thăng hạng (Promotion) lẫn giáng hạng (Demotion).
    """
    if not user_id:
        return False, None
    user = User.query.get(user_id)
    if not user:
        return False, None

    new_rank_name, new_band = compute_user_academic_tier(user)

    level_changed = False
    old_rank = user.current_level

    if user.current_level != new_rank_name or getattr(user, 'current_band', 'A1') != new_band:
        user.current_level = new_rank_name
        user.current_band = new_band
        db.session.commit()
        level_changed = True

    return level_changed, user.current_level


def process_exam_result(user_id, milestone_id, exam_score, section_scores, is_abandoned=False, is_practice=False):
    """
    Quy trình xử lý kết quả khảo thí chặng Lộ trình Target Band:
    - Nếu is_practice=True (Chế độ Đấu tập / Thi thử):
      + Không trừ RP, không giáng hạng, không phạt Cooldown.
      + Cung cấp toàn bộ chẩn đoán điểm liệt và phản hồi để người học cọ xát an toàn.
    - Nếu is_practice=False (Khảo thí Xếp hạng Thực tế):
      + 1. Quy tắc Điểm Liệt: Mọi phần thi phải >= 6.0/10.0. Nếu có 1 phần < 6.0 -> TRƯỢT NGAY.
      + 2. Điểm Chuẩn Qua Ải: Tổng điểm >= 8.2/10.0.
      + 3. Thưởng / Phạt RP: Đỗ +60 đến +100 RP. Trượt phạt -45 RP (Bỏ cuộc -65 RP).
      + 4. Giáng hạng nếu RP tụt dưới ngưỡng; phạt Cooldown ôn tập.
    """
    if not user_id or not milestone_id:
        return {"error": "Thiếu mã người dùng hoặc mã chặng thi!"}
    user = User.query.get(user_id)
    milestone = RoadmapMilestone.query.get(milestone_id)
    if not user or not milestone:
        return {"error": "Không tìm thấy người dùng hoặc chặng thi!"}

    if user.academic_rp is None:
        user.academic_rp = 0

    old_rank = user.current_level
    old_band = getattr(user, 'current_band', 'A1')
    old_rp = user.academic_rp

    progress = UserMilestoneProgress.query.filter_by(user_id=user_id, milestone_id=milestone_id).first()
    if not progress:
        progress = UserMilestoneProgress(user_id=user_id, milestone_id=milestone_id, attempts=1, best_score=0.0)
        db.session.add(progress)
    else:
        if not is_practice:
            progress.attempts = (progress.attempts or 0) + 1

    # Kiểm tra Điểm Liệt (Ngưỡng khắc nghiệt >= 6.0)
    disqualified = False
    disqualified_sections = []
    for sec_key, sec_score in section_scores.items():
        if sec_score < 6.0:
            disqualified = True
            sec_label = SECTION_NAMES.get(sec_key, sec_key)
            disqualified_sections.append(f"{sec_label} ({sec_score:.1f}/10)")

    passed = False
    disqualified_reason = None

    if is_abandoned:
        disqualified = True
        disqualified_reason = "Bỏ dở bài thi giữa chừng! Hệ thống tính 0 điểm và phạt vi phạm quy chế thi."
    elif disqualified:
        disqualified_reason = f"DÍNH ĐIỂM LIỆT! Các phần thi dưới 6.0 điểm: {', '.join(disqualified_sections)}. Quy chế thi yêu cầu mọi phần phải đạt tối thiểu 6.0/10."
    elif exam_score < 8.2:
        disqualified_reason = f"Chưa đạt điểm chuẩn qua ải ({exam_score:.1f}/10.0). Điểm chuẩn học thuật yêu cầu tối thiểu 8.2/10.0."
    else:
        passed = True

    # NẾU LÀ CHẾ ĐỘ THI THỬ (PRACTICE MODE) -> KHÔNG THƯỞNG PHẠT RP, KHÔNG COOLDOWN
    if is_practice:
        return {
            "passed": passed,
            "score": exam_score,
            "best_score": progress.best_score or 0.0,
            "is_completed": progress.is_completed,
            "section_scores": section_scores,
            "disqualified": disqualified,
            "disqualified_reason": disqualified_reason,
            "rp_change": 0,
            "old_rp": old_rp,
            "new_rp": user.academic_rp,
            "promoted": False,
            "demoted": False,
            "current_rank": user.current_level,
            "current_band": getattr(user, 'current_band', 'A1'),
            "consecutive_fails": user.consecutive_fails or 0,
            "cooldown_seconds": 0,
            "reward_coins": 0,
            "is_practice": True
        }

    rp_change = 0
    demoted = False
    promoted = False

    if passed:
        # Tính thưởng RP (Mốc chuẩn được điều chỉnh tương ứng với nỗ lực học thực tế)
        if exam_score >= 9.5:
            rp_change = 25
        elif exam_score >= 8.5:
            rp_change = 20
        else:
            rp_change = 15

        user.academic_rp += rp_change
        user.consecutive_fails = 0

        if exam_score > (progress.best_score or 0.0):
            progress.best_score = exam_score

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.now()
            # Thưởng xu khi đỗ chặng
            user.coins += milestone.reward_coins

        # Kiểm tra thăng hạng
        new_rank, new_band = compute_user_academic_tier(user)
        if new_rank != old_rank:
            user.current_level = new_rank
            user.current_band = new_band
            promoted = True

    else:
        # Bị phạt trừ RP (Chuẩn khảo thí kỷ luật nghiêm ngặt)
        if is_abandoned:
            rp_change = -18  # Phạt -18 RP khi tự ý bỏ cuộc / thoát phòng thi
        else:
            rp_change = -10

        user.academic_rp = max(0, user.academic_rp + rp_change)
        user.consecutive_fails = (user.consecutive_fails or 0) + 1
        user.last_exam_fail_time = datetime.now()

        # Kiểm tra nguy cơ Giáng Hạng (Demotion)
        new_rank, new_band = compute_user_academic_tier(user)
        if new_rank != old_rank:
            # RP tụt xuống dưới ngưỡng của bậc rank hiện tại -> Giáng cấp!
            user.current_level = new_rank
            user.current_band = new_band
            demoted = True

    db.session.commit()

    return {
        "passed": passed,
        "score": exam_score,
        "best_score": progress.best_score,
        "is_completed": progress.is_completed,
        "section_scores": section_scores,
        "disqualified": disqualified,
        "disqualified_reason": disqualified_reason,
        "rp_change": rp_change,
        "old_rp": old_rp,
        "new_rp": user.academic_rp,
        "promoted": promoted,
        "demoted": demoted,
        "current_rank": user.current_level,
        "current_band": getattr(user, 'current_band', 'A1'),
        "consecutive_fails": user.consecutive_fails,
        "cooldown_seconds": 90 if not passed else 0,
        "reward_coins": milestone.reward_coins if passed else 0
    }