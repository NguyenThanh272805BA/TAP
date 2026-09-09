import os
import math
import sys
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class SmartSRS:
    """
    Bộ não 3: FSRS (Free Spaced Repetition Scheduler) & Adaptive Memory Engine
    Thuật toán giãn cách ôn tập hiện đại dựa trên mô hình ba biến trạng thái nhận thức:
    - D (Difficulty - Độ khó [1, 10])
    - S (Stability - Độ bền vững trí nhớ [giờ])
    - R (Retrievability - Xác suất nhớ lại thành công)
    Kết hợp cơ chế Multi-Armed Bandit để chọn lọc nội dung học tối ưu, không phụ thuộc vào data huấn luyện tĩnh.
    """

    def __init__(self, target_retention: float = 0.90):
        self.target_retention = target_retention
        # Hệ số cơ bản của thuật toán FSRS
        self.w = [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61]

    def calculate_difficulty(self, fail_count: int, response_time: float) -> float:
        """
        Ước lượng độ khó D trong khoảng [1.0, 10.0]:
        Càng trả lời chậm (> 4s) hoặc càng sai nhiều thì D càng tiến sát 10.
        """
        # Khởi điểm độ khó trung bình = 4.5
        d = 4.5 + (1.2 * fail_count) + (0.15 * max(0.0, response_time - 3.0))
        return float(np.clip(d, 1.0, 10.0))

    def calculate_retrievability(self, elapsed_hours: float, stability_hours: float) -> float:
        """
        Xác suất nhớ lại R tại thời điểm trôi qua t với độ bền vững S:
        R(t) = exp( - ln(10) * (t / (9 * S)) ) ~ (1 + t / (9 * S))^(-1)
        """
        if stability_hours <= 0:
            return 0.0
        # Dạng chuẩn hàm mũ suy giảm trí nhớ
        return float(math.exp(- (elapsed_hours / max(1.0, stability_hours)) * math.log(1.0 / self.target_retention)))

    def predict_next_review(self, fail_count: int, response_time: float, previous_interval: float) -> Tuple[datetime, float]:
        """
        Tính toán khoảng thời gian chu kỳ ôn tập tiếp theo:
        Tương thích ngược 100% với giao diện:
        next_time, new_interval = srs_engine.predict_next_review(fail_count, response_time, prev_int)
        """
        prev_int = 24.0 if previous_interval is None or previous_interval <= 0 else float(previous_interval)
        d = self.calculate_difficulty(fail_count, response_time)

        if fail_count > 0:
            # 1. TRƯỜNG HỢP TRẢ LỜI SAI: Trừng phạt trí nhớ (Memory Lapse / Reset)
            # Rút ngắn chu kỳ ôn tập xuống đáng kể để học viên ôn ngay
            lapse_factor = 1.0 / (1.5 + 0.8 * fail_count)
            hours_interval = max(0.5, prev_int * lapse_factor)
        else:
            # 2. TRƯỜNG HỢP TRẢ LỜI ĐÚNG:
            # Tốc độ phản xạ: response_time < 3s là thuộc nhuần nhuyễn, > 5s là còn do dự
            speed_bonus = max(0.8, 2.0 - (response_time / 5.0))
            
            # Hệ số giãn nở chu kỳ FSRS theo độ khó D: Từ càng dễ thì khoảng cách càng kéo dài
            stability_factor = 1.0 + math.exp(1.6 - 0.16 * d) * speed_bonus
            
            hours_interval = prev_int * stability_factor

        # 3. Giới hạn an toàn (Boundary Clipping)
        # Tối thiểu 30 phút, tối đa 180 ngày (4320 giờ)
        hours_interval = max(0.5, min(float(hours_interval), 24.0 * 180.0))
        hours_interval = round(hours_interval, 2)

        next_time = datetime.now() + timedelta(hours=hours_interval)
        return next_time, hours_interval

    def bandit_select_review_items(self, user_items: List[Dict], top_k: int = 4) -> List[Dict]:
        """
        Thuật toán Multi-Armed Bandit (Thompson Sampling / Upper Confidence Bound):
        Tự động cân bằng giữa:
        - Exploitation (Từ vựng sắp rơi vào vùng quên: R < 0.85)
        - Exploration (Từ vựng có độ bất định cao hoặc chưa được củng cố)
        """
        now = datetime.now()
        scored_items = []

        for item in user_items:
            next_review = item.get("next_review_time")
            prev_interval = item.get("previous_interval", 24.0)
            
            if next_review is None:
                # Từ mới tinh -> Ưu tiên cao
                urgency_score = 2.0
            else:
                # Tính số giờ đã trôi qua kể từ thời điểm ôn tập dự kiến
                if isinstance(next_review, str):
                    try:
                        next_review = datetime.fromisoformat(next_review)
                    except Exception:
                        next_review = now

                elapsed = (now - next_review).total_seconds() / 3600.0
                # Nếu đã quá hạn (elapsed > 0) -> Điểm khẩn cấp cao
                urgency_score = 1.0 + (elapsed / max(1.0, prev_interval))
            
            # Thêm nhiễu ngẫu nhiên khám phá (Thompson Exploration perturbation)
            exploration_noise = np.random.beta(2, 5) * 0.3
            final_priority = urgency_score + exploration_noise

            scored_items.append((final_priority, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]


if __name__ == "__main__":
    srs = SmartSRS()

    print("=== KIỂM THỬ THUẬT TOÁN FSRS SMART SRS ===")
    # Trường hợp 1: Trả lời đúng cực nhanh (< 2s), chưa từng sai
    dt1, int1 = srs.predict_next_review(fail_count=0, response_time=1.5, previous_interval=24.0)
    print(f"[ĐÚNG NHANH] Khoảng cách chu kỳ tiếp theo: {int1:.2f} giờ (~{int1/24:.1f} ngày)")

    # Trường hợp 2: Trả lời đúng nhưng phân vân lâu (7.5s)
    dt2, int2 = srs.predict_next_review(fail_count=0, response_time=7.5, previous_interval=24.0)
    print(f"[ĐÚNG CHẬM ] Khoảng cách chu kỳ tiếp theo: {int2:.2f} giờ (~{int2/24:.1f} ngày)")

    # Trường hợp 3: Trả lời sai 2 lần
    dt3, int3 = srs.predict_next_review(fail_count=2, response_time=4.0, previous_interval=48.0)
    print(f"[SAI 2 LẦN ] Rút ngắn chu kỳ khẩn cấp về: {int3:.2f} giờ")