import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta


class SmartSRS:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self._mock_train_model()

    def _mock_train_model(self):
        # Features: [fail_count, avg_response_time_seconds, word_length]
        # Target Y: hours_until_next_review
        X_train = np.array([
            [0, 1.5, 5],  # Nhanh, dễ -> ôn sau 72h
            [3, 5.0, 10],  # Sai nhiều, chậm, khó -> ôn sau 2h
            [1, 2.5, 4],  # Sai 1 lần, trung bình -> ôn sau 24h
            [5, 4.0, 7]  # Sai cực nhiều -> ôn sau 0.5h
        ])
        y_train = np.array([72.0, 2.0, 24.0, 0.5])
        self.model.fit(X_train, y_train)

    def predict_next_review(self, fail_count, response_time, word_length):
        features = np.array([[fail_count, response_time, word_length]])
        hours_interval = self.model.predict(features)[0]

        # Clip giới hạn từ 30 phút đến 30 ngày
        hours_interval = max(0.5, min(hours_interval, 24 * 30))
        next_time = datetime.now() + timedelta(hours=hours_interval)
        return next_time, hours_interval