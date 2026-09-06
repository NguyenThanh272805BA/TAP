import numpy as np
import os
import joblib
from datetime import datetime, timedelta


class SmartSRS:
    """
    Bộ não 3: Dự đoán chu kỳ ôn tập bằng Toán học hàm mũ (Ebbinghaus Curve)
    """

    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'srs_model.pkl')
        if os.path.exists(model_path):
            self.params = joblib.load(model_path)
            self.is_mock = False
        else:
            self.params = [12.0, 1.5, 0.8]
            self.is_mock = True

    def predict_next_review(self, fail_count: int, response_time: float, previous_interval: float):
        base_interval, retention_multiplier, fail_penalty = self.params

        # Tránh lỗi logarit/mũ khi previous_interval = 0
        prev_int = 24.0 if previous_interval == 0 else previous_interval

        # Phương trình lãng quên Ebbinghaus
        hours_interval = base_interval + (prev_int * retention_multiplier) * np.exp(
            -fail_penalty * fail_count - 0.1 * response_time)

        # Clip ranh giới: Tối thiểu 30 phút, tối đa 6 tháng để bảo vệ AI khỏi việc dự đoán cực đoan
        hours_interval = max(0.5, min(hours_interval, 24 * 180))

        next_time = datetime.now() + timedelta(hours=hours_interval)
        return next_time, hours_interval