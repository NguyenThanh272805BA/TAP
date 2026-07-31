import os
import joblib
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from app import create_app, db
from app.models.user_vocabulary import UserVocabulary
from app.models.vocabulary import Vocabulary

def retrain_srs_model():
    """Job lấy data thực tế từ DB để train lại thuật toán Gợi ý chu kỳ học"""
    app = create_app()
    with app.app_context():
        # Query join 2 bảng để lấy đặc trưng
        records = db.session.query(
            UserVocabulary.fail_count,
            UserVocabulary.avg_response_time,
            Vocabulary.word,
            UserVocabulary.next_review_time,
            UserVocabulary.last_tested_at
        ).join(Vocabulary, UserVocabulary.vocab_id == Vocabulary.id).all()

        if len(records) < 10:
            print("[!] Số lượng bản ghi quá ít (Cold-start). Cần tối thiểu 10 lượt chơi để trigger retrain!")
            return

        data = []
        for r in records:
            if r.last_tested_at and r.next_review_time:
                # Tính nhãn Y: Thực tế user mất bao nhiêu giờ để hệ thống review lại
                delta_hours = (r.next_review_time - r.last_tested_at).total_seconds() / 3600.0
                if delta_hours > 0:
                    data.append({
                        'fail_count': r.fail_count,
                        'avg_response_time': float(r.avg_response_time),
                        'word_length': len(r.word),
                        'target_hours': delta_hours
                    })

        df = pd.DataFrame(data)
        if df.empty:
            print("Không có dữ liệu hợp lệ để train.")
            return

        X = df[['fail_count', 'avg_response_time', 'word_length']]
        y = df['target_hours']

        print(f"[*] Đang Retrain thuật toán SRS trên {len(df)} bản ghi thực tế từ Database...")
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        print("\n========== SRS REGRESSOR METRICS ==========")
        y_pred = model.predict(X)
        print(f"Mean Absolute Error (MAE): {mean_absolute_error(y, y_pred):.2f} hours")
        print(f"Mean Squared Error (MSE): {mean_squared_error(y, y_pred):.2f}")
        print("===========================================\n")

        model_path = os.path.join(os.path.dirname(__file__), 'srs_model.pkl')
        joblib.dump(model, model_path)
        print(f"[+] Đã ghi đè mô hình SRS mới thành công: {model_path}")

if __name__ == "__main__":
    retrain_srs_model()