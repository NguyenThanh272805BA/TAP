import spacy


class SpacyNER:
    def __init__(self):
        try:
            # Load model tiếng Anh cỡ nhỏ để trích xuất các keyword tiếng Anh từ câu chat
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("[HỆ THỐNG] Không tìm thấy model spaCy. Đang tự động tải 'en_core_web_sm'...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def extract_entity(self, text, intent):
        """
        Trích xuất Entity (Target) từ câu chat của User dựa vào Intent
        """
        if not text:
            return None

        doc = self.nlp(text)

        # Chiến thuật 1: Lấy các cụm danh từ (Noun Chunks) hoặc Danh từ riêng (PROPN)
        # Vì user Việt Nam thường gõ tên ngữ pháp/từ vựng bằng tiếng Anh, model EN sẽ nhận diện chúng thành Noun/PROPN.
        entities = []

        # Nếu là ngữ pháp (Thường gồm 2-3 chữ như "Past Simple", "Relative Clause")
        if intent == 'ask_grammar':
            # Quét các từ viết hoa chữ cái đầu hoặc ghép cụm danh từ
            for chunk in doc.noun_chunks:
                # Loại bỏ các đại từ xưng hô linh tinh
                if chunk.text.lower() not in ['i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'my', 'your']:
                    entities.append(chunk.text)

            # Fallback: Lấy các từ tiếng Anh (is_ascii) nếu câu quá ngắn
            if not entities:
                english_words = [token.text for token in doc if token.is_alpha and token.is_ascii]
                if english_words:
                    entities.append(" ".join(english_words))

        # Nếu là từ vựng (Thường là 1 từ hoặc cụm từ ngắn)
        elif intent == 'ask_vocab':
            for token in doc:
                # Lọc ra các từ đóng vai trò cốt lõi và không phải stop words
                if token.is_alpha and token.is_ascii and not token.is_stop:
                    entities.append(token.text)

        # Trả về chuỗi dài nhất tìm được (có khả năng là tên Cấu trúc/Từ vựng nhất)
        if entities:
            return max(entities, key=len).strip()

        return None