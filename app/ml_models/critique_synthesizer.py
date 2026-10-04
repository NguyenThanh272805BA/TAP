import os
import sys
import random
import re
from typing import Dict, List, Optional
from app.ml_models.vocab_classifier import VocabCEFRClassifier

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LocalCritiqueSynthesizer:
    """
    Bộ não Tổng hợp Nhận xét Sư phạm Tự nhiên & Thích ứng theo Cấp độ (Level-Aware Pedagogical Mentor Synthesizer)
    Master G đóng vai trò là một người thầy / cố vấn ngôn ngữ tiếng Anh uyên bác, tinh tế, ân cần nhưng sắc sảo:
    - Loại bỏ hoàn toàn giọng điệu máy móc, các thẻ tag thô cứng kiểu log file [ĐÁNH GIÁ TỔNG QUAN].
    - Giải thích lỗi sai bằng tiếng Việt tự nhiên, trực quan, giải thích rõ nguyên nhân ngữ pháp và cách tư duy.
    - Đưa ra phiên bản viết lại tự nhiên và gợi ý nâng cấp câu văn phù hợp theo 3 bậc trình độ:
      + SƠ CẤP (Beginner): Khích lệ, ân cần, giảng giải ngữ pháp nền tảng rõ ràng, dễ hiểu.
      + TRUNG CẤP (Intermediate): Trau chuốt tính trôi chảy, sự hòa hợp thì, liên từ và gợi ý từ vựng B1/B2.
      + CAO CẤP (Advanced): Soi kỹ sắc thái nghĩa, collocations học thuật và độ tự nhiên bản xứ (idiomatic flow).
    """

    RULE_CATEGORY_MAP = {
        'GRAMMAR': 'Ngữ pháp',
        'TYPOS': 'Chính tả',
        'SPELLING': 'Chính tả từ vựng',
        'CASING': 'Viết hoa đầu câu',
        'PUNCTUATION': 'Dấu câu',
        'STYLE': 'Văn phong diễn đạt',
        'COLLOCATIONS': 'Kết hợp từ (Collocation)',
        'CONFUSED_WORDS': 'Từ dễ gây nhầm lẫn'
    }

    # Ngân hàng lời mở đầu tự nhiên, thân thiện và giàu tính sư phạm của Master G
    LEVEL_ADAPTIVE_OPENINGS = {
        'BEGINNER': {
            'perfect': [
                "Khởi đầu rất tuyệt vời! Bạn đặt một câu chuẩn xác và gãy gọn. Đối với người mới bắt đầu, đây là một nền móng cực kỳ vững chắc.",
                "Master G rất ấn tượng với câu viết này! Bạn nắm rất vững cấu trúc câu căn bản và diễn đạt rất tự tin.",
                "Một câu viết chuẩn chỉ, không có bất kỳ điểm sơ suất nào! Tiếp tục phát huy phản xạ tốt này nhé."
            ],
            'good': [
                "Ý tưởng của bạn rất hay và truyền tải thông điệp rất dễ hiểu! Chỉ cần trau chuốt lại một vài chi tiết nhỏ là câu sẽ hoàn hảo.",
                "Một nỗ lực đặt câu rất tốt! Bạn đã diễn đạt được trọn vẹn ý muốn nói, chỉ cần lưu ý một điểm ngữ pháp nhỏ dưới đây.",
                "Rất triển vọng! Cấu trúc câu tổng thể khá sáng sủa, sửa lại một chút là câu văn sẽ chuẩn chỉnh ngay."
            ],
            'average': [
                "Cố gắng rất đáng ghi nhận! Mới học tiếng Anh thì việc gặp một vài vướng mắc ngữ pháp là hoàn toàn bình thường. Hãy cùng Master G gỡ rối nhé.",
                "Đừng lo lắng nhé! Ý tưởng của bạn đã có, chúng ta chỉ cần sắp xếp lại trật tự từ và cách chia động từ cho thật ăn khớp.",
                "Câu của bạn đã biểu đạt được ý định, nhưng cấu trúc cần được gia cố thêm một chút. Xem gợi ý của Master G bên dưới nhé."
            ],
            'poor': [
                "Đừng nản lòng nhé! Việc bạn chủ động viết câu đã là một bước tiến đáng khen. Hãy xem phân tích bên dưới để nắm chắc cách đặt câu hơn.",
                "Bình tĩnh nào! Tiếng Anh có một số quy tắc ghép câu nền tảng rất thú vị. Hãy cùng Master G sửa từng chi tiết nhé.",
                "Mọi hành trình vạn dặm đều bắt đầu từ những câu viết đầu tiên. Xem câu chuẩn bên dưới để ghi nhớ cấu trúc nhé."
            ]
        },
        'INTERMEDIATE': {
            'perfect': [
                "Rất ấn tượng! Câu văn của bạn rất mạch lạc, cấu trúc chuẩn mực và diễn đạt hết sức tự nhiên.",
                "Chuẩn không cần chỉnh! Bạn dùng từ và ngữ pháp rất tự tin, nhịp điệu câu đọc lên rất mượt mà.",
                "Một câu văn xuất sắc! Cấu trúc câu gãy gọn và truyền tải thông điệp rất đĩnh đạc."
            ],
            'good': [
                "Câu viết tương đối tốt và sáng ý! Ở trình độ này, chỉ cần bạn chú ý thêm một hạt sạn nhỏ dưới đây là câu sẽ hoàn hảo hơn nhiều.",
                "Diễn đạt khá trôi chảy! Bạn đã thể hiện được tư duy liên kết câu tốt, chỉ cần tinh chỉnh lại một chi tiết nhỏ này.",
                "Gần như đạt điểm tuyệt đối! Bạn chỉ bất cẩn một chút ở phần chia từ, sửa lại là chuẩn ngay."
            ],
            'average': [
                "Ý tưởng câu rất đáng khen, nhưng cách dùng từ hoặc phối hợp thì của bạn đang hơi gợn một chút. Hãy xem phân tích để hoàn thiện hơn.",
                "Cấu trúc câu này cần được làm mượt mà hơn để người bản ngữ có thể nắm bắt thông điệp một cách tự nhiên nhất.",
                "Bạn đang có xu hướng dịch theo lối tư duy tiếng Việt nên câu hơi mất tự nhiên. Hãy cùng Master G điều chỉnh lại nhé."
            ],
            'poor': [
                "Câu văn đang bị xáo trộn cấu trúc và thiếu sự liên kết giữa các thành phần. Hãy đọc kỹ phần phân tích bên dưới để lấy lại phong độ nhé.",
                "Diễn đạt hiện tại chưa phản ánh đúng năng lực của bạn. Cần rà soát lại quy tắc cấu trúc câu cơ bản ngay.",
                "Cần chấn chỉnh lại cách đặt câu! Hãy tập trung vào cấu trúc câu hoàn chỉnh trước khi viết những câu dài phức tạp."
            ]
        },
        'ADVANCED': {
            'perfect': [
                "Tuyệt vời! Câu văn đạt độ mượt mà, tự nhiên và sắc thái biểu cảm rất chuẩn mực theo phong cách bản ngữ.",
                "Rất đĩnh đạc! Cách bạn kết hợp từ và lựa chọn cấu trúc câu thể hiện năng lực ngôn ngữ rất sâu sắc.",
                "Không còn điểm nào để chê! Câu văn rất học thuật, tự nhiên và có chiều sâu."
            ],
            'good': [
                "Ngữ pháp rất vững vàng! Ở trình độ cao cấp này, Master G chỉ muốn gợi ý thêm một góc nhìn nhỏ về tính tự nhiên (idiomatic flow) để câu đắt giá hơn.",
                "Đúng ngữ pháp nhưng nếu muốn đạt đến độ tự nhiên tinh tế nhất, bạn có thể cân nhắc nâng cấp một vài kết hợp từ (collocations).",
                "Câu văn sắc bén! Chỉ cần mài giũa thêm một chút về phong cách hành văn là đạt tiêu chuẩn bản xứ trọn vẹn."
            ],
            'average': [
                "Ở cấp độ này, việc để xuất hiện các lỗi cấu trúc cơ bản thế này là điều bạn cần lưu tâm rèn luyện lại ngay. Xem phân tích bên dưới nhé.",
                "Câu văn hơi gượng gạo và dùng từ chưa thật sự chuẩn xác theo ngữ cảnh học thuật. Hãy đọc kỹ gợi ý bên dưới.",
                "Cần chú ý hơn đến tính liên kết và sắc thái nghĩa của từng từ khi đặt trong văn cảnh phức tạp."
            ],
            'poor': [
                "Câu văn bị vỡ cấu trúc và thiếu tính mạch lạc. Bạn cần chậm lại một nhịp để củng cố lại trật tự câu trước khi thử sức với các cấu trúc khó.",
                "Diễn đạt chưa đạt chuẩn ở cấp bậc này. Hãy xem lại toàn bộ cấu trúc và cách chọn từ để khôi phục phong độ."
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

        advanced_keywords = [
            'độc cô', 'á thần', 'triết gia', 'hủy diệt', 'kiến trúc', 'bẻ cong',
            'lãnh chúa', 'bậc thầy', 'nghệ nhân', 'advanced', 'c1', 'c2', 'master'
        ]
        if any(k in l for k in advanced_keywords):
            return 'ADVANCED'

        intermediate_keywords = [
            'chiến binh', 'hiệp sĩ', 'pháp sư', 'học giả', 'đạo tặc', 'trinh sát',
            'thợ săn', 'intermediate', 'b1', 'b2'
        ]
        if any(k in l for k in intermediate_keywords):
            return 'INTERMEDIATE'

        return 'BEGINNER'

    def _determine_tier(self, score: float) -> str:
        if score >= 9.5:
            return 'perfect'
        elif score >= 7.5:
            return 'good'
        elif score >= 5.0:
            return 'average'
        return 'poor'

    def explain_error_pedagogically(self, err: Dict, user_input: str) -> str:
        """
        Chuyển hóa thông báo lỗi thô của LanguageTool thành lời chỉ dẫn sư phạm tiếng Việt tự nhiên, ấm áp và dễ hiểu.
        """
        rule_id = str(err.get('rule_id', '')).upper()
        msg = str(err.get('message', ''))
        msg_lower = msg.lower()
        reps = err.get('replacements', [])
        rep = reps[0] if reps else ""
        context = err.get('context', '')
        category = str(err.get('category', 'GRAMMAR')).upper()

        # Tìm từ/cụm từ sai trong câu
        offset = err.get('offset', 0)
        length = err.get('error_length', 0)
        err_word = ""
        if length > 0 and 0 <= offset < len(user_input):
            err_word = user_input[offset:offset + length].strip()

        # 1. Lỗi chỉ nhập 1 từ đơn lẻ hoặc câu khuyết vị ngữ (Fragment)
        if rule_id == "SINGLE_WORD_INPUT":
            return "Bạn mới chỉ nhập một từ đơn lẻ. Để hoàn thành nhiệm vụ, hãy đặt từ này vào một câu hoàn chỉnh có đầy đủ Chủ ngữ và Vị ngữ nhé."
        if rule_id == "SENTENCE_FRAGMENT":
            return "Câu của bạn đang thiếu động từ chính (vị ngữ). Hãy bổ sung thêm hành động hoặc trạng thái để tạo thành câu hoàn chỉnh diễn đạt trọn vẹn một ý nghĩ."

        # 2. Lỗi mạo từ a / an
        if 'EN_A_VS_AN' in rule_id or "use 'an' instead of 'a'" in msg_lower or "use 'a' instead of 'an'" in msg_lower:
            if rep:
                return f"Quy tắc mạo từ 'a' / 'an': Dùng **'{rep}'** (thay vì *'{err_word or 'từ trước đó'}'*) vì từ đi liền sau bắt đầu bằng nguyên âm/phụ âm trong phát âm."
            return "Quy tắc mạo từ: Chú ý dùng 'an' trước các từ bắt đầu bằng nguyên âm phát âm (u, e, o, a, i) và 'a' trước phụ âm."

        # 3. Lỗi thiếu mạo từ (Missing article)
        if 'ARTICLE' in rule_id or 'article is missing' in msg_lower or 'an article seems' in msg_lower:
            noun = err_word or "danh từ này"
            rep_hint = f" (ví dụ: *{rep}*)" if rep else ""
            return f"Thiếu mạo từ: Danh từ đếm được số ít *'{noun}'* cần có mạo từ (*a*, *an*, *the*) hoặc đại từ sở hữu đứng trước{rep_hint}."

        # 4. Lỗi sự hòa hợp Chủ ngữ - Động từ (Subject-Verb Agreement)
        if any(k in rule_id for k in ['AGREEMENT', 'VERB_AGR', 'PERS_PRONOUN']) or any(k in msg_lower for k in ['third-person', 'singular', 'agreement error', 'subject and verb']):
            if 'auxiliary' in msg_lower or 'do not' in user_input.lower() or 'does not' in rep.lower():
                aux_rep = rep if rep else "does not"
                aux_err = err_word if err_word else "do not"
                return f"Sự hòa hợp chủ ngữ & trợ động từ: Với chủ ngữ ngôi thứ ba số ít, bạn cần dùng trợ động từ **'{aux_rep}'** thay vì *'{aux_err}'*."
            if rep:
                return f"Sự hòa hợp Chủ - Vị: Chủ ngữ và động từ cần hòa hợp về số ít/số nhiều. Gợi ý bạn nên chia là **'{rep}'** (thay cho *'{err_word}'*)."
            return "Sự hòa hợp Chủ - Vị: Chú ý chia động từ tương ứng với chủ ngữ số ít hoặc số nhiều."

        # 5. Lỗi động từ sau trợ động từ (Modal / Auxiliary + Bare Infinitive)
        if 'auxiliary verb' in msg_lower or 'base form' in msg_lower:
            if rep:
                return f"Dạng động từ sau trợ động từ: Sau trợ động từ (như *do, does, did, can, will...*), động từ chính bắt buộc giữ ở dạng nguyên mẫu không chia: dùng **'{rep}'** (không thêm 's' hay 'ed')."
            return "Sau trợ động từ, động từ chính luôn ở dạng nguyên mẫu không chia."

        # 6. Lỗi thì và phân từ (Tenses & Participles)
        if any(k in msg_lower for k in ['past tense', 'past participle', 'participle should be used']):
            if rep:
                return f"Chia thì & dạng động từ: Ở ngữ cảnh này, bạn cần dùng dạng quá khứ / phân từ **'{rep}'** thay cho *'{err_word}'* để đúng thì của câu."
            return "Hãy kiểm tra lại dạng quá khứ hoặc phân từ của động từ để phù hợp với ngữ cảnh thì."

        # 7. Lỗi giới từ (Prepositions)
        if 'PREPOSITION' in rule_id or 'preposition' in msg_lower:
            if rep:
                return f"Giới từ tự nhiên: Thay vì dùng *'{err_word}'*, người bản ngữ thường kết hợp với giới từ **'{rep}'** trong ngữ cảnh này."
            return "Chú ý lựa chọn giới từ phù hợp với động từ hoặc tính từ đi trước."

        # 8. Lỗi chính tả & gõ phím (Spelling / Typo)
        if category in ['TYPOS', 'SPELLING'] or 'MORFOLOGIK' in rule_id or 'spelling mistake' in msg_lower:
            if rep:
                return f"Chính tả từ vựng: Từ *'{err_word}'* có vẻ bị gõ nhầm. Gợi ý từ đúng là **'{rep}'**."
            return f"Từ *'{err_word}'* dường như bị sai chính tả. Hãy kiểm tra lại cách viết."

        # 9. Lỗi viết hoa đầu câu (Casing)
        if category == 'CASING' or 'UPPERCASE' in rule_id or 'uppercase letter' in msg_lower:
            return "Quy chuẩn viết câu: Hãy nhớ viết hoa chữ cái đầu câu để câu văn thêm chỉn chu và đúng chuẩn mực."

        # 10. Lỗi dấu câu (Punctuation)
        if category == 'PUNCTUATION' or 'PUNCTUATION' in rule_id or 'comma' in msg_lower:
            return "Dấu câu & ngắt nghỉ: Hãy chú ý ngắt nghỉ và đặt dấu câu phù hợp để người đọc dễ theo dõi mạch câu."

        # 11. Tổng quát / Fallback: Làm mềm thông điệp tiếng Anh
        if rep:
            return f"Lưu ý diễn đạt tại *'{err_word or 'vị trí này'}'*: Gợi ý điều chỉnh thành **'{rep}'** để câu văn chuẩn xác và tự nhiên hơn."

        clean_msg = msg.replace('"', "'")
        return f"Điểm cần lưu ý: {clean_msg}."

    def _analyze_vocabulary_sophistication(self, text: str, user_tier: str, is_fragment: bool = False) -> Dict:
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

        if is_fragment:
            word_show = ', '.join(advanced_words or [ranked_words[0][0]])
            comment = f"Cụm từ chứa từ vựng cấp độ {max_level} ({word_show}). Hãy đặt từ này vào một câu hoàn chỉnh có chủ ngữ và vị ngữ để Master G ghi nhận điểm số nhé."
            return {
                "max_level": max_level,
                "highlight_words": advanced_words,
                "comment": comment
            }

        # Nhận xét thích ứng theo cấp độ người học tự nhiên, tích cực
        if user_tier == 'BEGINNER':
            if advanced_words:
                word_show = ', '.join(advanced_words)
                comment = f"Điểm sáng từ vựng: Bạn đã chủ động dùng từ nâng cao [{word_show}] ({max_level}). Đây là dấu hiệu tiến bộ rất đáng khích lệ!"
            else:
                comment = f"Vốn từ nền tảng ({max_level}) được dùng rất đúng chỗ, rất thích hợp để rèn luyện phản xạ ngữ pháp vững vàng."
        elif user_tier == 'INTERMEDIATE':
            if advanced_words:
                comment = f"Điểm sáng từ vựng: Bạn kết hợp tốt các từ cấp độ [{', '.join(advanced_words)}] ({max_level}). Hãy tiếp tục làm quen với các cụm collocations tự nhiên đi kèm nhé."
            else:
                comment = "Từ vựng ở mức cơ bản (A1/A2). Khi đã vững ngữ pháp, bạn có thể thử thay thế bằng một số từ đồng nghĩa ở mức B1/B2 để câu văn thêm sinh động."
        else:  # ADVANCED
            if max_level in ['C1', 'C2']:
                comment = f"Vốn từ phong phú và giàu tính học thuật ({max_level}) với [{', '.join(advanced_words)}]. Giữ vững phong độ sắc bén này nhé."
            else:
                comment = "Ở cấp bậc Cao Cấp, câu văn sẽ đắt giá hơn nữa nếu bạn lồng ghép thêm các thành ngữ (idioms) hoặc kết hợp từ học thuật nâng cao."

        return {
            "max_level": max_level,
            "highlight_words": advanced_words,
            "comment": comment
        }

    def synthesize(self, user_input: str, gec_result: Dict, user_level: str = "Beginner", target_word: str = "") -> str:
        """
        Tổng hợp nhận xét chuyên sâu theo phong cách Cố Vấn Ngôn Ngữ Master G:
        - Tự nhiên, ấm áp, thấu cảm, giàu giá trị sư phạm.
        - Khai thác 100% bộ não gợi ý offline (Hint Service & Collocations) để phân tích mục tiêu.
        - Chẩn đoán từ loại, cấp độ CEFR, cấu trúc ngữ pháp và nghĩa tiếng Việt.
        - Cung cấp câu mẫu chuẩn mực ngữ cảnh kèm dịch nghĩa, triệt tiêu hoàn toàn ví dụ cứng nhắc.
        - Gợi ý cụm từ collocations tự nhiên và hướng dẫn nâng cấp theo bậc trình độ (A1-C2).
        """
        score = float(gec_result.get('score', 0.0))
        corrected_text = gec_result.get('corrected_text', user_input).strip()
        errors = gec_result.get('errors', [])
        is_fragment = gec_result.get('is_fragment', False)
        tier = self._determine_tier(score)
        user_tier = self.normalize_user_level(user_level)

        # 1. Lời mở đầu Master G đồng hành
        level_openings = self.LEVEL_ADAPTIVE_OPENINGS.get(user_tier, self.LEVEL_ADAPTIVE_OPENINGS['BEGINNER'])
        opening_pool = level_openings.get(tier, level_openings['average'])
        opening = random.choice(opening_pool)

        tier_title = {
            'BEGINNER': 'Sơ Cấp',
            'INTERMEDIATE': 'Trung Cấp',
            'ADVANCED': 'Cao Cấp'
        }.get(user_tier, 'Người Học')

        output_parts = [
            f"🎯 Master G Cố Vấn | Đánh giá: {score}/10 Điểm ({tier_title})",
            "",
            opening,
            ""
        ]

        # 2. Khai thác dữ liệu gợi ý Offline từ Hint Service
        hint_data = None
        target_focus = (target_word or "").strip()

        # Nếu không có target_word rõ ràng, tự động trích xuất từ vựng trọng tâm từ câu
        if not target_focus:
            raw_tokens = [w.strip('.,!?"\'()[]{}:;') for w in user_input.split()]
            meaningful_tokens = [w for w in raw_tokens if len(w) >= 3 and w.lower() not in {
                'this', 'that', 'they', 'them', 'have', 'with', 'from', 'what', 'when', 'where', 'there', 'here', 'will', 'some'
            }]
            if meaningful_tokens:
                # Ưu tiên từ có CEFR cao nhất
                meaningful_tokens.sort(key=lambda t: self.cefr_classifier.predict_cefr(t), reverse=True)
                target_focus = meaningful_tokens[0]

        if target_focus:
            try:
                from app.utils.hint_service import get_offline_vocab_hint, generate_grammar_hint
                grammar_indicators = {'present', 'past', 'future', 'continuous', 'perfect', 'passive', 'conditional', 'inversion', 'gerund', 'clause'}
                if any(ind in target_focus.lower() for ind in grammar_indicators):
                    hint_data = generate_grammar_hint(target_focus)
                else:
                    hint_data = get_offline_vocab_hint(target_focus)
            except Exception as e:
                hint_data = None

        # 3. Chẩn đoán Mục tiêu Cốt lõi (Target Core Mastery)
        if hint_data and target_focus:
            tgt_word = hint_data.get('word', target_focus)
            tgt_meaning = hint_data.get('meaning', '')
            tgt_pos = hint_data.get('pos', 'Từ vựng')
            tgt_cefr = hint_data.get('cefr', 'B1')

            clean_tgt = target_focus.lower()
            tokens_in_input = set(re.findall(r'\b[a-zA-Z]+\b', user_input.lower()))
            is_target_used = any(clean_tgt in tok or tok in clean_tgt for tok in tokens_in_input) or (clean_tgt in user_input.lower())

            output_parts.append("🎯 CHẨN ĐOÁN MỤC TIÊU CỐT LÕI:")
            output_parts.append(f"• Từ/Cấu trúc: {tgt_word} [{tgt_cefr}] - {tgt_pos}")
            if tgt_meaning and tgt_meaning != "Từ vựng mục tiêu":
                output_parts.append(f"• Giải nghĩa: {tgt_meaning}")

            if target_word:
                if is_target_used:
                    output_parts.append(f"✨ Vận dụng mục tiêu: Xuất sắc! Bạn đã lồng ghép chuẩn xác '{target_word}' vào câu.")
                else:
                    output_parts.append(f"⚠️ Lưu ý mục tiêu: Câu của bạn hiện chưa xuất hiện '{target_word}'. Hãy thử áp dụng cấu trúc đề xuất bên dưới để hoàn thành bài tập nhé!")
            output_parts.append("")

        # 4. Chi tiết lỗi sai & phân tích sư phạm
        if is_fragment:
            output_parts.append("🔍 Điểm cốt lõi cần lưu ý:")
            output_parts.append(
                f"Nội dung bạn nhập ('{user_input}') hiện mới là một cụm từ rời rạc / từ đơn lẻ, chưa cấu thành một câu hoàn chỉnh. "
                f"Trong tiếng Anh, một câu chuẩn bắt buộc phải có đầy đủ Chủ ngữ (Subject) và Động từ vị ngữ chính (Verb) để diễn đạt một thông điệp trọn vẹn."
            )
            output_parts.append("")
        elif errors:
            output_parts.append(f"🔍 Những điểm cần lưu ý ({len(errors)} điểm):")
            displayed_errors = errors
            if user_tier == 'BEGINNER':
                grammar_core = [e for e in errors if e.get('category') != 'STYLE']
                displayed_errors = grammar_core if grammar_core else errors

            for err in displayed_errors[:4]:
                explanation = self.explain_error_pedagogically(err, user_input)
                output_parts.append(f"• {explanation}")
            output_parts.append("")
        else:
            output_parts.append("✨ Điểm sáng trong câu:")
            output_parts.append("• Cấu trúc câu chuẩn xác 100%, các thành phần câu liên kết chặt chẽ và truyền tải ý tứ rất mạch lạc.")
            output_parts.append("")

        # 5. Phiên bản đề xuất & Câu mẫu chuẩn ngữ cảnh (Showcase Example)
        if corrected_text and corrected_text.strip().lower() != user_input.strip().lower():
            output_parts.append("💡 Phiên bản chuẩn chỉnh đề xuất:")
            output_parts.append(f'"{corrected_text}"')
            output_parts.append("")
        elif not errors and not is_fragment:
            output_parts.append("💡 Câu văn hoàn thiện:")
            output_parts.append(f'"{user_input}"')
            output_parts.append("")

        # Đưa ra câu ví dụ mẫu chuẩn ngữ cảnh từ Hint Service (Offline)
        if hint_data and hint_data.get('main_sentence'):
            main_sen = hint_data.get('main_sentence')
            main_vi = hint_data.get('main_sentence_vi', '')
            output_parts.append("📖 Câu mẫu chuẩn ngữ cảnh (Showcase Example):")
            output_parts.append(f'• "{main_sen}"')
            if main_vi:
                output_parts.append(f'  ➔ Dịch nghĩa: {main_vi}')
            output_parts.append("")

        # 6. Kho cụm từ hay đi kèm (Collocations)
        collocations = (hint_data.get('collocations') if hint_data else []) or []
        if collocations:
            output_parts.append("🔗 Cụm từ hay đi kèm (Collocations nên dùng):")
            for c in collocations[:4]:
                if isinstance(c, dict):
                    c_text = c.get('collocation') or c.get('text', '')
                    c_mean = c.get('meaning', '')
                    disp = f"{c_text} ({c_mean})" if c_mean else c_text
                else:
                    disp = str(c)
                if disp and disp != "undefined":
                    output_parts.append(f"• {disp}")
            output_parts.append("")

        # 7. Lời khuyên nâng cấp từ Master G (Pedagogical Upgrade)
        vocab_analysis = self._analyze_vocabulary_sophistication(user_input, user_tier, is_fragment=is_fragment)
        output_parts.append("🚀 Lời khuyên phát triển từ Master G:")

        formula = hint_data.get('formula') if hint_data else ""
        if formula:
            output_parts.append(f"💡 Cấu trúc gợi ý: {formula}")

        if is_fragment:
            output_parts.append(
                "Để biến cụm từ thành một câu hoàn chỉnh, hãy áp dụng mô hình S + V (+ O): "
                "bổ sung một chủ thể thực hiện hành động hoặc một trạng thái cụ thể."
            )
        elif user_tier == 'BEGINNER':
            if errors:
                output_parts.append(
                    "Hãy luôn ghi nhớ quy tắc trục xương sống: Chủ ngữ + Động từ + Tân ngữ (S-V-O). "
                    "Khi viết, chỉ cần dừng lại 2 giây kiểm tra xem động từ đã chia đúng theo chủ ngữ chưa là câu sẽ luôn chuẩn chỉnh."
                )
            else:
                output_parts.append(
                    "Bạn đã nắm rất vững cấu trúc câu nền tảng! Khi đã quen tay, hãy thử mở rộng câu bằng cách thêm từ nối (because, so, and) "
                    "hoặc bổ sung trạng từ chỉ thời gian, nơi chốn để câu giàu thông tin hơn nhé."
                )
        elif user_tier == 'INTERMEDIATE':
            output_parts.append(
                "Để câu văn thêm chiều sâu, hãy thử kết hợp các liên từ phụ thuộc (although, whereas, while...) "
                "hoặc sử dụng mệnh đề quan hệ rút gọn. Điều này sẽ giúp câu văn của bạn đạt phong cách tự nhiên chuẩn B2."
            )
        else:  # ADVANCED
            output_parts.append(
                "Ở cấp độ này, hãy chú ý tăng cường các collocations học thuật và nhịp điệu của câu. "
                "Sự phối hợp tinh tế giữa câu ngắn và câu ghép phức sẽ tạo nên một phong cách hành văn đầy sức thuyết phục."
            )

        tip = hint_data.get('tip') if hint_data else ""
        if tip:
            output_parts.append(f"• Mẹo: {tip}")

        if vocab_analysis["comment"]:
            output_parts.append(f"• Vốn từ: {vocab_analysis['comment']}")

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
            {"rule_id": "PERS_PRONOUN_AGREEMENT", "category": "GRAMMAR", "message": "The pronoun 'She' is third-person singular.", "replacements": ["does not"], "offset": 4, "error_length": 6},
            {"rule_id": "AUXILIARY_VERB", "category": "GRAMMAR", "message": "After auxiliary verb, use base form 'like'.", "replacements": ["like"], "offset": 11, "error_length": 5}
        ]
    }

    print("=== THỬ NGHIỆM CÙNG MỘT CÂU VỚI 3 CẤP ĐỘ KHÁC NHAU ===\n")
    print("--- 1. NGƯỜI DÙNG SƠ CẤP ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Tân Binh Ngơ Ngác"))
    print("\n" + "="*70 + "\n")

    print("--- 2. NGƯỜI DÙNG TRUNG CẤP ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Chiến Binh Giao Tiếp"))
    print("\n" + "="*70 + "\n")

    print("--- 3. NGƯỜI DÙNG CAO CẤP ---")
    print(synthesizer.synthesize(sample_sentence, mock_bad_gec, user_level="Độc Cô Cầu Bại"))
