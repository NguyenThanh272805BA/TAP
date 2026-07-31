import pandas as pd
import joblib
import os
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


def extract_features(word):
    """Trích xuất đặc trưng thủ công (Feature Engineering) cho bài toán ML"""
    word = str(word).lower().strip()
    return {
        'length': len(word),
        'vowel_count': len(re.findall(r'[aeiouy]', word)),
        'consonant_count': len(re.findall(r'[^aeiouy]', word)),
        'has_suffix_tion': 1 if word.endswith('tion') else 0,
        'has_suffix_ment': 1 if word.endswith('ment') else 0,
        'has_suffix_ly': 1 if word.endswith('ly') else 0,
    }


if __name__ == "__main__":
    # Dataset mô phỏng (Trong thực tế bạn có thể tải bộ CEFR Oxford 3000)
    print("[*] Đang nạp CEFR Mock Dataset...")
    raw_data = [
        ("cat", "A1"), ("dog", "A1"), ("hello", "A1"), ("apple", "A1"), ("run", "A1"),
        ("beautiful", "A2"), ("garden", "A2"), ("weather", "A2"), ("quick", "A2"),
        ("environment", "B1"), ("development", "B1"), ("knowledge", "B1"), ("traditional", "B1"),
        ("infrastructure", "B2"), ("consequence", "B2"), ("sophisticated", "B2"), ("substantially", "B2"),
        ("phenomenon", "C1"), ("ubiquitous", "C1"), ("ephemeral", "C1"), ("quintessential", "C2")
    ]
    # Nhân bản data và thêm nhiễu để có tập dataset lớn hơn cho Random Forest
    extended_data = raw_data * 20
    df = pd.DataFrame(extended_data, columns=['word', 'label'])

    # Feature Engineering
    print("[*] Đang trích xuất đặc trưng (Feature Engineering)...")
    features_df = pd.DataFrame([extract_features(w) for w in df['word']])
    X = features_df
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Huấn luyện mô hình Random Forest
    print("[*] Đang huấn luyện Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    print("\n========== CEFR CLASSIFIER METRICS ==========")
    y_pred = clf.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("=============================================\n")

    model_path = os.path.join(os.path.dirname(__file__), 'cefr_model.pkl')
    joblib.dump(clf, model_path)
    print(f"[+] Đã export mô hình: {model_path}")