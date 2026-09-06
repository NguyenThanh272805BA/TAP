import os
import sys
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.utils.gemini_helper import evaluate_english_skill

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LocalGECEngine:
    """
    Bộ não 1: Grammar Error Correction (GEC) - Hybrid Transformer
    Phiên bản Transformer kết hợp Fallback LLM.
    """

    # Fallback 0.55 (Mức giới hạn toán học của phân loại nhị phân là 0.5)
    def __init__(self, model_path="app/ml_models/saved_models/gec_transformer", fallback_threshold=0.55, lazy=False):
        self.fallback_threshold = fallback_threshold
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.is_active = False
        self.is_quantized = False
        self.device = torch.device("cpu") # Quantized INT8 chạy tối ưu trên CPU

        if not lazy:
            self._ensure_loaded()

    def _ensure_loaded(self):
        """Lazy loading: Chỉ tải mô hình vào RAM khi có lượt gọi đầu tiên để tiết kiệm tài nguyên."""
        if self.is_active:
            return True

        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Không tìm thấy thư mục mô hình tại {self.model_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # Ưu tiên nạp bản lượng tử hóa siêu nhẹ (INT8) nếu có
            quantized_file = os.path.join(self.model_path, "quantized_model.pt")
            if os.path.exists(quantized_file):
                print(f"[GEC ENGINE] Phát hiện bản nén INT8. Đang nạp {quantized_file} ...")
                self.model = torch.load(quantized_file, map_location=self.device, weights_only=False)
                self.is_quantized = True
                print("[GEC ENGINE] Đã nạp thành công Local Transformer GEC (Quantized INT8 - Tối ưu 2x CPU Latency).")
            else:
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                # Đẩy model lên GPU nếu có và là model thường
                if torch.cuda.is_available():
                    self.device = torch.device("cuda")
                self.model.to(self.device)
                print("[GEC ENGINE] Đã nạp thành công Local Transformer GEC (FP32).")

            self.model.eval()
            self.is_active = True
            return True

        except Exception as e:
            print(f"[GEC ENGINE] Cảnh báo lỗi khởi tạo Transformer: {e}. Hệ thống sẽ phụ thuộc 100% vào LLM.")
            self.is_active = False
            return False

    def evaluate(self, text: str) -> dict:
        """
        Dự đoán ngữ pháp. Trả về Score (Thang 10) và Feedback.
        Kích hoạt Fallback LLM nếu Confidence Score quá thấp (Dưới 0.55).
        """
        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "feedback": "Ngươi định lừa Master G bằng một khoảng trống tĩnh lặng à? Nhập chữ vào!"
            }

        if not self.is_active:
            if not self._ensure_loaded():
                return self._trigger_fallback(text, "Local Brain Offline")

        # Tiền xử lý văn bản
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            # Chuyển đổi Logits thành phân phối xác suất
            probs = torch.softmax(logits, dim=1).squeeze().tolist()

        # probs[0]: Unacceptable (Sai ngữ pháp), probs[1]: Acceptable (Đúng ngữ pháp)
        prob_unacceptable, prob_acceptable = probs[0], probs[1]
        confidence = max(prob_unacceptable, prob_acceptable)

        # ---------------------------------------------------------
        # HYBRID FALLBACK: Gọi LLM nếu Local Model cực kỳ thiếu tự tin ( < 0.55)
        # ---------------------------------------------------------
        if confidence < self.fallback_threshold:
            print(
                f"[GEC ENGINE] Confidence ({confidence:.2f}) < Threshold ({self.fallback_threshold}). Kích hoạt Fallback...")
            return self._trigger_fallback(text, "Out of Distribution (OOD)")

        # ---------------------------------------------------------
        # XỬ LÝ NỘI BỘ (LOCAL BRAIN 100%)
        # ---------------------------------------------------------
        score = max(0.0, round(prob_acceptable * 10, 1))

        if score >= 8.0:
            feedback = f"[Điểm Tự Tin: {confidence:.2f}] Tuyệt vời! Ngữ pháp rất mượt mà. Phong độ ngạo nghễ!"
        elif 5.0 <= score < 8.0:
            feedback = f"[Điểm Tự Tin: {confidence:.2f}] Tạm ổn, nhưng Master G thấy câu này vẫn hơi lấn cấn. Cố làm cho nó tự nhiên hơn nhé!"
        else:
            feedback = f"[Điểm Tự Tin: {confidence:.2f}] Cấu trúc tan nát! Câu này sai ngữ pháp hoặc tối nghĩa rồi. Master G từ chối hiểu!"

        return {
            "score": score,
            "feedback": feedback
        }

    def _trigger_fallback(self, text: str, reason: str) -> dict:
        """
        Giao tiếp với utils/gemini_helper.py để lấy kết quả chấm điểm mỏ hỗn từ LLM.
        """
        print(f"[GEC ENGINE -> FALLBACK] Chuyển hướng tới Gemini. Lý do: {reason}")
        try:
            raw_json = evaluate_english_skill(text)
            llm_result = json.loads(raw_json)

            final_feedback = f"[LLM FALLBACK] {llm_result.get('feedback', '')}"
            if "slang_suggestion" in llm_result:
                final_feedback += f"\nGợi ý từ lóng: {llm_result['slang_suggestion']}"

            return {
                "score": float(llm_result.get("score", 0.0)),
                "feedback": final_feedback
            }
        except Exception as e:
            print(f"[GEC ENGINE] Lỗi nghiêm trọng khi Fallback: {e}")
            return {
                "score": 5.0,
                "feedback": f"[SYSTEM WARNING] Lò phản ứng AI cạn kiệt. Master G đi vắng. Tạm cho 5 điểm."
            }


if __name__ == "__main__":
    engine = LocalGECEngine()

    print("\n" + "="*50)
    print("TEST 1: Câu sai ngữ pháp hiển nhiên (Kỳ vọng: Local chấm điểm thấp)")
    print("="*50)
    res_1 = engine.evaluate("She do not likes play with dog.")
    print(res_1)

    print("\n" + "="*50)
    print("TEST 2: Câu đúng ngữ pháp hoàn toàn (Kỳ vọng: Local chấm điểm cao)")
    print("="*50)
    res_2 = engine.evaluate("She does not like playing with dogs.")
    print(res_2)

    print("\n" + "="*50)
    print("TEST 3: Câu lủng củng/OOD (Kỳ vọng: Kích hoạt Fallback gọi LLM)")
    print("="*50)
    res_3 = engine.evaluate("Dog she likes play not do.")
    print(res_3)