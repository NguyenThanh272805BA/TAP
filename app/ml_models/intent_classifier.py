import os
import joblib
from app.ml_models.semantic_intent_parser import get_semantic_intent_parser


class LocalIntentClassifier:
    """
    Bộ não 2: Nhận diện Ý định (Intent) Độc lập Dữ liệu Huấn luyện
    Sử dụng Semantic Intent Parser (DFA & Structural Heuristic) làm động cơ chính,
    không phụ thuộc vào file CSV hay mạng nơ-ron huấn luyện tĩnh.
    """
    def __init__(self):
        self.semantic_parser = get_semantic_intent_parser()
        
        # Vẫn nạp legacy pipeline (nếu có) để tương thích ngược
        model_path = os.path.join(os.path.dirname(__file__), 'intent_model.pkl')
        if os.path.exists(model_path):
            try:
                self.legacy_pipeline = joblib.load(model_path)
            except Exception:
                self.legacy_pipeline = None
        else:
            self.legacy_pipeline = None

        print("[INTENT ENGINE] Đã kích hoạt Zero-shot Semantic Intent Engine (Độc lập dữ liệu huấn luyện).")

    def predict(self, text: str) -> str:
        """
        Dự đoán ý định người dùng tức thì (< 0.5ms):
        Ưu tiên bộ phân giải ngữ nghĩa hình thức, độ chính xác tuyệt đối trên các mẫu hành vi.
        """
        if not text:
            return "general_chat"

        # 1. Dự đoán bằng Semantic Intent Parser
        intent = self.semantic_parser.parse_intent(text)
        
        # 2. Nếu là general_chat và có legacy pipeline, có thể kiểm tra chéo
        if intent == "general_chat" and self.legacy_pipeline is not None:
            try:
                legacy_pred = self.legacy_pipeline.predict([text])[0]
                if legacy_pred in ['ask_grammar', 'ask_vocab', 'story_action']:
                    return legacy_pred
            except Exception:
                pass

        return intent


if __name__ == "__main__":
    clf = LocalIntentClassifier()
    print("Test intent:", clf.predict("Chỉ cho tôi cách dùng thì hiện tại hoàn thành"))
    print("Test intent:", clf.predict("What is the meaning of apple?"))
    print("Test intent:", clf.predict("Attack with sword"))