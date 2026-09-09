import os
import sys
import random
from typing import Dict, List, Optional
from app.ml_models.vocab_classifier import VocabCEFRClassifier

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LocalCritiqueSynthesizer:
    """
    Bộ não Tổng hợp Nhận xét Sư phạm Thích ứng theo Cấp độ (Level-Aware Pedagogical & Persona Critique Synthesizer)
    Tự động điều chỉnh phong cách nhận xét của Master G theo đúng trình độ người học:
    - SƠ CẤP (Beginner - A1/A2): Khích lệ, ân cần chỉ dẫn, tập trung ngữ pháp cốt lõi, không bắt bẻ văn phong.
    - TRUNG CẤP (Intermediate - B1/B2): Xéo xắt vừa phải, thách thức, chỉ lỗi thì hoàn thành, liên từ, gợi ý từ vựng B2.
    - CAO CẤP (Advanced - C1/C2): Tiêu chuẩn khắt khe bản xứ, soi kỹ sắc thái nghĩa, Collocation, tính tự nhiên.
    """

    RULE_CATEGORY_MAP = {
        'GRAMMAR': 'Ngữ pháp cơ bản',
        'TYPOS': 'Lỗi chính tả & Gõ phím',
        'SPELLING': 'Chính tả từ vựng',
        'CASING': 'Quy tắc viết hoa',
        'PUNCTUATION': 'Dấu câu & Ngắt nghỉ',
        'STYLE': 'Văn phong & Phong cách diễn đạt',
        'COLLOCATIONS': 'Kết hợp từ (Collocation)',
        'CONFUSED_WORDS': 'Nhầm lẫn từ đồng âm/gần nghĩa'
    }

    # Ngân hàng lời mở đầu Master G được cá nhân hóa theo 3 Cấp độ người học và 4 Thang điểm
    LEVEL_ADAPTIVE_OPENINGS = {
        'BEGINNER': {
            'perfect': [
                "🎉 [Tân Binh Xuất Sắc] Quá tuyệt vời! Đối với người mới bắt đầu, một câu chuẩn chỉnh thế này là điểm 10 xứng đáng!",
                "👏 [Khởi Đầu Vững Chắc] Master G rất ưng ý! Bạn nắm rất vững cấu trúc câu nền tảng rồi đấy!",
                "✨ [Tiến Bộ Nhanh] Không có bất kỳ lỗi nào! Phong độ rất hứa hẹn, tiếp tục giữ vững nhé!"
            ],
            'good': [
                "🌱 [Đang Lên Tay] Ý tưởng câu rất tốt! Chỉ còn một chút sơ suất nhỏ, sửa là ngon lành ngay:",
                "👍 [Cố Gắng Tốt] Câu của bạn truyền tải thông điệp rất rõ ràng. Cùng Master G trau chuốt lại xíu nào:",
                "👌 [Rất Triển Vọng] Gần đạt điểm tối đa rồi! Chú ý thêm một chi tiết nhỏ này nha:"
            ],
            'average': [
                "🧐 [Lưu Ý Nền Tảng] Bình tĩnh nào, mới học thì sai là chuyện bình thường. Nhìn kỹ các lỗi cơ bản này để nhớ lâu hơn nhé:",
                "💡 [Chỉ Dẫn Cho Bạn] Đừng nản lòng! Hãy chú ý cách chia từ theo hướng dẫn bên dưới của Master G nha:",
                "📝 [Nhắc Nhở Nhẹ] Câu hơi lúng túng một chút. Để Master G gỡ rối từng chỗ cho bạn:"
            ],
            'poor': [
                "🛡️ [Vực Dậy Tinh Thần] Ôi chao, câu này bị lẫn lộn cấu trúc rồi! Không sao cả, xem câu chuẩn bên dưới rồi chép lại luyện tay nào:",
                "🎯 [Tập Trung Lại Nào] Ngữ pháp cơ bản đang bị xáo trộn. Hãy bình tĩnh xem gợi ý sửa chi tiết của Master G dưới đây nhé!",
                "💪 [Khởi Động Lại] Đừng sợ sai! Xem Master G sửa từng từ một để lần sau không vấp nữa nha:"
            ]
        },
        'INTERMEDIATE': {
            'perfect': [
                "🔥 [Chiến Binh Đẳng Cấp] Ồ quao! Đôi mắt cú vọ của Master G hôm nay không bắt bẻ được ngươi điểm nào. Phong độ rất ngạo nghễ!",
                "😎 [Tay Viết Lão Luyện] Chuẩn không cần chỉnh! Cấu trúc mượt mà, dùng từ rất tự tin và đĩnh đạc!",
                "⚡ [Không Tì Vết] Ngữ pháp chuẩn mực như sách in. Tạm thời thu hồi danh hiệu 'thánh sai vặt' của ngươi!"
            ],
            'good': [
                "😏 [Khá Khẩm Đấy] Viết tương đối ổn áp đấy học trò, nhưng đẳng cấp của ngươi là không được để sót mấy hạt sạn này:",
                "🧐 [Vẫn Còn Sạn] Cấu trúc sáng sủa nhưng vẫn có chỗ làm Master G ngứa mắt. Mau tinh chỉnh lại:",
                "🤏 [Thiếu Tí Nữa] Suýt thì hoàn hảo nếu ngươi không bất cẩn ở vài chỗ này:"
            ],
            'average': [
                "🤨 [Hơi Mất Phong Độ] Tầm này rồi mà vẫn để sai mấy cấu trúc này à? Mau chấn chỉnh lại cho ta:",
                "⚠️ [Cảnh Báo Lủng Củng] Viết thế này thì Tây nó nghe cũng phải 'bật phụ đề' trong đầu mất! Mau xem lại:",
                "🌪️ [Ngữ Pháp Bay Quá] Ngữ pháp đang bay bổng quá đà rồi đấy nhé! Ghìm cương lại với các lỗi sau:"
            ],
            'poor': [
                "🤦‍♂️ [Master G Cạn Lời] Ngươi vừa sáng tạo ra một hệ thống ngữ pháp mới của người ngoài hành tinh à?",
                "💥 [Tan Hoang Cấu Trúc] Câu cú tan hoang như vừa dính phải bùa chú bóng tối! Dừng lại xem sửa ngay:",
                "😤 [Trầm Cảm Nhẹ] Viết thế này thực sự làm Master G 'trầm cảm' đấy! Sửa ngay lập tức:"
            ]
        },
        'ADVANCED': {
            'perfect': [
                "👑 [Bậc Thầy Tinh Hoa] Tuyệt tác! Diễn đạt tự nhiên, chuẩn mực học thuật và sắc thái cực kỳ tinh tế!",
                "🌟 [Đỉnh Cao Ngôn Từ] Không còn gì để chỉnh sửa. Câu văn đạt độ mượt mà và tự nhiên của người bản xứ có học thức!",
                "🏆 [Độc Cô Cầu Bại] Master G chính thức cúi đầu công nhận sự hoàn mỹ trong câu văn này của ngươi!"
            ],
            'good': [
                "🔍 [Soi Kính Hiển Vi] Ở cảnh giới này, ngữ pháp chuẩn thôi là chưa đủ! Master G vẫn thấy một chút gợn về tính tự nhiên (Idiomatic flow):",
                "🎯 [Cần Độ Tinh Tế] Đúng ngữ pháp nhưng chưa đạt độ 'chạm' tinh tế nhất. Cùng Master G nâng cấp sắc thái nghĩa:",
                "💎 [Đánh Bóng Kim Cương] Viên ngọc này chỉ cần mài giũa thêm một góc nhỏ về văn phong là hoàn hảo:"
            ],
            'average': [
                "🛑 [Tiêu Chuẩn Khắt Khe] Với cấp bậc của ngươi, để xuất hiện những lỗi cấu trúc thế này là một bước lùi đáng trách! Nhìn kỹ đây:",
                "⚡ [Hạ Phong Độ] Quá chủ quan trong liên kết câu và sắc thái nghĩa! Không thể chấp nhận lỗi này ở đẳng cấp này:",
                "📉 [Cảnh Báo Sa Sút] Viết câu gượng gạo và dùng từ chưa chuẩn collocation! Xem phân tích chuyên sâu bên dưới:"
            ],
            'poor': [
                "💥 [Rơi Đài Cao Thủ] Không thể tin nổi một người ở cấp bậc này lại viết ra một câu vỡ trận như thế này! Tự kiểm điểm ngay:",
                "🚨 [Khủng Hoảng Ngôn Từ] Diễn đạt hoàn toàn mất kiểm soát! Mau xem lại toàn bộ cấu trúc và từ vựng ngay lập tức!"
            ]
        }
    }

    def __init__(self):
        self.cefr_classifier = VocabCEFRClassifier()

    def normalize_user_level(self, level_str: str) -> str:
        """Chuẩn hóa mọi cấp độ hoặc tên Rank trong hệ thống thành 3 Tier: BEGINNER, INTERMEDIATE, ADVANCED"""
        if not level_str:
            return 'BEGINNER'
        l = str(level_str).lower()
        
        # Nhóm Cao cấp / Master
        advanced_keywords = [
            'độc cô', 'á thần', 'triết gia', 'hủy diệt', 'kiến trúc', 'bẻ cong', 
            'lãnh chúa', 'bậc thầy', 'nghệ nhân', 'advanced', 'c1', 'c2', 'master'
        ]
        if any(k in l for k in advanced_keywords):
            return 'ADVANCED'

        # Nhóm Trung cấp / Intermediate
        intermediate_keywords = [
            'chiến binh', 'hiệp sĩ', 'pháp sư', 'học giả', 'đạo tặc', 'trinh sát', 
            'thợ săn', 'intermediate', 'b1', 'b2'
        ]
        if any(k in l for k in intermediate_keywords):
            return 'INTERMEDIATE'

        # Nhóm Sơ cấp / Beginner (Tân binh, Thực tập sinh, Kẻ sống sót, Kẻ lang thang, A1, A2)
        return 'BEGINNER'

    def _determine_tier(self, score: float) -> str:
        if score >= 9.5:
            return 'perfect'
        elif score >= 7.5:
            return 'good'
        elif score >= 5.0:
            return 'average'
        return 'poor'

    def _analyze_vocabulary_sophistication(self, text: str, user_tier: str) -> Dict:
        """Phân tích mức độ tinh tế của từ vựng theo chuẩn CEFR và đối chiếu với Cấp độ người học."""
        words = [w.strip('.,!?"\'()[]{}:;') for w in text.split()]
        words = [w for w in words if len(w) >= 3 and w.isalpha()]

        if not words:
            return {"max_level": "A1", "highlight_words": [], "comment": ""}

        level_scores = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        ranked_words = []

        for w in set(words):
            lvl = self.cefr_classifier.predict_cefr(w)
            ranked_words.append((w, lvl, level_scores.get(lvl, 1)))

        ranked_words.sort(key=lambda x: x[2], reverse=True)
        max_level = ranked_words[0][1] if ranked_words else 'A1'
        advanced_words = [w[0] for w in ranked_words if w[2] >= 4]

        # Nhận xét thích ứng theo cấp độ người học
        if user_tier == 'BEGINNER':
            if advanced_words or max_level in ['B1', 'B2']:
                comment = f"Tuyệt vời! Dù ở cấp độ cơ bản nhưng bạn đã dám dùng từ vựng nâng cao [{', '.join(advanced_words or [ranked_words[0][0]])}] ({max_level}). Rất đáng khen!"
            else:
                comment = f"Từ vựng căn bản ({max_level}), rất phù hợp để củng cố nền tảng câu chắc chắn."
        elif user_tier == 'INTERMEDIATE':
            if advanced_words:
                comment = f"Điểm sáng từ vựng: Bạn phối hợp tốt các từ cấp độ [{', '.join(advanced_words)}] ({max_level}). Cố gắng dùng thêm collocations tự nhiên!"
            else:
                comment = "Từ vựng hơi an toàn (A1/A2). Là người học trung cấp, hãy mạnh dạn thay thế bằng các từ đồng nghĩa B1/B2 phong phú hơn!"
        else: # ADVANCED
            if max_level in ['C1', 'C2']:
                comment = f"Vốn từ xuất sắc ({max_level}) với các từ ngữ học thuật chuyên sâu [{', '.join(advanced_words)}]. Giữ vững phong độ đỉnh cao này!"
            else:
                comment = "Ở cấp bậc Cao Cấp, vốn từ này còn quá đơn giản (chưa có từ C1/C2). Hãy làm phong phú câu bằng các từ ngữ mang tính học thuật hoặc sắc thái thành ngữ!"

        return {
            "max_level": max_level,
            "highlight_words": advanced_words,
            "comment": comment
        }

    def synthesize(self, user_input: str, gec_result: Dict, user_level: str = "Beginner") -> str:
        """
        Tổng hợp nhận xét cá nhân hóa theo cấp độ người học:
        - Giọng điệu Master G thích ứng theo Level (Beginner / Intermediate / Advanced)
        - Lọc và nhấn mạnh các lỗi phù hợp với năng lực học viên
        - Câu sửa hoàn chỉnh
        - Nhận xét từ vựng CEFR đối chiếu với kỳ vọng cấp độ
        """
        score = float(gec_result.get('score', 0.0))
        corrected_text = gec_result.get('corrected_text', user_input).strip()
        errors = gec_result.get('errors', [])
        tier = self._determine_tier(score)
        user_tier = self.normalize_user_level(user_level)

        # 1. Lời mở đầu phong cách Master G thích ứng theo Level
        level_openings = self.LEVEL_ADAPTIVE_OPENINGS.get(user_tier, self.LEVEL_ADAPTIVE_OPENINGS['BEGINNER'])
        opening_pool = level_openings.get(tier, level_openings['average'])
        opening = random.choice(opening_pool)

        # Huy hiệu cấp độ hiển thị trên nhận xét
        level_badge = {
            'BEGINNER': '🌱 [Cấp độ: Sơ Cấp / Tân Binh]',
            'INTERMEDIATE': '⚔️ [Cấp độ: Trung Cấp / Chiến Binh]',
            'ADVANCED': '👑 [Cấp độ: Cao Cấp / Bậc Thầy]'
        }.get(user_tier, '')

        output_parts = [
            f"**{level_badge} — [Master G Đánh Giá: {score}/10 Điểm]**",
            opening,
            ""
        ]

        # 2. Chi tiết phân tích lỗi (Được lọc trọng tâm theo cấp độ)
        if errors:
            output_parts.append("🔍 **Chi tiết điểm cần lưu ý:**")
            
            # Đối với Beginner: Ẩn bớt các lỗi STYLE để tránh làm học viên ngợp
            displayed_errors = errors
            if user_tier == 'BEGINNER':
                grammar_core = [e for e in errors if e.get('category') != 'STYLE']
                displayed_errors = grammar_core if grammar_core else errors

            for i, err in enumerate(displayed_errors[:4], 1):
                cat = self.RULE_CATEGORY_MAP.get(err.get('category', ''), 'Ngữ pháp')
                msg = err.get('message', 'Lỗi cấu trúc câu')
                reps = err.get('replacements', [])
                
                rep_str = f" ➔ *Gợi ý sửa:* **'{', '.join(reps[:2])}'**" if reps else ""
                output_parts.append(f"{i}. [{cat}] {msg}{rep_str}")
            
            output_parts.append("")

        # 3. Câu chuẩn đề xuất
        if corrected_text and corrected_text.lower() != user_input.lower():
            output_parts.append("✨ **Câu chuẩn chỉnh đề xuất:**")
            output_parts.append(f"> *\"{corrected_text}\"*")
            output_parts.append("")
        elif tier == 'perfect':
            output_parts.append(f"✨ **Ngữ pháp chuẩn chỉ:** *\"{user_input}\"*")
            output_parts.append("")

        # 4. Phân tích từ vựng CEFR theo cấp độ
        vocab_analysis = self._analyze_vocabulary_sophistication(user_input, user_tier)
        if vocab_analysis["comment"]:
            output_parts.append(f"📚 **Nhận xét Năng lực Từ vựng:** {vocab_analysis['comment']}")

        return "\n".join(output_parts)


# Singleton instance
_synthesizer_instance = None

def get_critique_synthesizer() -> LocalCritiqueSynthesizer:
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = LocalCritiqueSynthesizer()
    return _synthesizer_instance


if __name__ == "__main__":
    synthesizer = get_critique_synthesizer()
    sample_sentence = "She do not likes apples."
    mock_bad_gec = {
        "score": 6.6,
        "corrected_text": "She does not like apples.",
        "errors": [
            {"category": "GRAMMAR", "message": "The pronoun 'She' is third-person singular.", "replacements": ["does not"]},
            {"category": "GRAMMAR", "message": "After auxiliary verb, use base form 'like'.", "replacements": ["like"]}
        ]
    }

    print("=== THỬ NGHIỆM CÙNG MỘT CÂU VỚI 3 CẤP ĐỘ KHÁC NHAU ===\n")
    print("--- 1. NGƯỜI DÙNG SƠ CẤP (TÂN BINH NGƠ NGÁC) ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Tân Binh Ngơ Ngác"))
    print("\n" + "="*70 + "\n")

    print("--- 2. NGƯỜI DÙNG TRUNG CẤP (CHIẾN BINH GIAO TIẾP) ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Chiến Binh Giao Tiếp"))
    print("\n" + "="*70 + "\n")

    print("--- 3. NGƯỜI DÙNG CAO CẤP (ĐỘC CÔ CẦU BẠI) ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Độc Cô Cầu Bại"))
