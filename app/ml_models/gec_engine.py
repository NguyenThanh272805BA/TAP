import language_tool_python
import re


class LocalGECEngine:
    """
    Bộ não 1: Grammar Error Correction (GEC)
    Xử lý nội bộ 100% offline. Đánh giá ngữ pháp, trừ điểm nghiêm ngặt và nội suy gợi ý.
    """

    def __init__(self):
        try:
            self.tool = language_tool_python.LanguageTool('en-US')
            print("[GEC ENGINE] Đã khởi động Hệ thống Chấm Ngữ Pháp Local thành công.")
        except Exception as e:
            print(f"[GEC ENGINE] Cảnh báo lỗi khởi tạo: {e}")
            self.tool = None

    def evaluate(self, text: str) -> dict:
        """
        Quét văn bản, phát hiện lỗi và trả về điểm số nghiêm ngặt kèm feedback.
        """
        if not self.tool:
            return {
                "score": 5.0,
                "feedback": "[SYSTEM WARNING] GEC Engine đang offline. Hãy kiểm tra lại Java hoặc báo cáo Admin."
            }

        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "feedback": "Ngươi định lừa Master G bằng một khoảng trống tĩnh lặng à? Nhập chữ vào!"
            }

        matches = self.tool.check(text)
        score = 10.0
        feedback_messages = []

        if not matches:
            return {
                "score": score,
                "feedback": "Tuyệt vời! Không thể soi ra được hạt sạn ngữ pháp nào. Phong độ rất ngạo nghễ!"
            }

        for match in matches:
            issue_type = match.rule_issue_type

            # Trọng số trừ điểm
            if issue_type == 'misspelling':
                score -= 1.5  # Sai chính tả phạt nặng hơn
            elif issue_type == 'grammar':
                score -= 3.0  # Sai cấu trúc ngữ pháp phạt sâu
            elif issue_type == 'style':
                score -= 0.5  # Lỗi văn phong
            else:
                score -= 1.0  # Các lỗi khác

            error_text = match.context[match.offset:match.offset + match.error_length]
            suggestions = " / ".join(match.replacements[:3]) if match.replacements else "Tự suy nghĩ cách sửa đi!"
            clean_message = re.sub(r'(\s+)', ' ', match.message).strip()

            feedback_messages.append(
                f"- Lỗi ngay chỗ '{error_text}': {clean_message}. Gợi ý của hệ thống: [{suggestions}]"
            )

        # Giới hạn điểm thấp nhất là 0.0, làm tròn 1 chữ số thập phân
        score = max(0.0, round(score, 1))

        intro_text = f"Master G vừa soi ra {len(matches)} hạt sạn chí mạng trong câu của ngươi:\n"
        final_feedback = intro_text + "\n".join(feedback_messages)

        return {
            "score": score,
            "feedback": final_feedback
        }


if __name__ == "__main__":
    engine = LocalGECEngine()
    test_sentence = "She do not likes play with dog."
    result = engine.evaluate(test_sentence)
    print(f"\nĐiểm: {result['score']}/10.0")
    print(f"Phản hồi:\n{result['feedback']}")