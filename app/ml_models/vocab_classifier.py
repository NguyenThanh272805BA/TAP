import os
import joblib
import pandas as pd
from wordfreq import zipf_frequency


class VocabCEFRClassifier:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'cefr_model.pkl')
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            self.model = None

    def _extract_features(self, word):
        """
        Trích xuất đặc trưng đồng bộ với model đã train
        """
        word = str(word).lower().strip()
        zipf_score = zipf_frequency(word, 'en')

        return {
            'length': len(word),
            'zipf_frequency': zipf_score,
            'has_suffix_tion': 1 if word.endswith('tion') else 0,
            'has_suffix_ment': 1 if word.endswith('ment') else 0,
            'has_suffix_ly': 1 if word.endswith('ly') else 0,
            'has_suffix_ity': 1 if word.endswith('ity') else 0,
        }

    def predict_cefr(self, word: str) -> str:
        """
        Dự đoán cấp độ CEFR của một từ mới
        """
        if not self.model:
            return "A1"  # Fallback nếu chưa train

        features = self._extract_features(word)
        # Đảm bảo thứ tự columns khớp với lúc train
        df = pd.DataFrame([features])
        prediction = self.model.predict(df)[0]

        return prediction