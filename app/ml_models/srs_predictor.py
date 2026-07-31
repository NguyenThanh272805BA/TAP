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
        """Khởi động lạnh cho người dùng đầu tiên (Base Heuristics)"""
        X_train = np.array([[0, 1.5, 5], [3, 5.0, 10], [1, 2.5, 4], [5, 4.0, 7]])
        y_train = np.array([72.0, 2.0, 24.0, 0.5])
        self.model.fit(X_train, y_train)

    def predict_next_review(self, fail_count, response_time, word_length):
        features = np.array([[fail_count, response_time, word_length]])
        hours_interval = self.model.predict(features)[0]

        # Clip giới hạn từ 30 phút đến 30 ngày (Ngăn AI dự đoán vô lý)
        hours_interval = max(0.5, min(hours_interval, 24 * 30))
        next_time = datetime.now() + timedelta(hours=hours_interval)
        return next_time, hours_interval