import random
import re

GRAMMAR_COLLOCATIONS_PRESETS = {
    "present perfect": ["already", "just", "yet", "since 2020", "for ages", "so far", "ever", "never"],
    "past continuous": ["while", "as", "when", "at that moment", "all evening yesterday"],
    "conditional": ["if only", "provided that", "as long as", "unless", "in case of", "otherwise"],
    "passive": ["is widely regarded as", "was discovered by", "has been proven to be", "are expected to"],
    "inversion": ["hardly had... when", "no sooner... than", "seldom do", "under no circumstances", "rarely have"],
    "modal": ["must have been", "could have done", "should have known", "can't have happened"],
    "relative clause": ["whoever", "whose name", "which leads to", "in which", "whereby"],
    "subjunctive": ["it is crucial that", "demanded that he be", "recommended that she study", "vital that"],
    "gerund": ["look forward to", "can't help", "be accustomed to", "devote to", "worth doing"],
    "comparison": ["far more important than", "by far the most", "the more... the more", "twice as large as"]
}

def generate_grammar_collocations(structure, explanation="", example=""):
    """Sinh các từ vựng và cụm từ thường đi kèm (Collocations) với cấu trúc này"""
    s_lower = (structure or "").lower()
    collocations = []

    for key, coll_list in GRAMMAR_COLLOCATIONS_PRESETS.items():
        if key in s_lower:
            collocations.extend(coll_list)

    if not collocations:
        # Tự động trích xuất các từ/cụm từ nổi bật từ ví dụ
        words = re.findall(r'[a-zA-Z\']{4,}', example or "")
        collocations = words[:6] if words else ["frequently used with", "common verbs", "adverbs of frequency"]

    return list(dict.fromkeys(collocations))[:8]


def generate_grammar_quiz(grammar_obj):
    """Sinh bộ đề thi mini trắc nghiệm 5 câu hỏi chuyên biệt cho cấu trúc ngữ pháp"""
    struct = grammar_obj.structure
    exam = grammar_obj.example or "She had already left when I arrived."
    expl = grammar_obj.explanation or "Cấu trúc ngữ pháp chuẩn CEFR"
    level = grammar_obj.cefr_level or "A1"

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
                generate_grammar_collocations(struct, expl, exam)[0] if generate_grammar_collocations(struct, expl, exam) else "Specifically",
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
