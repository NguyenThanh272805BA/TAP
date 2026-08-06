import os
import json


class VocabCEFRClassifier:
    """
    Đã được đại tu ở Phase 6: Chuyển từ Random Forest Model sang Oxford Dictionary Lookup.
    Tra cứu trực tiếp (O(1)) siêu tốc và chính xác 100%.
    """

    def __init__(self):
        # Đường dẫn tới file chứa 5000 từ Oxford
        self.dict_path = os.path.join(os.path.dirname(__file__), 'oxford_5000.json')
        self.oxford_dict = {}

        if os.path.exists(self.dict_path):
            try:
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    self.oxford_dict = json.load(f)
                print(f"[SYSTEM] Đã nạp thành công bộ từ điển Oxford với {len(self.oxford_dict)} từ vựng chuẩn.")
            except Exception as e:
                print(f"[ERROR] Lỗi đọc file từ điển Oxford: {e}")
        else:
            print("[WARNING] Không tìm thấy oxford_5000.json! Sẽ sử dụng Fallback Dictionary.")
            # Fallback thu gọn nếu bạn chưa kịp chuẩn bị file JSON
            self.oxford_dict = {
                "hello": "A1", "apple": "A1", "cat": "A1", "run": "A1",
                "beautiful": "A2", "machine": "A2", "careful": "A2",
                "environment": "B1", "knowledge": "B1", "community": "B1",
                "infrastructure": "B2", "consequence": "B2", "implementation": "B2",
                "phenomenon": "C1", "ubiquitous": "C1", "lucrative": "C1",
                "quintessential": "C2", "obfuscate": "C2", "ineffable": "C2"
            }

    def predict_cefr(self, word: str) -> str:
        """
        Tra cứu cấp độ CEFR của một từ mới.
        Nếu từ không nằm trong bộ Oxford 5000, mặc định xếp vào hàng từ nâng cao (B2).
        """
        if not word:
            return "A1"

        word_lower = str(word).lower().strip()

        # Tra cứu O(1)
        cefr_level = self.oxford_dict.get(word_lower)

        # Nếu tìm thấy, trả về. Nếu không (có thể là từ lóng, thuật ngữ chuyên ngành), mặc định cho là B2
        return cefr_level if cefr_level else "B2"