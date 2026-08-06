# app/ml_models/vocab_classifier.py
import os
import json
from wordfreq import zipf_frequency

class VocabCEFRClassifier:
    """
    Bộ não 4: Hybrid CEFR Predictor
    Kết hợp tra cứu O(1) Oxford Dictionary và thuật toán Zipf Frequency.
    """
    def __init__(self):
        # Đường dẫn tới file chứa 5000 từ Oxford (nếu có)
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
            print("[WARNING] Không tìm thấy oxford_5000.json! Hệ thống sẽ chuyển sang dùng 100% Thuật toán Zipf.")

    def predict_cefr(self, word: str) -> str:
        """
        Dự đoán cấp độ CEFR cho một từ vựng bất kỳ.
        """
        if not word:
            return "A1"

        word_lower = str(word).lower().strip()

        # Bước 1: Tra cứu O(1) siêu tốc
        if word_lower in self.oxford_dict:
            return self.oxford_dict[word_lower]

        # Bước 2: Hybrid Fallback - Nếu là từ lóng, cụm từ hoặc từ ngoài từ điển
        # zipf_frequency trả về dải điểm logarit cơ số 10 (thường từ 1.0 đến 8.0)
        # Điểm càng cao -> Từ càng phổ biến (VD: 'the' ~ 8.0, 'apple' ~ 5.0)
        zipf_score = zipf_frequency(word_lower, 'en')

        if zipf_score == 0.0:
            # Từ không tồn tại trong corpus (từ lóng mới, sai chính tả nặng)
            return "C2" 
        elif zipf_score >= 5.5:
            # Rất phổ biến
            return "A2" 
        elif zipf_score >= 4.0:
            # Phổ biến trung bình
            return "B2" 
        else:
            # Từ hiếm gặp
            return "C1" 

# --- TEST NHANH ---
if __name__ == "__main__":
    classifier = VocabCEFRClassifier()
    test_words = ["apple", "ubiquitous", "skibidi", "infrastructure"]
    for w in test_words:
        print(f"Từ: {w:15} -> Mức độ CEFR: {classifier.predict_cefr(w)}")