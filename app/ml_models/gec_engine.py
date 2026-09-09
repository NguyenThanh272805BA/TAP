import os
import sys
import json
from app.utils.gemini_helper import evaluate_english_skill

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LocalGECEngine:
    """
    Bộ não 1: Symbolic Grammar Error Correction & Diagnostics Engine
    Sử dụng LanguageTool phân tích cú pháp quy tắc hình thức (Symbolic Grammar Rules)
    kết hợp công thức tính điểm toán học và sửa câu tự động, không phụ thuộc vào dữ liệu train tĩnh.
    """

    _instance = None
    _lt_tool = None

    def __new__(cls, *args, **kwargs):
        """Mẫu Singleton đảm bảo chỉ tạo 1 tiến trình LanguageTool trong toàn bộ server."""
        if cls._instance is None:
            cls._instance = super(LocalGECEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, fallback_threshold=0.55, lazy=False):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.fallback_threshold = fallback_threshold
        self._initialized = True
        self.is_active = False

        if not lazy:
            self._ensure_loaded()

    def _ensure_loaded(self):
        """Khởi tạo LanguageTool Engine (Lazy Loading Singleton)."""
        if self.is_active and self._lt_tool is not None:
            return True

        try:
            import language_tool_python
            print("[GEC ENGINE] Đang khởi tạo Symbolic Grammar Engine (LanguageTool en-US)...")
            self._lt_tool = language_tool_python.LanguageTool('en-US')
            self.is_active = True
            print("[GEC ENGINE] Đã nạp thành công Symbolic Grammar Engine. Độc lập 100% dữ liệu train.")
            return True
        except Exception as e:
            print(f"[GEC ENGINE] Lỗi khởi tạo LanguageTool: {e}. Sẽ dùng fallback LLM.")
            self.is_active = False
            return False

    def evaluate(self, text: str) -> dict:
        """
        Phân tích ngữ pháp chuyên sâu:
        - Phát hiện vị trí sai (offset, length)
        - Phân loại luật ngữ pháp vi phạm (rule_id, category)
        - Gợi ý từ thay thế (replacements)
        - Tự động sửa thành câu hoàn chỉnh (corrected_text)
        - Tính điểm khoa học theo mật độ lỗi trên tổng số từ
        """
        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "feedback": "Ngươi định lừa Master G bằng một khoảng trống tĩnh lặng à? Nhập câu tiếng Anh vào!",
                "corrected_text": "",
                "errors": [],
                "error_count": 0
            }

        if not self.is_active:
            if not self._ensure_loaded():
                return self._trigger_fallback(text, "Local Brain Offline")

        try:
            # 1. Phân tích ngữ pháp hình thức bằng LanguageTool
            matches = self._lt_tool.check(text)
            corrected = self._lt_tool.correct(text)

            words = text.strip().split()
            word_count = max(1, len(words))

            # 2. Tính toán điểm số định lượng dựa trên mật độ lỗi
            # Trọng số theo loại lỗi: Ngữ pháp nặng = 1.2, Chính tả/Viết hoa = 0.5, Phong cách = 0.4
            total_penalty = 0.0
            error_details = []

            for m in matches:
                category = getattr(m, 'category', 'GRAMMAR')
                rule_id = getattr(m, 'rule_id', '')
                
                # Xác định trọng số phạt
                if 'SPELLING' in category or 'TYPOS' in category:
                    weight = 0.6
                elif 'CASING' in category:
                    weight = 0.4
                elif 'STYLE' in category:
                    weight = 0.5
                else:
                    weight = 1.2

                # Phạt tỉ lệ theo độ dài câu: Mật độ lỗi càng cao thì trừ càng nặng
                penalty = weight * (10.0 / word_count)
                total_penalty += penalty

                error_details.append({
                    "rule_id": rule_id,
                    "message": getattr(m, 'message', ''),
                    "offset": getattr(m, 'offset', 0),
                    "error_length": getattr(m, 'error_length', 0),
                    "context": getattr(m, 'context', ''),
                    "replacements": getattr(m, 'replacements', [])[:3],
                    "category": category
                })

            # Điểm từ 0.0 đến 10.0
            score = max(0.0, min(10.0, round(10.0 - total_penalty, 1)))

            # 3. Tạo phản hồi nhận xét sư phạm chi tiết (Pedagogical Feedback)
            if len(matches) == 0:
                feedback = "[Hoàn hảo] Câu của bạn chuẩn xác 100% về ngữ pháp và từ vựng! Phong độ ngạo nghễ!"
            else:
                feedback_lines = [f"[Tìm thấy {len(matches)} điểm cần lưu ý (Điểm: {score}/10)]:"]
                for i, err in enumerate(error_details[:3], 1):
                    rep_text = f" -> Gợi ý sửa: '{', '.join(err['replacements'])}'" if err['replacements'] else ""
                    feedback_lines.append(f"{i}. {err['message']}{rep_text}")
                
                if corrected != text:
                    feedback_lines.append(f"\n=> Câu chuẩn đề xuất: \"{corrected}\"")
                
                feedback = "\n".join(feedback_lines)

            return {
                "score": score,
                "feedback": feedback,
                "corrected_text": corrected,
                "errors": error_details,
                "error_count": len(error_details)
            }

        except Exception as e:
            print(f"[GEC ENGINE] Ngoại lệ khi phân tích câu: {e}. Kích hoạt Fallback.")
            return self._trigger_fallback(text, str(e))

    def _trigger_fallback(self, text: str, reason: str) -> dict:
        """Fallback LLM khi có ngoại lệ hệ thống."""
        print(f"[GEC ENGINE -> FALLBACK] Chuyển hướng tới Gemini. Lý do: {reason}")
        try:
            raw_json = evaluate_english_skill(text)
            llm_result = json.loads(raw_json)

            final_feedback = f"[LLM FALLBACK] {llm_result.get('feedback', '')}"
            if "slang_suggestion" in llm_result:
                final_feedback += f"\nGợi ý từ lóng: {llm_result['slang_suggestion']}"

            return {
                "score": float(llm_result.get("score", 0.0)),
                "feedback": final_feedback,
                "corrected_text": llm_result.get("corrected_text", text),
                "errors": [],
                "error_count": 0
            }
        except Exception as e:
            print(f"[GEC ENGINE] Lỗi nghiêm trọng khi Fallback: {e}")
            return {
                "score": 5.0,
                "feedback": "[SYSTEM WARNING] Lò phản ứng AI cạn kiệt. Master G đi vắng. Tạm cho 5 điểm.",
                "corrected_text": text,
                "errors": [],
                "error_count": 0
            }


if __name__ == "__main__":
    engine = LocalGECEngine()

    print("\n" + "="*60)
    print("TEST 1: Câu sai ngữ pháp hiển nhiên (Chủ ngữ số ít đi với động từ số nhiều)")
    print("="*60)
    res_1 = engine.evaluate("She do not likes play with dog.")
    print(json.dumps(res_1, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("TEST 2: Câu đúng ngữ pháp hoàn toàn")
    print("="*60)
    res_2 = engine.evaluate("She does not like playing with dogs.")
    print(json.dumps(res_2, indent=2, ensure_ascii=False))