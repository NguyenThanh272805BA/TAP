# app/ml_models/intent_classifier.py
import os
import joblib

class LocalIntentClassifier:
    """
    Bộ não 2: Nhận diện Ý định (Intent) bằng Mạng Nơ-ron Đa tầng (MLP)
    """
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'intent_model.pkl')
        if os.path.exists(model_path):
            self.pipeline = joblib.load(model_path)
            print("[INTENT ENGINE] Đã nạp thành công Mạng Nơ-ron Intent Classifier.")
        else:
            self.pipeline = None
            print("[WARNING] Chưa tìm thấy intent_model.pkl. Hệ thống sẽ mù phương hướng. Hãy chạy train_intent.py!")

    def predict(self, text: str) -> str:
        if not text or not self.pipeline:
            return "unknown"
        return self.pipeline.predict([text])[0]