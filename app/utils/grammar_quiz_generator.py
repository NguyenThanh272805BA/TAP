import random
import re

GRAMMAR_COLLOCATIONS_PRESETS = {
    "present perfect": [
        {"collocation": "already", "meaning": "đã... rồi"},
        {"collocation": "just", "meaning": "vừa mới"},
        {"collocation": "yet", "meaning": "chưa"},
        {"collocation": "since + mốc tg", "meaning": "kể từ khi"},
        {"collocation": "for + khoảng tg", "meaning": "trong suốt"},
        {"collocation": "so far", "meaning": "cho tới nay"},
        {"collocation": "ever / never", "meaning": "từng / chưa bao giờ"}
    ],
    "past perfect": [
        {"collocation": "by the time", "meaning": "trước thời điểm"},
        {"collocation": "had already", "meaning": "đã hoàn tất trước"},
        {"collocation": "before / after", "meaning": "trước / sau khi"},
        {"collocation": "as soon as", "meaning": "ngay sau khi"}
    ],
    "past continuous": [
        {"collocation": "while / as", "meaning": "trong khi đang"},
        {"collocation": "when", "meaning": "khi (xen vào)"},
        {"collocation": "at that moment", "meaning": "vào thời điểm đó"},
        {"collocation": "all evening", "meaning": "suốt buổi tối"}
    ],
    "present continuous": [
        {"collocation": "right now", "meaning": "ngay lúc này"},
        {"collocation": "at the moment", "meaning": "hiện tại"},
        {"collocation": "currently", "meaning": "đang diễn ra"},
        {"collocation": "always + V-ing", "meaning": "phàn nàn thói quen"}
    ],
    "conditional": [
        {"collocation": "if only", "meaning": "giá như mà"},
        {"collocation": "provided that", "meaning": "với điều kiện là"},
        {"collocation": "as long as", "meaning": "miễn là"},
        {"collocation": "unless", "meaning": "trừ khi / nếu không"},
        {"collocation": "in case", "meaning": "phòng khi"},
        {"collocation": "otherwise", "meaning": "nếu không thì"}
    ],
    "passive": [
        {"collocation": "is widely regarded as", "meaning": "được coi rộng rãi là"},
        {"collocation": "was discovered by", "meaning": "được phát hiện bởi"},
        {"collocation": "has been proven to be", "meaning": "được chứng minh là"},
        {"collocation": "are expected to", "meaning": "được kỳ vọng sẽ"},
        {"collocation": "is considered to be", "meaning": "được nhận định là"}
    ],
    "by the time": [
        {"collocation": "by the time + S + V(htđ)", "meaning": "trước thời điểm (tương lai)"},
        {"collocation": "will have + V3/ed", "meaning": "sẽ đã hoàn tất"},
        {"collocation": "by next month", "meaning": "trước tháng tới"},
        {"collocation": "by then", "meaning": "cho tới lúc đó"}
    ],
    "svo": [
        {"collocation": "transitive verbs", "meaning": "ngoại động từ cần tân ngữ"},
        {"collocation": "direct object", "meaning": "tân ngữ trực tiếp"},
        {"collocation": "perform an action", "meaning": "chủ ngữ thực hiện hành động"},
        {"collocation": "every day / regularly", "meaning": "thói quen hàng ngày"}
    ],
    "inversion": [
        {"collocation": "hardly had... when", "meaning": "vừa mới... thì đã"},
        {"collocation": "no sooner... than", "meaning": "ngay khi... thì"},
        {"collocation": "seldom do", "meaning": "hiếm khi làm gì"},
        {"collocation": "under no circumstances", "meaning": "tuyệt đối không bao giờ"},
        {"collocation": "rarely have", "meaning": "hiếm khi từng"}
    ],
    "modal": [
        {"collocation": "must have been", "meaning": "chắc hẳn đã là"},
        {"collocation": "could have done", "meaning": "lẽ ra có thể làm"},
        {"collocation": "should have known", "meaning": "đáng lẽ nên biết"},
        {"collocation": "can't have happened", "meaning": "không thể đã xảy ra"}
    ],
    "relative clause": [
        {"collocation": "whoever", "meaning": "bất kỳ ai mà"},
        {"collocation": "whose name", "meaning": "người có tên là"},
        {"collocation": "which leads to", "meaning": "điều này dẫn đến"},
        {"collocation": "in which / whereby", "meaning": "trong đó / nhờ đó"}
    ],
    "subjunctive": [
        {"collocation": "it is crucial that", "meaning": "tối quan trọng là"},
        {"collocation": "demanded that", "meaning": "yêu cầu nghiêm ngặt"},
        {"collocation": "recommended that", "meaning": "khuyên nên làm"},
        {"collocation": "vital that", "meaning": "cực kỳ thiết yếu"}
    ],
    "gerund": [
        {"collocation": "look forward to", "meaning": "rất mong đợi"},
        {"collocation": "can't help", "meaning": "không thể không"},
        {"collocation": "be accustomed to", "meaning": "đã quen với việc"},
        {"collocation": "devote to", "meaning": "cống hiến hết mình cho"},
        {"collocation": "worth doing", "meaning": "đáng để thực hiện"}
    ],
    "comparison": [
        {"collocation": "far more important than", "meaning": "quan trọng hơn nhiều"},
        {"collocation": "by far the most", "meaning": "vượt trội hơn hẳn"},
        {"collocation": "the more... the more", "meaning": "càng... thì càng"},
        {"collocation": "twice as large as", "meaning": "gấp đôi quy mô"}
    ],
    "used to": [
        {"collocation": "used to + V-inf", "meaning": "từng làm trong quá khứ"},
        {"collocation": "no longer", "meaning": "giờ không còn nữa"},
        {"collocation": "in the past", "meaning": "trong quá khứ"}
    ]
}

def generate_grammar_collocations(structure, explanation="", example=""):
    """Sinh các từ vựng và cụm từ thường đi kèm (Collocations) với cấu trúc này"""
    s_lower = (structure or "").lower()
    e_lower = (explanation or "").lower()
    combined = f"{s_lower} {e_lower}"
    collocations = []

    # Kiểm tra theo từng nhóm từ khóa ưu tiên
    for key, coll_list in GRAMMAR_COLLOCATIONS_PRESETS.items():
        if key in combined:
            collocations.extend(coll_list)

    # Thêm điều kiện bắt if/condition
    if not collocations and ("if " in s_lower or "if +" in s_lower):
        collocations.extend(GRAMMAR_COLLOCATIONS_PRESETS["conditional"])

    # Thêm điều kiện bắt svo / subject
    if not collocations and ("svo" in s_lower or "subject" in s_lower):
        collocations.extend(GRAMMAR_COLLOCATIONS_PRESETS["svo"])

    if not collocations:
        # Tự động trích xuất các từ/cụm từ nổi bật từ ví dụ
        words = re.findall(r"[a-zA-Z']{4,}", example or "")
        filtered = [w for w in words if w.lower() not in ['this', 'that', 'with', 'from', 'have', 'were', 'been', 'will']]
        collocations = [{"collocation": w, "meaning": "từ khóa ví dụ"} for w in filtered[:5]]
        if not collocations:
            collocations = [
                {"collocation": "common phrasing", "meaning": "cách dùng thường gặp"},
                {"collocation": "adverbs of frequency", "meaning": "trạng từ đi kèm"}
            ]

    # Loại bỏ trùng lặp dựa trên collocation
    seen = set()
    unique_collocations = []
    for c in collocations:
        if isinstance(c, dict):
            name = c.get("collocation", "")
            item = c
        else:
            name = str(c)
            item = {"collocation": name, "meaning": ""}
        if name and name not in seen:
            seen.add(name)
            unique_collocations.append(item)

    return unique_collocations[:6]


def generate_grammar_quiz(grammar_obj):
    """Sinh bộ đề thi mini trắc nghiệm 5 câu hỏi chuyên biệt cho cấu trúc ngữ pháp"""
    struct = grammar_obj.structure
    exam = grammar_obj.example or "She had already left when I arrived."
    expl = grammar_obj.explanation or "Cấu trúc ngữ pháp chuẩn CEFR"
    level = grammar_obj.cefr_level or "A1"

    colls = generate_grammar_collocations(struct, expl, exam)
    best_coll = colls[0]["collocation"] if (colls and isinstance(colls[0], dict)) else (colls[0] if colls else "Specifically")

    # 5 câu hỏi trắc nghiệm chuyên sâu
    questions = [
        {
            "id": 1,
            "type": "FILL_IN_BLANK",
            "prompt": f"Chọn phương án đúng nhất để hoàn thiện câu áp dụng cấu trúc: [{struct}]",
            "sentence": f"Identify the correct formulation: '_____ {exam.lower()}'",
            "options": [
                exam,
                exam.replace("is", "are").replace("have", "has") if "is" in exam or "have" in exam else exam + " (incorrect form)",
                exam.replace("not", "").replace("didn't", "don't") if "not" in exam else "Neither " + exam,
                exam.split()[0] + " being " + " ".join(exam.split()[1:]) if len(exam.split()) > 2 else "Incomplete formulation"
            ],
            "correct_idx": 0,
            "explanation": f"Phương án A là dạng chuẩn xác của cấu trúc '{struct}'. {expl}"
        },
        {
            "id": 2,
            "type": "IDENTIFY_ERROR",
            "prompt": f"Trong cấu trúc [{struct}], yếu tố ngữ pháp nào BẮT BUỘC phải tuân thủ?",
            "sentence": f"Quy tắc chuẩn CEFR ({level}) của cấu trúc: {struct}",
            "options": [
                f"Sự hòa hợp giữa chủ ngữ và dạng thức chính xác của động từ/mệnh đề theo quy tắc '{struct}'.",
                "Chỉ sử dụng được ở thì quá khứ đơn, không bao giờ dùng ở thì hiện tại.",
                "Bắt buộc phải có trạng từ chỉ tần suất đứng ở đầu câu.",
                "Không được kết hợp với bất kỳ tính từ hoặc danh từ số nhiều nào."
            ],
            "correct_idx": 0,
            "explanation": f"Nguyên tắc cốt lõi: {expl}"
        },
        {
            "id": 3,
            "type": "CONTEXT_USAGE",
            "prompt": "Ngữ cảnh nào sau đây sử dụng cấu trúc này là TỰ NHIÊN và CHUẨN XÁC nhất?",
            "sentence": f"Vận dụng cấu trúc: '{struct}'",
            "options": [
                f"Sử dụng trong giao tiếp học thuật và văn cảnh thể hiện: {expl[:90]}...",
                "Chỉ dùng khi ra lệnh khẩn cấp, không dùng trong văn viết.",
                "Chỉ dùng trong tin nhắn viết tắt trên mạng xã hội.",
                "Chỉ áp dụng khi nói về các hành động trong tương lai xa 100 năm nữa."
            ],
            "correct_idx": 0,
            "explanation": f"Cấu trúc '{struct}' chuẩn CEFR {level} được dùng chính trong văn cảnh: {expl}"
        },
        {
            "id": 4,
            "type": "SYNTAX_TRANSFORMATION",
            "prompt": "Phương án nào sau đây diễn đạt LẠI câu mà KHÔNG làm thay đổi ý nghĩa ngữ pháp?",
            "sentence": f"Gốc: \"{exam}\"",
            "options": [
                f"It is established that: {exam}",
                f"Contrary to the fact, {exam.replace('was', 'is').replace('were', 'are')}",
                "None of the statements reflect the original tone.",
                "The meaning is completely reversed in passive form."
            ],
            "correct_idx": 0,
            "explanation": f"Phương án A giữ trọn vẹn ngữ nghĩa và cấu trúc của câu gốc."
        },
        {
            "id": 5,
            "type": "COLLOCATION_CHECK",
            "prompt": "Cụm từ / Liên từ nào dưới đây THƯỜNG XUYÊN đi kèm với cấu trúc này nhất?",
            "sentence": f"Cấu trúc khảo sát: {struct}",
            "options": [
                best_coll,
                "Randomly without rule",
                "Strictly ungrammatical particle",
                "Opposite conjunction"
            ],
            "correct_idx": 0,
            "explanation": f"Cụm từ này là collocation điển hình xuất hiện cùng cấu trúc '{struct}'."
        }
    ]

    # Trộn thứ tự đáp án ngẫu nhiên để bài test khách quan
    letters = ['A', 'B', 'C', 'D']
    for q in questions:
        orig_options = q["options"]
        correct_content = orig_options[q["correct_idx"]]
        shuffled = list(orig_options)
        random.shuffle(shuffled)
        q["correct_idx"] = shuffled.index(correct_content)
        q["question"] = q["prompt"]
        q["options"] = [{"key": letters[i] if i < 4 else str(i+1), "text": opt} for i, opt in enumerate(shuffled)]
        q["raw_options"] = shuffled

    return questions
