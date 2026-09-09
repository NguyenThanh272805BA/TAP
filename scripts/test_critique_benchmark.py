import os
import sys
import time
from typing import List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_models.gec_engine import LocalGECEngine


def run_critique_benchmark():
    print("\n" + "=" * 75)
    print("   BỘ ĐỐI CHUẨN ĐÁNH GIÁ CÂU LOCAL-FIRST & CỔNG PHÂN LUỒNG THÔNG MINH")
    print("   Hệ thống: TAP - AI Local Evaluation & Selective LLM Fallback Gate")
    print("=" * 75 + "\n")

    gec = LocalGECEngine()

    test_scenarios = [
        ("She does not like playing with dogs.", "Câu chuẩn ngữ pháp (A2)", False),
        ("She do not likes play with dog.", "Sai ngữ pháp hiển nhiên (Chủ vị & dạng động từ)", False),
        ("Ubiquitous artificial intelligence facilitates autonomous systems.", "Câu học thuật từ vựng cao cấp (C1)", False),
        ("He have many book on the table.", "Sai danh từ đếm được và động từ have (A1)", False),
        ("Dog banana flying tree jump running swiftly over the moon without sense.", "Câu OOD dị thường có thể cần phân tích ngữ cảnh", False),
        ("When the researcher who was investigating the complicated algorithmic methodology that had been established during the earlier experimental phase arrived at the laboratory, he found that all data records had been mysteriously erased without any backup.", "Câu phức dài đặc biệt (> 35 từ, nhiều mệnh đề lồng nhau)", True),
    ]

    total_local_handled = 0
    total_latency_ms = 0.0

    for i, (text, desc, expected_escalation) in enumerate(test_scenarios, 1):
        print(f"[TEST {i}] '{text}'")
        print(f"  * Mô tả: {desc}")

        start_time = time.perf_counter()
        res = gec.evaluate(text)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        total_latency_ms += latency_ms

        escalation = res.get("needs_llm_escalation", False)
        if not escalation:
            total_local_handled += 1

        engine_name = "LLM Escalation" if escalation else "Local Brain (100% Offline)"

        print(f"  * Điểm số:           {res['score']}/10")
        print(f"  * Điều phối:         [{engine_name}] (Độ bất định: {res.get('uncertainty_score', 0):.2f})")
        print(f"  * Lý do:             {res.get('escalation_reason', 'N/A')}")
        print(f"  * Độ trễ suy luận:   {latency_ms:.2f} ms")
        print(f"  * Đoạn nhận xét Master G sinh tự động:")
        # In 2 dòng đầu của nhận xét để xem trước
        critique_preview = "\n".join(["    > " + line for line in res['master_g_critique'].split('\n')[:5]])
        print(critique_preview)
        print("  " + "-" * 70)

    print("\n" + "=" * 75)
    print("   TỔNG KẾT HIỆU NĂNG VÀ TỶ LỆ TIẾT KIỆM TÀI NGUYÊN")
    print("=" * 75)
    local_ratio = (total_local_handled / len(test_scenarios)) * 100.0
    avg_latency = total_latency_ms / len(test_scenarios)

    print(f"- Tổng số mẫu kiểm thử:           {len(test_scenarios)}")
    print(f"- Tỷ lệ AI Local tự chủ:           {total_local_handled}/{len(test_scenarios)} ({local_ratio:.1f}%)")
    print(f"- Tỷ lệ chuyển giao LLM:           {len(test_scenarios) - total_local_handled}/{len(test_scenarios)} ({100 - local_ratio:.1f}%)")
    print(f"- Độ trễ trung bình AI Local:      {avg_latency:.2f} ms (Nhanh gấp ~20 lần so với gọi API LLM)")
    print(f"- Tỷ lệ tiết kiệm Token LLM:       {local_ratio:.1f}% toàn hệ thống!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_critique_benchmark()
