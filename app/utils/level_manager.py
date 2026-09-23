from datetime import datetime
from app.models.user import User
from app.models.user_vocabulary import UserVocabulary
from app.models.test import TestLog
from app.models.roadmap import UserMilestoneProgress, RoadmapMilestone
from app import db

# BẢNG ÁNH XẠ RANK HỌC THUẬT THEO KHUNG CEFR & ĐIỂM RP (ACADEMIC ROADMAP TIERS - CHUẨN KHẮC NGHIỆT)
ACADEMIC_TIERS = [
    {"band": "C2", "rank_name": "ĐỘC CÔ CẦU BẠI (Diamond)", "min_milestones": 16, "min_rp": 2400, "req_vocab": 1800, "req_sentence": 1200},
    {"band": "C1", "rank_name": "Kiến Trúc Sư C1 (Platinum)", "min_milestones": 12, "min_rp": 1700, "req_vocab": 1100, "req_sentence": 700},
    {"band": "B2", "rank_name": "Pháp Sư B2 (Gold)", "min_milestones": 8, "min_rp": 1200, "req_vocab": 700, "req_sentence": 450},
    {"band": "B1", "rank_name": "Chiến Binh B1 (Silver)", "min_milestones": 5, "min_rp": 800, "req_vocab": 400, "req_sentence": 250},
    {"band": "A2", "rank_name": "Thợ Săn A2 (Bronze II)", "min_milestones": 3, "min_rp": 450, "req_vocab": 160, "req_sentence": 90},
    {"band": "A1", "rank_name": "Tân Binh A1 (Bronze I)", "min_milestones": 0, "min_rp": 0, "req_vocab": 0, "req_sentence": 0}
]

SECTION_NAMES = {
    "vocab_mcq": "Nhận Diện Từ Vựng (MCQ)",
    "word_scramble": "Gỡ Bom Ký Tự (Scramble)",
    "syntax": "Lắp Ráp Cú Pháp (Syntax)",
    "grammar_cloze": "Vận Dụng Ngữ Pháp (Cloze)"
}


def compute_user_academic_tier(user):
    """
    Tính toán Rank học thuật của người dùng dựa trên đồng thời 2 yếu tố:
    1. Số chặng Lộ trình đã vượt qua (Completed Milestones).
    2. Điểm uy tín học thuật (Academic RP).
    Nếu RP tụt sâu dưới ngưỡng an toàn, người dùng sẽ bị GIÁNG HẠNG (Demotion)!
    """
    if not user:
        return "Tân Binh A1 (Bronze I)", "A1"

    completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user.id, is_completed=True).count()
    user_rp = user.academic_rp if user.academic_rp is not None else 500

    target_tier = ACADEMIC_TIERS[-1]  # Mặc định A1

    for tier in ACADEMIC_TIERS:
        # Điều kiện thăng/giữ hạng: Phải đủ cả mốc chặng VÀ đủ điểm RP uy tín
        if completed_milestones >= tier["min_milestones"] and user_rp >= tier["min_rp"]:
            target_tier = tier
            break

    return target_tier["rank_name"], target_tier["band"]


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


def process_exam_result(user_id, milestone_id, exam_score, section_scores, is_abandoned=False):
    """
    Quy trình xử lý kết quả khảo thí chặng Lộ trình Target Band KHẮC NGHIỆT chuẩn đời thật:
    1. Quy tắc Điểm Liệt: Mọi phần thi phải >= 6.0/10.0. Nếu có 1 phần < 6.0 -> TRƯỢT NGAY.
    2. Điểm Chuẩn Qua Ải: Tổng điểm >= 8.2/10.0.
    3. Thưởng / Phạt RP:
       - Đỗ: +60 đến +100 RP.
       - Trượt: Phạt -45 RP (Bỏ cuộc giữa chừng phạt -65 RP).
       - Trượt liên tiếp >= 2: Tăng cảnh báo giáng hạng.
       - Giáng hạng (Demotion) nếu RP tụt xuống dưới ngưỡng.
    4. Kích hoạt Cooldown 90 giây trước khi được thi lại để buộc ôn tập nghiêm túc.
    """
    if not user_id or not milestone_id:
        return {"error": "Thiếu mã người dùng hoặc mã chặng thi!"}
    user = User.query.get(user_id)
    milestone = RoadmapMilestone.query.get(milestone_id)
    if not user or not milestone:
        return {"error": "Không tìm thấy người dùng hoặc chặng thi!"}

    if user.academic_rp is None:
        user.academic_rp = 500

    old_rank = user.current_level
    old_band = getattr(user, 'current_band', 'A1')
    old_rp = user.academic_rp

    progress = UserMilestoneProgress.query.filter_by(user_id=user_id, milestone_id=milestone_id).first()
    if not progress:
        progress = UserMilestoneProgress(user_id=user_id, milestone_id=milestone_id, attempts=1, best_score=0.0)
        db.session.add(progress)
    else:
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

    rp_change = 0
    demoted = False
    promoted = False

    if passed:
        # Tính thưởng RP
        if exam_score >= 9.5:
            rp_change = 100
        elif exam_score >= 8.5:
            rp_change = 80
        else:
            rp_change = 60

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
            rp_change = -65  # Phạt nặng -65 RP khi tự ý bỏ cuộc / thoát phòng thi
        else:
            rp_change = -45

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