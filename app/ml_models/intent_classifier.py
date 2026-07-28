from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC


class LocalIntentClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.classifier = LinearSVC(dual=False)
        self._train_initial_model()

    def _train_initial_model(self):
        training_texts = [
            "What does this word mean?", "Nghĩa của từ này", "Giúp tôi từ vựng",
            "Giải thích cấu trúc ngữ pháp", "Cách dùng", "Grammar check",
            "Tôi tấn công", "Mở cửa", "Bắn súng vào nó",
            "Xin chào", "Hello", "Bạn khỏe không"
        ]
        labels = [
            "ask_vocab", "ask_vocab", "ask_vocab",
            "ask_grammar", "ask_grammar", "ask_grammar",
            "story_action", "story_action", "story_action",
            "general_chat", "general_chat", "general_chat"
        ]
        X = self.vectorizer.fit_transform(training_texts)
        self.classifier.fit(X, labels)

    def predict(self, text):
        if not text: return "unknown"
        X_test = self.vectorizer.transform([text])
        return self.classifier.predict(X_test)[0]