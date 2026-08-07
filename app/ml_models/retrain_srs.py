import os
import sys
import joblib
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app, db
from app.models.user_vocabulary import UserVocabulary


def ebbinghaus_curve(X, base_interval, retention_multiplier, fail_penalty):
    """
    Phương trình Toán học mô phỏng Đường cong lãng quên (Ebbinghaus Forgetting Curve)
    """
    fail_count, response_time, prev_interval = X
    # Xử lý Cold-start: Nếu từ mới học (prev_interval = 0), mốc tính mặc định là 24h
    prev_interval = np.where(prev_interval == 0, 24.0, prev_interval)

    # Hàm mũ:
    # Nếu không sai (fail=0), chu kỳ sau sẽ giãn ra gấp retention_multiplier lần.
    # Nếu sai (fail > 0), bị phạt ép theo hàm mũ e^(-x) khiến thời gian ôn tập giảm gắt.
    return base_interval + (prev_interval * retention_multiplier) * np.exp(
        -fail_penalty * fail_count - 0.1 * response_time)


def retrain_srs_model():
    app = create_app()
    with app.app_context():
        records = db.session.query(
            UserVocabulary.fail_count,
            UserVocabulary.avg_response_time,
            UserVocabulary.previous_interval,
            UserVocabulary.next_review_time,
            UserVocabulary.last_tested_at
        ).all()

        data = []
        for r in records:
            if r.last_tested_at and r.next_review_time:
                delta_hours = (r.next_review_time - r.last_tested_at).total_seconds() / 3600.0
                if delta_hours > 0:
                    data.append({
                        'fail_count': r.fail_count,
                        'avg_response_time': float(r.avg_response_time),
                        'previous_interval': float(r.previous_interval or 0.0),
                        'target_hours': delta_hours
                    })

        df = pd.DataFrame(data)

        # Tham số khởi tạo SM-2 chuẩn (Base=12h, Mul=1.5, Penalty=0.8)
        optimal_params = [12.0, 1.5, 0.8]

        if len(df) >= 10:
            print(f"[*] Đang tìm tham số hàm mũ Ebbinghaus trên {len(df)} bản ghi thực tế...")
            X_train = (df['fail_count'].values, df['avg_response_time'].values, df['previous_interval'].values)
            y_train = df['target_hours'].values

            try:
                # Giới hạn (bounds) để đường cong không bị vô lý:
                # base_interval: 1h -> 24h | retention_multiplier: 1.0 -> 3.0 | fail_penalty: 0.1 -> 2.0
                popt, _ = curve_fit(ebbinghaus_curve, X_train, y_train, p0=optimal_params,
                                    bounds=([1.0, 1.0, 0.1], [24.0, 3.0, 2.0]))
                optimal_params = popt

                # Tính MAE để hiển thị Console
                y_pred = ebbinghaus_curve(X_train, *optimal_params)
                mae = np.mean(np.abs(y_train - y_pred))

                print("\n========== EBBINGHAUS SRS METRICS ==========")
                print(f"Hệ số cơ sở (Base): {optimal_params[0]:.2f}")
                print(f"Hệ số giãn chu kỳ (Multiplier): {optimal_params[1]:.2f}")
                print(f"Hệ số trừng phạt sai (Penalty): {optimal_params[2]:.2f}")
                print(f"Mean Absolute Error (MAE): {mae:.2f} hours")
                print("============================================\n")
            except Exception as e:
                print(f"[!] Lỗi nội suy Curve Fitting: {e}. Giữ nguyên tham số chuẩn.")
        else:
            print(f"[!] Chỉ có {len(df)} bản ghi (Cần tối thiểu 10). Tạm thời sử dụng hệ số Ebbinghaus chuẩn...")

        model_path = os.path.join(os.path.dirname(__file__), 'srs_model.pkl')
        # Lưu mảng 3 tham số thay vì cả 1 mô hình Machine Learning khổng lồ
        joblib.dump(optimal_params, model_path)
        print(f"[+] Đã xuất màng tham số phương trình thành công: {model_path}")


if __name__ == "__main__":
    retrain_srs_model()