import language_tool_python
import re


class LocalGECEngine:
    """
    Bộ não 1: Grammar Error Correction (GEC)
    Xử lý nội bộ 100% offline. Đánh giá ngữ pháp, trừ điểm và nội suy gợi ý.
    """

    def __init__(self):
        try:
            # Khởi tạo mô hình ngôn ngữ tiếng Anh cục bộ
            # Lưu ý: Lần chạy đầu tiên sẽ tự động tải file rule (~200MB) về cache cục bộ,
            # các lần sau sẽ khởi động cực nhanh và chạy offline hoàn toàn.
            self.tool = language_tool_python.LanguageTool('en-US')
            print("[GEC ENGINE] Đã khởi động Hệ thống Chấm Ngữ Pháp Local thành công.")
        except Exception as e:
            print(f"[GEC ENGINE] Cảnh báo lỗi khởi tạo: {e}")
            self.tool = None

    def evaluate(self, text: str) -> dict:
        """
        Quét văn bản, phát hiện lỗi và trả về điểm số kèm feedback.
        """
        if not self.tool:
            return {
                "score": 5.0,
                "feedback": "[SYSTEM WARNING] GEC Engine đang offline. Hãy báo cáo Admin."
            }

        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "feedback": "Ngươi định lừa Master G bằng một khoảng trống tĩnh lặng à? Nhập chữ vào!"
            }

        # Thực thi quét lỗi O(1) qua Engine
        matches = self.tool.check(text)
        score = 10.0
        feedback_messages = []

        if not matches:
            return {
                "score": score,
                "feedback": "Tuyệt vời! Không thể soi ra được hạt sạn ngữ pháp nào. Phong độ rất ngạo nghễ!"
            }

        for match in matches:
            # Phân loại lỗi và áp dụng trọng số trừ điểm
            issue_type = match.ruleIssueType
            if issue_type == 'misspelling':
                score -= 0.5  # Sai chính tả nhẹ
            elif issue_type == 'grammar':
                score -= 1.0  # Sai cấu trúc nặng
            elif issue_type == 'style':
                score -= 0.2  # Văn phong chưa mượt
            else:
                score -= 0.5  # Các lỗi khác (dấu câu, khoảng trắng...)

            # Trích xuất đoạn text bị lỗi
            error_text = match.context[match.offset:match.offset + match.errorLength]

            # Lấy tối đa 3 gợi ý sửa đổi đáng tin cậy nhất
            suggestions = " / ".join(match.replacements[:3]) if match.replacements else "Tự suy nghĩ cách sửa đi!"

            # Lọc bớt các câu message quá dài hoặc thô cứng của thư viện
            clean_message = re.sub(r'(\s+)', ' ', match.message).strip()

            feedback_messages.append(
                f"- Lỗi ngay chỗ '{error_text}': {clean_message}. Gợi ý của hệ thống: [{suggestions}]"
            )

        # Chặn điểm âm, làm tròn 1 chữ số thập phân
        score = max(0.0, round(score, 1))

        # Nội suy Feedback chuẩn phong cách Master G
        intro_text = f"Master G vừa soi ra {len(matches)} hạt sạn chí mạng trong câu của ngươi:\n"
        final_feedback = intro_text + "\n".join(feedback_messages)

        return {
            "score": score,
            "feedback": final_feedback
        }


# --- TEST NHANH KHI CHẠY FILE ĐỘC LẬP ---
if __name__ == "__main__":
    engine = LocalGECEngine()
    test_sentence = "She do not likes play with dog."
    result = engine.evaluate(test_sentence)
    print(f"\nCâu test: '{test_sentence}'")
    print(f"Điểm: {result['score']}/10.0")
    print(f"Phản hồi:\n{result['feedback']}")