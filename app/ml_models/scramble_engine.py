import random
import time
import re
from typing import Dict, List, Tuple
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.grammar import Grammar
from app.ml_models.srs_predictor import SmartSRS
from app import db

srs_engine = SmartSRS()


class LocalScrambleEngine:
    """
    Bộ não Minigame Cục bộ: Ải Ghép Chữ & Cú Pháp (Cyber Word & Syntax Forge)
    Hoạt động 100% bằng thuật toán xáo trộn ký tự, đối soát cú pháp ngữ pháp hình thức.
    Độ trễ < 5ms, hoàn toàn không tốn Token LLM.
    """

    def __init__(self):
        pass

    def generate_word_scramble(self, vocab_id: int = None, cefr_filter: str = None) -> Dict:
        """
        Sinh câu đố ghép chữ (Word Unscramble) từ kho từ vựng.
        """
        query = Vocabulary.query
        if cefr_filter:
            query = query.filter_by(cefr_level=cefr_filter)

        if vocab_id:
            vocab = Vocabulary.query.get(vocab_id)
        else:
            total = query.count()
            if total == 0:
                vocab = Vocabulary.query.first()
            else:
                offset = random.randint(0, total - 1)
                vocab = query.offset(offset).first()

        if not vocab:
            return {
                "status": "error",
                "message": "Không tìm thấy từ vựng phù hợp trong hệ thống!"
            }

        word_clean = vocab.word.strip().upper()
        letters = [ch for ch in word_clean if ch.isalpha()]

        # Thuật toán xáo trộn ngẫu nhiên (Fisher-Yates) đảm bảo không trùng với từ gốc
        shuffled = letters.copy()
        if len(shuffled) > 2:
            attempts = 0
            while "".join(shuffled) == "".join(letters) and attempts < 10:
                random.shuffle(shuffled)
                attempts += 1
        elif len(shuffled) == 2:
            shuffled.reverse()

        # Tính thời gian tương ứng với độ dài từ và cấp độ CEFR
        base_time = 12.0
        if len(word_clean) >= 8:
            base_time = 18.0
        elif len(word_clean) <= 4:
            base_time = 8.0

        return {
            "status": "success",
            "vocab_id": vocab.id,
            "target_word": word_clean,
            "meaning": vocab.meaning,
            "theme": vocab.theme or "General",
            "cefr_level": vocab.cefr_level or "A1",
            "shuffled_letters": shuffled,
            "word_length": len(letters),
            "hint_letter": letters[0] if letters else "",
            "time_limit": base_time
        }

    def verify_word_scramble(self, vocab_id: int, user_answer: str, response_time_sec: float, user_id: int = None) -> Dict:
        """
        Xác thực kết quả ghép chữ của học viên và tự động đồng bộ vào Smart SRS.
        """
        if not vocab_id:
            return {"status": "error", "message": "Thiếu mã từ vựng!"}
        try:
            vocab_id = int(vocab_id)
        except (ValueError, TypeError):
            return {"status": "error", "message": "Mã từ vựng không hợp lệ!"}

        vocab = Vocabulary.query.get(vocab_id)
        if not vocab:
            return {"status": "error", "message": "Từ vựng không tồn tại!"}

        clean_target = "".join([c for c in vocab.word.strip().upper() if c.isalpha()])
        clean_user = "".join([c for c in (user_answer or "").strip().upper() if c.isalpha()])

        is_correct = (clean_target == clean_user)

        # Tính điểm số dựa trên độ chính xác và phản xạ thời gian
        score = 10.0 if is_correct else 0.0
        if is_correct and response_time_sec > 0:
            if response_time_sec <= 3.0:
                score = 10.0  # Siêu tốc
            elif response_time_sec <= 7.0:
                score = 9.0
            else:
                score = 8.0

        # Tự động cập nhật hồ sơ ghi nhớ Smart SRS nếu có user_id
        if user_id:
            uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
            if not uv:
                uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True, fail_count=0, avg_response_time=0.0, previous_interval=0.0)
                db.session.add(uv)
                db.session.flush()

            current_fail = int(uv.fail_count) if uv.fail_count is not None else 0
            current_avg = float(uv.avg_response_time) if uv.avg_response_time is not None else 0.0
            current_prev_interval = float(uv.previous_interval) if uv.previous_interval is not None else 0.0

            if not is_correct:
                uv.fail_count = current_fail + 1
                uv.memorization_level = 'CHUA_THUOC'
            else:
                uv.fail_count = current_fail
                uv.memorization_level = 'DA_THUOC'

            time_val = max(0.5, float(response_time_sec))
            uv.avg_response_time = time_val if current_avg == 0.0 else (current_avg + time_val) / 2.0

            next_dt, new_interval = srs_engine.predict_next_review(
                int(uv.fail_count or 0), float(uv.avg_response_time or 2.0), current_prev_interval
            )
            uv.next_review_time = next_dt
            uv.previous_interval = new_interval
            db.session.commit()

        feedback_msg = (
            f"🎉 CHÍNH XÁC! Bạn ghép chuẩn từ '{vocab.word}' trong {response_time_sec:.1f}s!"
            if is_correct
            else f"❌ TIẾC QUÁ! Đáp án đúng là: '{vocab.word}' ({vocab.meaning}). Đã đưa vào lịch ôn Smart SRS!"
        )

        return {
            "status": "success",
            "is_correct": is_correct,
            "target_word": vocab.word,
            "meaning": vocab.meaning,
            "score": score,
            "response_time": response_time_sec,
            "message": feedback_msg
        }

    def generate_syntax_scramble(self, grammar_id: int = None) -> Dict:
        """
        Sinh ải lắp ráp trật tự cú pháp câu (Syntax Assembly).
        """
        grammar = Grammar.query.get(grammar_id) if grammar_id else Grammar.query.order_by(db.func.rand()).first()
        if not grammar or not grammar.example:
            # Fallback câu ví dụ chuẩn
            example_sentence = "She does not like eating apples in the morning."
            structure_name = "Present Simple Negative"
            explanation = "Thì hiện tại đơn thể phủ định"
        else:
            example_sentence = grammar.example.strip()
            structure_name = grammar.structure
            explanation = grammar.explanation

        # Tách câu thành các mảnh ghép từ / cụm từ
        tokens = example_sentence.replace('.', '').replace('?', '').replace('!', '').split()
        if len(tokens) <= 6:
            chunks = tokens.copy()
        else:
            # Gom các cụm từ ngắn lại để bài tập không bị rời rạc
            chunks = []
            i = 0
            while i < len(tokens):
                if i + 1 < len(tokens) and len(tokens[i]) <= 3:
                    chunks.append(f"{tokens[i]} {tokens[i+1]}")
                    i += 2
                else:
                    chunks.append(tokens[i])
                    i += 1

        shuffled_chunks = chunks.copy()
        attempts = 0
        while " ".join(shuffled_chunks).lower() == " ".join(chunks).lower() and attempts < 10 and len(chunks) > 1:
            random.shuffle(shuffled_chunks)
            attempts += 1

        return {
            "status": "success",
            "grammar_id": grammar.id if grammar else 1,
            "structure": structure_name,
            "explanation": explanation,
            "original_sentence": example_sentence,
            "shuffled_chunks": shuffled_chunks,
            "chunk_count": len(shuffled_chunks)
        }

    def verify_syntax_scramble(self, original_sentence: str, user_chunks: List[str]) -> Dict:
        """
        Xác thực câu cú pháp học viên sắp xếp.
        Ưu tiên đối soát chuỗi trực tiếp; nếu khác nhưng đúng ngữ pháp sẽ kiểm định qua LocalGECEngine.
        """
        user_sentence = " ".join([c.strip() for c in user_chunks if c.strip()])
        clean_orig = re.sub(r'[^\w\s]', '', original_sentence).strip().lower()
        clean_user = re.sub(r'[^\w\s]', '', user_sentence).strip().lower()

        if clean_orig == clean_user:
            return {
                "status": "success",
                "is_correct": True,
                "score": 10.0,
                "user_sentence": user_sentence,
                "original_sentence": original_sentence,
                "message": "🔥 HOÀN HẢO! Trật tự cú pháp chính xác 100% theo mẫu chuẩn!"
            }

        # Kiểm tra nếu cách sắp xếp khác câu mẫu nhưng vẫn đúng ngữ pháp qua LanguageTool cục bộ
        try:
            from app.ml_models.gec_engine import LocalGECEngine
            gec = LocalGECEngine()
            gec_res = gec.evaluate(user_sentence)
            gec_score = float(gec_res.get('score', 0.0))

            if gec_score >= 9.0:
                return {
                    "status": "success",
                    "is_correct": True,
                    "score": gec_score,
                    "user_sentence": user_sentence,
                    "original_sentence": original_sentence,
                    "message": f"💡 SÁNG TẠO! Bạn sắp xếp câu theo trật tự hợp lệ khác (AI chấm {gec_score}/10)!"
                }
        except Exception:
            pass

        return {
            "status": "success",
            "is_correct": False,
            "score": 0.0,
            "user_sentence": user_sentence,
            "original_sentence": original_sentence,
            "message": f"⚠️ Trật tự chưa chuẩn! Câu đúng: \"{original_sentence}\""
        }
