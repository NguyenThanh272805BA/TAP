from app.models.user import User
from app.models.user_vocabulary import UserVocabulary
from app.models.test import TestLog
from app import db

RANKS = [
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
    user = User.query.get(user_id)
    if not user: return False, None

    vocab_count = UserVocabulary.query.filter_by(user_id=user_id, memorization_level='DA_THUOC').count()
    sentences_count = TestLog.query.filter(TestLog.user_id == user_id, TestLog.score >= 5.0).count()

    new_rank_name = "Tân Binh Ngơ Ngác"
    for rank in RANKS:
        _, name, req_vocab, req_sentence = rank
        if vocab_count >= req_vocab and sentences_count >= req_sentence:
            new_rank_name = name
            break

    if user.current_level != new_rank_name:
        user.current_level = new_rank_name
        db.session.commit()
        return True, new_rank_name
    return False, user.current_level