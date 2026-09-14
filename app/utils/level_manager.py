from app.models.user import User
from app.models.user_vocabulary import UserVocabulary
from app.models.test import TestLog
from app.models.roadmap import UserMilestoneProgress, RoadmapMilestone
from app import db

# BẢNG ÁNH XẠ RANK HỌC THUẬT THEO KHUNG CEFR & TIẾN ĐỘ CHẶNG (ACADEMIC ROADMAP TIERS)
ACADEMIC_TIERS = [
    {"band": "C2", "rank_name": "ĐỘC CÔ CẦU BẠI (Diamond)", "min_milestones": 25, "req_vocab": 3000, "req_sentence": 2000},
    {"band": "C1", "rank_name": "Kiến Trúc Sư C1 (Platinum)", "min_milestones": 18, "req_vocab": 1800, "req_sentence": 1200},
    {"band": "B2", "rank_name": "Pháp Sư B2 (Gold)", "min_milestones": 12, "req_vocab": 1000, "req_sentence": 600},
    {"band": "B1", "rank_name": "Chiến Binh B1 (Silver)", "min_milestones": 7, "req_vocab": 500, "req_sentence": 300},
    {"band": "A2", "rank_name": "Thợ Săn A2 (Bronze II)", "min_milestones": 3, "req_vocab": 150, "req_sentence": 80},
    {"band": "A1", "rank_name": "Tân Binh A1 (Bronze I)", "min_milestones": 0, "req_vocab": 0, "req_sentence": 0}
]

# Danh mục danh hiệu cổ điển để tương thích ngược
LEGACY_RANKS = [
    (20, "ĐỘC CÔ CẦU BẠI", 5000, 3500), (19, "Á Thần Ngôn Ngữ", 4000, 2700),
    (18, "Triết Gia Toàn Thư", 3300, 2200), (17, "Kẻ Hủy Diệt Ngữ Pháp", 2700, 1800),
    (16, "Kiến Trúc Sư Thực Tại", 2200, 1500), (15, "Kẻ Bẻ Cong Ngôn Ngữ", 1800, 1200),
    (14, "Lãnh Chúa Từ Điển", 1450, 1000), (13, "Bậc Thầy Giao Tiếp", 1150, 800),
    (12, "Nghệ Nhân Ghép Chữ", 900, 650), (11, "Học Giả Tinh Anh", 700, 500),
    (10, "Pháp Sư Ngôn Ngữ", 500, 350), (9, "Hiệp Sĩ Cú Pháp", 350, 250),
    (8, "Đạo Tặc Từ Vựng", 250, 180), (7, "Chiến Binh Giao Tiếp", 180, 120),
    (6, "Trinh Sát Ngữ Pháp", 120, 80), (5, "Thợ Săn Ngôn Từ", 80, 50),
    (4, "Kẻ Lang Thang", 50, 30), (3, "Kẻ Sống Sót", 30, 15),
    (2, "Thực Tập Sinh", 10, 5), (1, "Tân Binh Ngơ Ngác", 0, 0)
]


def check_and_update_level(user_id):
    """
    Hệ thống nâng cấp cấp bậc thích ứng:
    Kết hợp giữa số Chặng Milestone lộ trình đã vượt qua + Số lượng từ đã thuộc và câu đã kiểm tra.
    """
    user = User.query.get(user_id)
    if not user:
        return False, None

    # 1. Đếm số lượng mốc học tập thực tế
    vocab_count = UserVocabulary.query.filter_by(user_id=user_id, memorization_level='DA_THUOC').count()
    sentences_count = TestLog.query.filter(TestLog.user_id == user_id, TestLog.score >= 5.0).count()
    completed_milestones = UserMilestoneProgress.query.filter_by(user_id=user_id, is_completed=True).count()

    new_rank_name = "Tân Binh A1 (Bronze I)"
    new_current_band = "A1"

    # 2. Quét kiểm tra thăng hạng theo Tier lộ trình học thuật
    for tier in ACADEMIC_TIERS:
        milestone_ok = completed_milestones >= tier["min_milestones"]
        vocab_ok = vocab_count >= tier["req_vocab"]
        
        # Thăng cấp nếu hoàn thành chặng lộ trình tương ứng HOẶC cày cuốc tích lũy từ vựng
        if milestone_ok or (vocab_ok and sentences_count >= tier["req_sentence"]):
            new_rank_name = tier["rank_name"]
            new_current_band = tier["band"]
            break

    level_changed = False
    if user.current_level != new_rank_name or getattr(user, 'current_band', 'A1') != new_current_band:
        user.current_level = new_rank_name
        user.current_band = new_current_band
        db.session.commit()
        level_changed = True

    return level_changed, user.current_level