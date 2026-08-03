import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

class SmartSRS:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'srs_model.pkl')
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            self.is_mock = False
        else:
            # Mô hình khởi động lạnh (Cold-start) nếu hệ thống chưa có data
            self.model = RandomForestRegressor(n_estimators=50, random_state=42)
            self._mock_train_model()
            self.is_mock = True

    def _mock_train_model(self):
        """
        Khởi động lạnh dựa trên logic Ebbinghaus (SM-2).
        Features: [fail_count, response_time, previous_interval_hours]
        """
        X_train = np.array([
            [0, 1.5, 24.0],  # Không sai, phản xạ nhanh, review trước là 1 ngày -> next = 3 ngày
            [3, 5.0, 72.0],  # Sai nhiều, phản xạ chậm -> next = giảm xuống 12h
            [1, 2.5, 12.0],  # Hơi vấp -> next = 24h
            [5, 4.0, 48.0],  # Sai quá nhiều -> next = 4h
            [0, 1.0, 0.0]    # Lần đầu học (previous_interval = 0) -> next = 24h
        ])
        y_train = np.array([72.0, 12.0, 24.0, 4.0, 24.0])
        self.model.fit(X_train, y_train)

    def predict_next_review(self, fail_count, response_time, previous_interval):
        features = np.array([[fail_count, response_time, previous_interval]])
        hours_interval = self.model.predict(features)[0]

        # Clip giới hạn từ 30 phút đến 6 tháng (Ngăn AI dự đoán lãng quên vô lý)
        hours_interval = max(0.5, min(hours_interval, 24 * 180))
        next_time = datetime.now() + timedelta(hours=hours_interval)
        return next_time, hours_interval