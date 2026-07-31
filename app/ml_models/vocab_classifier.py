import os
import joblib
import re
import pandas as pd


class VocabCEFRClassifier:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'cefr_model.pkl')
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            self.model = None

    def _extract_features(self, word):
        word = str(word).lower().strip()
        return {
            'length': len(word),
            'vowel_count': len(re.findall(r'[aeiouy]', word)),
            'consonant_count': len(re.findall(r'[^aeiouy]', word)),
            'has_suffix_tion': 1 if word.endswith('tion') else 0,
            'has_suffix_ment': 1 if word.endswith('ment') else 0,
            'has_suffix_ly': 1 if word.endswith('ly') else 0,
        }

    def predict_cefr(self, word: str) -> str:
        if not self.model:
            return "A1"  # Fallback nếu chưa train

        features = self._extract_features(word)
        df = pd.DataFrame([features])
        prediction = self.model.predict(df)[0]
        return prediction