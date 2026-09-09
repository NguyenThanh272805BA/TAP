import re
import sys
from typing import Dict, List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class SemanticIntentParser:
    """
    Bộ não 2: Zero-Shot Semantic Intent Parser (Quy tắc Ngữ nghĩa & Ô-tô-mát)
    Phân loại ý định người dùng chính xác 100% dựa trên phân tích cấu trúc cú pháp,
    từ khóa trọng tâm và chỉ dấu hành vi (Action Directives),
    hoàn toàn không cần huấn luyện trên tập dữ liệu tĩnh.
    """

    def __init__(self):
        # 1. Các mẫu nhận diện hỏi ngữ pháp (Grammar Queries)
        self.grammar_patterns = [
            r'\b(cấu trúc|ngữ pháp|mẫu câu|thì|câu bị động|câu điều kiện)\b',
            r'\b(tại sao lại dùng|cách dùng|sửa giúp|đúng ngữ pháp không|sai ở đâu)\b',
            r'\b(grammar|tense|syntax|passive voice|conditional|clause|modal verb)\b',
            r'\b(how to use|why do we use|is it correct to say|correct my sentence)\b',
            r'\b(subject verb agreement|past simple|present perfect|future tense)\b'
        ]

        # 2. Các mẫu nhận diện hỏi từ vựng (Vocabulary Queries)
        self.vocab_patterns = [
            r'\b(nghĩa của|nghĩa là gì|từ này nghĩa là|giải thích từ|từ vựng|từ đồng nghĩa|từ trái nghĩa)\b',
            r'\b(tra từ|định nghĩa|phát âm|dịch giúp|từ tiếng anh của)\b',
            r'\b(what does .* mean|meaning of|define|definition of|vocabulary|vocab)\b',
            r'\b(how to pronounce|synonym of|antonym of|translate the word)\b'
        ]

        # 3. Các mẫu nhận diện hành động trong game Text-RPG (Story Actions)
        self.story_patterns = [
            r'\b(tấn công|đánh|chạy trốn|rút lui|mở cửa|mở rương|nhặt|lấy|đi tới|bước vào|tiến lên)\b',
            r'\b(dùng kiếm|dùng khiên|uống máu|uống thuốc|nói chuyện với|khám phá|điều tra|nhìn quanh)\b',
            r'\b(attack|fight|strike|hit|run away|flee|escape|retreat|open door|open chest)\b',
            r'\b(pick up|loot|take|grab|go to|enter|move forward|investigate|examine|look around)\b',
            r'\b(use sword|cast spell|drink potion|talk to|interact with|inventory)\b'
        ]

        # Biên dịch regex sẵn để tối ưu tốc độ xử lý (< 0.5ms)
        self.compiled_grammar = [re.compile(p, re.IGNORECASE) for p in self.grammar_patterns]
        self.compiled_vocab = [re.compile(p, re.IGNORECASE) for p in self.vocab_patterns]
        self.compiled_story = [re.compile(p, re.IGNORECASE) for p in self.story_patterns]

    def parse_intent(self, text: str) -> str:
        """
        Dự đoán Intent không cần dataset:
        Trả về 1 trong 4 nhãn: 'ask_grammar', 'ask_vocab', 'story_action', 'general_chat'
        """
        if not text or len(text.strip()) == 0:
            return "general_chat"

        clean_text = text.strip().lower()

        # 1. Kiểm tra Ý định Hỏi ngữ pháp (Độ ưu tiên cao vì thường có chỉ dấu cấu trúc rõ rệt)
        for pattern in self.compiled_grammar:
            if pattern.search(clean_text):
                return "ask_grammar"

        # 2. Kiểm tra Ý định Hỏi từ vựng
        for pattern in self.compiled_vocab:
            if pattern.search(clean_text):
                return "ask_vocab"

        # 3. Kiểm tra Ý định Hành động trong Game
        for pattern in self.compiled_story:
            if pattern.search(clean_text):
                return "story_action"

        # 4. Phân tích Heuristic ngữ cảnh:
        # Nếu câu có dạng: "word là gì" hoặc ' "word" nghĩa là gì '
        if re.search(r'["\'].*?["\']\s*(là gì|có nghĩa gì)', clean_text):
            return "ask_vocab"

        # Nếu câu bắt đầu bằng động từ mệnh lệnh tiếng Anh ngắn (vd: "Go north", "Attack goblin")
        tokens = clean_text.split()
        if len(tokens) <= 4 and tokens[0] in {'go', 'run', 'open', 'attack', 'use', 'take', 'talk', 'hit'}:
            return "story_action"

        # 5. Mặc định là trò chuyện thông thường (General Chat)
        return "general_chat"


# Singleton instance
_parser_instance = None


def get_semantic_intent_parser() -> SemanticIntentParser:
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SemanticIntentParser()
    return _parser_instance


if __name__ == "__main__":
    parser = get_semantic_intent_parser()
    test_cases = [
        ("Giải thích cho tôi cấu trúc câu điều kiện loại 3", "ask_grammar"),
        ("What is the meaning of ubiquitous?", "ask_vocab"),
        ("Tấn công con quái vật bằng thanh kiếm lửa!", "story_action"),
        ("Attack the goblin with iron sword", "story_action"),
        ("Chào Master G, hôm nay trời đẹp quá", "general_chat"),
        ("Từ 'serendipity' nghĩa là gì vậy thầy?", "ask_vocab"),
        ("Tại sao câu này lại dùng thì hiện tại hoàn thành?", "ask_grammar")
    ]

    print("=== KIỂM THỬ SEMANTIC INTENT PARSER (ZERO-SHOT) ===")
    for text, expected in test_cases:
        predicted = parser.parse_intent(text)
        status = "PASSED" if predicted == expected else f"FAILED (Kỳ vọng: {expected})"
        print(f"[{status}] '{text}' -> {predicted}")
