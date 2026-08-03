import re


class RuleBasedNER:
    def __init__(self):
        # Không cần load model AI nặng nề của spaCy nữa, khởi tạo tức thì (O(1))
        pass

    def extract_entity(self, text, intent):
        """
        Trích xuất Entity (Target) từ câu chat của User bằng Regex & Rule-based
        """
        if not text:
            return None

        # CHIẾN THUẬT 1: Tìm cụm từ nằm trong ngoặc kép hoặc ngoặc đơn (Ưu tiên cao nhất)
        # VD: Giải thích cho tôi cấu trúc "Past Simple"
        quotes_pattern = r'["\']([^"\']+)["\']'
        matches = re.findall(quotes_pattern, text)
        if matches:
            return max(matches, key=len).strip()

        # CHIẾN THUẬT 2: Dựa vào từ khóa tiếng Việt
        text_lower = text.lower()
        if intent == 'ask_grammar':
            # Tìm chữ nằm sau "cấu trúc", "ngữ pháp", "mẫu câu"
            match = re.search(r'(cấu trúc|ngữ pháp|mẫu câu)\s+([a-zA-Z\s]+)', text_lower)
            if match:
                entity = match.group(2).strip()
                if entity:
                    return entity

        elif intent == 'ask_vocab':
            # Tìm chữ nằm sau "từ", "chữ", "từ vựng", "nghĩa của"
            match = re.search(r'(từ|chữ|từ vựng|nghĩa của)\s+([a-zA-Z\s]+)', text_lower)
            if match:
                entity = match.group(2).strip()
                words = entity.split()
                if words:
                    # Giới hạn chỉ lấy 1-2 từ tiếng Anh đầu tiên sau từ khóa
                    return " ".join(words[:2])

                    # CHIẾN THUẬT 3: Fallback - Lấy từ tiếng Anh dài nhất trong câu (Loại trừ Stopwords)
        english_words = re.findall(r'\b[a-zA-Z]+\b', text)
        stopwords = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'how', 'is', 'am', 'are', 'a', 'an', 'the'}
        filtered_words = [w for w in english_words if w.lower() not in stopwords]

        if filtered_words:
            return max(filtered_words, key=len)

        return None