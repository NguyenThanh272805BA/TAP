import os
import joblib


class LocalIntentClassifier:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'intent_model.pkl')
        if os.path.exists(model_path):
            self.pipeline = joblib.load(model_path)
        else:
            self.pipeline = None
            print("[CẢNH BÁO] Chưa tìm thấy intent_model.pkl. Hãy chạy file train_intent.py trước!")

    def predict(self, text):
        if not text or not self.pipeline:
            return "unknown"
        return self.pipeline.predict([text])[0]