import random
from datetime import datetime, timedelta
from app import db
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary

def generate_50_vocab_exam(user_id=None):
    """Sinh đề thi kiểm tra nghĩa 50 từ vựng với 4 phương án trắc nghiệm chuẩn xác"""
    # 1. Thu thập từ vựng của người dùng (ưu tiên từ chưa thuộc)
    user_words = []
    if user_id:
        uv_records = db.session.query(Vocabulary).join(
            UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
        ).filter(
            UserVocabulary.user_id == user_id
        ).all()
        user_words = uv_records

    # 2. Thu thập thêm từ vựng hệ thống nếu chưa đủ 50 từ
    all_system_words = Vocabulary.query.all()
    if not all_system_words:
        return {"error": "Ngân hàng từ vựng rỗng!"}

    selected_words = []
    # Ưu tiên lấy từ user trước
    if user_words:
        random.shuffle(user_words)
        selected_words.extend(user_words[:35])

    # Bổ sung từ kho hệ thống để đủ 50 từ
    seen_ids = {w.id for w in selected_words}
    remaining_pool = [w for w in all_system_words if w.id not in seen_ids]
    random.shuffle(remaining_pool)

    needed = 50 - len(selected_words)
    if needed > 0:
        selected_words.extend(remaining_pool[:needed])

    # Nếu toàn hệ thống có ít hơn 50 từ, lấy tối đa có thể
    random.shuffle(selected_words)

    # Tập hợp tất cả các nghĩa để làm distractor
    all_meanings = [w.meaning for w in all_system_words if w.meaning]

    questions = []
    for idx, v in enumerate(selected_words, 1):
        correct_meaning = v.meaning
        # Chọn 3 nghĩa gây nhiễu
        distractors = [m for m in all_meanings if m != correct_meaning]
        chosen_distractors = random.sample(distractors, min(3, len(distractors)))
        
        while len(chosen_distractors) < 3:
            chosen_distractors.append(f"Ý nghĩa khác của từ vựng ({len(chosen_distractors)+1})")

        options = [correct_meaning] + chosen_distractors
        random.shuffle(options)
        correct_idx = options.index(correct_meaning)

        questions.append({
            "id": idx,
            "question_num": idx,
            "vocab_id": v.id,
            "word": v.word,
            "theme": v.theme or "General",
            "cefr_level": v.cefr_level or "A1",
            "prompt": f"Hãy chọn bản dịch hoặc định nghĩa tiếng Việt chuẩn xác nhất cho từ '{v.word}':",
            "options": options,
            "correct_idx": correct_idx,
            "correct_meaning": correct_meaning
        })

    return {
        "status": "success",
        "total_questions": len(questions),
        "exam_title": f"BÀI KHẢO THÍ CHẨN ĐOÁN TỪ VỰNG ({len(questions)} TỪ)",
        "questions": questions
    }


def evaluate_50_vocab_exam(questions, user_answers):
    """Chấm điểm bài thi và trả về kết quả chi tiết từng câu phục vụ màn hình Review"""
    correct_count = 0
    results = []
    opt_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

    for q in questions:
        q_num = str(q["question_num"])
        selected_option_idx = user_answers.get(q_num)
        if selected_option_idx is None:
            selected_option_idx = user_answers.get(str(q.get("id")))

        if isinstance(selected_option_idx, str) and selected_option_idx.strip().upper() in opt_map:
            selected_option_idx = opt_map[selected_option_idx.strip().upper()]
        elif selected_option_idx is not None:
            try:
                selected_option_idx = int(selected_option_idx)
            except (ValueError, TypeError):
                selected_option_idx = -1
        else:
            selected_option_idx = -1

        is_correct = (selected_option_idx == q["correct_idx"])
        if is_correct:
            correct_count += 1

        user_selected_text = q["options"][selected_option_idx] if 0 <= selected_option_idx < len(q["options"]) else "Chưa chọn"

        results.append({
            "question_num": q["question_num"],
            "vocab_id": q["vocab_id"],
            "word": q["word"],
            "theme": q["theme"],
            "cefr_level": q["cefr_level"],
            "user_choice_idx": selected_option_idx,
            "user_choice_text": user_selected_text,
            "correct_meaning": q["correct_meaning"],
            "is_correct": is_correct,
            # Mặc định gợi ý trạng thái dựa trên kết quả trả lời
            "suggested_status": "DA_THUOC" if is_correct else "CHUA_THUOC"
        })

    total = len(questions)
    percentage = round((correct_count / total) * 100, 1) if total > 0 else 0

    return {
        "total_questions": total,
        "correct_count": correct_count,
        "percentage": percentage,
        "estimated_cefr": "C1/C2" if percentage >= 90 else ("B2" if percentage >= 75 else ("B1" if percentage >= 60 else "A2")),
        "review_list": results
    }


def apply_self_assessment_and_generate_srs_roadmap(user_id, assessments):
    """
    Cập nhật trạng thái [ĐÃ THUỘC - HƠI THUỘC - CHƯA THUỘC] vào DB
    và sinh lộ trình học tập cá nhân hóa chuẩn Spaced Repetition (SRS)
    """
    now = datetime.now()
    da_thuoc = []
    hoi_thuoc = []
    chua_thuoc = []

    for item in assessments:
        vocab_id = item.get("vocab_id")
        level = item.get("memorization_level", "CHUA_THUOC").upper()
        if not vocab_id:
            continue

        v = Vocabulary.query.get(vocab_id)
        if not v:
            continue

        uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
        if not uv:
            uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True)
            db.session.add(uv)

        uv.last_tested_at = now

        if level == 'DA_THUOC':
            uv.memorization_level = 'DA_THUOC'
            uv.next_review_time = now + timedelta(days=7) # Ôn lại sau 7 ngày
            da_thuoc.append({"id": v.id, "word": v.word, "meaning": v.meaning, "cefr": v.cefr_level})
        elif level == 'HOI_THUOC':
            uv.memorization_level = 'DANG_HOC'
            uv.next_review_time = now + timedelta(days=1, hours=12) # Ôn lại sau 36 giờ
            hoi_thuoc.append({"id": v.id, "word": v.word, "meaning": v.meaning, "cefr": v.cefr_level})
        else: # CHUA_THUOC
            uv.memorization_level = 'CHUA_THUOC'
            uv.next_review_time = now # Ôn ngay hôm nay
            chua_thuoc.append({"id": v.id, "word": v.word, "meaning": v.meaning, "cefr": v.cefr_level})

    db.session.commit()

    total_evaluated = len(assessments)
    roadmap = {
        "summary": {
            "total_evaluated": total_evaluated,
            "da_thuoc_count": len(da_thuoc),
            "hoi_thuoc_count": len(hoi_thuoc),
            "chua_thuoc_count": len(chua_thuoc),
            "mastery_rate": round((len(da_thuoc) / total_evaluated) * 100, 1) if total_evaluated > 0 else 0
        },
        "phases": [
            {
                "phase_num": 1,
                "title": "GIAI ĐOẠN 1: CẤP BÁCH — CHINH PHỤC TỪ CHƯA THUỘC",
                "timeframe": "Trong vòng 24 giờ tới",
                "badge": "KHẨN CẤP",
                "badge_color": "#ef4444",
                "description": f"Có {len(chua_thuoc)} từ vựng bạn chưa nắm được. Cần nạp lại ngay bằng phương pháp Flashcard và gỡ bom ký tự.",
                "words": chua_thuoc,
                "action_recommendation": "Dành 15 phút vào mục 'Lò Đúc' ôn tập ngay các từ này."
            },
            {
                "phase_num": 2,
                "title": "GIAI ĐOẠN 2: CỦNG CỐ PHẢN XẠ — CHUYỂN HÓA TRÍ NHỚ DÀI HẠN",
                "timeframe": "Sau 36 - 48 giờ",
                "badge": "TĂNG TỐC",
                "badge_color": "#f59e0b",
                "description": f"Có {len(hoi_thuoc)} từ vựng ở trạng thái nhận biết lờ mờ. Cần vận dụng đặt câu với AI để khắc sâu vào tiềm thức.",
                "words": hoi_thuoc,
                "action_recommendation": "Vào 'Đấu Trường AI' đặt câu phản xạ với các từ này đạt từ 6.0 điểm trở lên."
            },
            {
                "phase_num": 3,
                "title": "GIAI ĐOẠN 3: DUY TRÌ & BẢO CHỨNG — BỀN VỮNG TOÀN DIỆN",
                "timeframe": "Định kỳ sau 7 ngày",
                "badge": "VỮNG VÀNG",
                "badge_color": "#10b981",
                "description": f"Chúc mừng! {len(da_thuoc)} từ vựng đã được làm chủ xuất sắc. Hệ thống sẽ tự động nhắc nhở ôn lặp lại sau 1 tuần.",
                "words": da_thuoc[:10], # Trưng bày 10 từ tiêu biểu
                "action_recommendation": "Làm bài thi thử Mock Exam hàng tuần để duy trì phản xạ."
            }
        ],
        "phase_1": {
            "count": len(chua_thuoc),
            "words": chua_thuoc,
            "interval": "1-3 ngày"
        },
        "phase_2": {
            "count": len(hoi_thuoc),
            "words": hoi_thuoc,
            "interval": "4-7 ngày"
        },
        "phase_3": {
            "count": len(da_thuoc),
            "words": da_thuoc[:15],
            "interval": "14-30 ngày"
        }
    }

    return roadmap
