import os
import sys
import json
from app.utils.gemini_helper import evaluate_english_skill

from app.ml_models.critique_synthesizer import get_critique_synthesizer

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

    COMMON_VERB_LEXICON = {
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'done', 'can', 'could', 'will', 'would', 'shall', 'should',
        'may', 'might', 'must', 'ought', 'need', 'needs', 'needed', 'needing', 'dare',
        'go', 'goes', 'went', 'gone', 'going', 'come', 'comes', 'came', 'coming',
        'make', 'makes', 'made', 'making', 'take', 'takes', 'took', 'taken', 'taking',
        'get', 'gets', 'got', 'gotten', 'getting', 'give', 'gives', 'gave', 'given', 'giving',
        'see', 'sees', 'saw', 'seen', 'seeing', 'know', 'knows', 'knew', 'known', 'knowing',
        'think', 'thinks', 'thought', 'thinking', 'look', 'looks', 'looked', 'looking',
        'want', 'wants', 'wanted', 'wanting', 'use', 'uses', 'used', 'using',
        'find', 'finds', 'found', 'finding', 'tell', 'tells', 'told', 'telling',
        'ask', 'asks', 'asked', 'asking', 'work', 'works', 'worked', 'working',
        'seem', 'seems', 'seemed', 'seeming', 'feel', 'feels', 'felt', 'feeling',
        'try', 'tries', 'tried', 'trying', 'leave', 'leaves', 'left', 'leaving',
        'call', 'calls', 'called', 'calling', 'become', 'becomes', 'became', 'becoming',
        'put', 'puts', 'putting', 'mean', 'means', 'meant', 'meaning',
        'keep', 'keeps', 'kept', 'keeping', 'let', 'lets', 'letting',
        'begin', 'begins', 'began', 'begun', 'beginning', 'show', 'shows', 'showed', 'shown', 'showing',
        'hear', 'hears', 'heard', 'hearing', 'play', 'plays', 'played', 'playing',
        'run', 'runs', 'ran', 'running', 'move', 'moves', 'moved', 'moving',
        'like', 'likes', 'liked', 'liking', 'live', 'lives', 'lived', 'living',
        'believe', 'believes', 'believed', 'believing', 'hold', 'holds', 'held', 'holding',
        'bring', 'brings', 'brought', 'bringing', 'happen', 'happens', 'happened', 'happening',
        'write', 'writes', 'wrote', 'written', 'writing', 'provide', 'provides', 'provided', 'providing',
        'sit', 'sits', 'sat', 'sitting', 'stand', 'stands', 'stood', 'standing',
        'lose', 'loses', 'lost', 'losing', 'pay', 'pays', 'paid', 'paying',
        'meet', 'meets', 'met', 'meeting', 'include', 'includes', 'included', 'including',
        'continue', 'continues', 'continued', 'continuing', 'set', 'sets', 'setting',
        'learn', 'learns', 'learned', 'learning', 'change', 'changes', 'changed', 'changing',
        'lead', 'leads', 'led', 'leading', 'understand', 'understands', 'understood', 'understanding',
        'watch', 'watches', 'watched', 'watching', 'follow', 'follows', 'followed', 'following',
        'stop', 'stops', 'stopped', 'stopping', 'create', 'creates', 'created', 'creating',
        'speak', 'speaks', 'spoke', 'spoken', 'speaking', 'read', 'reads', 'reading',
        'allow', 'allows', 'allowed', 'allowing', 'add', 'adds', 'added', 'adding',
        'spend', 'spends', 'spent', 'spending', 'grow', 'grows', 'grew', 'grown', 'growing',
        'open', 'opens', 'opened', 'opening', 'walk', 'walks', 'walked', 'walking',
        'win', 'wins', 'won', 'winning', 'offer', 'offers', 'offered', 'offering',
        'remember', 'remembers', 'remembered', 'remembering', 'love', 'loves', 'loved', 'loving',
        'consider', 'considers', 'considered', 'considering', 'appear', 'appears', 'appeared', 'appearing',
        'buy', 'buys', 'bought', 'buying', 'wait', 'waits', 'waited', 'waiting',
        'serve', 'serves', 'served', 'serving', 'die', 'dies', 'died', 'dying',
        'send', 'sends', 'sent', 'sending', 'expect', 'expects', 'expected', 'expecting',
        'build', 'builds', 'built', 'building', 'stay', 'stays', 'stayed', 'staying',
        'fall', 'falls', 'fell', 'fallen', 'falling', 'cut', 'cuts', 'cutting',
        'reach', 'reaches', 'reached', 'reaching', 'kill', 'kills', 'killed', 'killing',
        'remain', 'remains', 'remained', 'remaining', 'suggest', 'suggests', 'suggested', 'suggesting',
        'raise', 'raises', 'raised', 'raising', 'pass', 'passes', 'passed', 'passing',
        'sell', 'sells', 'sold', 'selling', 'require', 'requires', 'required', 'requiring',
        'report', 'reports', 'reported', 'reporting', 'decide', 'decides', 'decided', 'deciding',
        'pull', 'pulls', 'pulled', 'pulling', 'eat', 'eats', 'ate', 'eaten', 'eating',
        'drink', 'drinks', 'drank', 'drunk', 'drinking', 'sleep', 'sleeps', 'slept', 'sleeping',
        'swim', 'swims', 'swam', 'swum', 'swimming', 'fly', 'flies', 'flew', 'flown', 'flying',
        'drive', 'drives', 'drove', 'driven', 'driving', 'teach', 'teaches', 'taught', 'teaching',
        'study', 'studies', 'studied', 'studying', 'produce', 'produces', 'produced', 'producing',
        'occur', 'occurs', 'occurred', 'occurring', 'react', 'reacts', 'reacted', 'reacting',
        'facilitate', 'facilitates', 'facilitated', 'facilitating', 'erase', 'erases', 'erased', 'erasing',
        'arrive', 'arrives', 'arrived', 'arriving', 'achieve', 'achieves', 'achieved', 'achieving',
        'contain', 'contains', 'contained', 'containing', 'cause', 'causes', 'caused', 'causing',
        'solve', 'solves', 'solved', 'solving', 'improve', 'improves', 'improved', 'improving',
        'reduce', 'reduces', 'reduced', 'reducing', 'increase', 'increases', 'increased', 'increasing',
        'develop', 'develops', 'developed', 'developing', 'protect', 'protects', 'protected', 'protecting',
        'support', 'supports', 'supported', 'supporting', 'agree', 'agrees', 'agreed', 'agreeing',
        'prepare', 'prepares', 'prepared', 'preparing', 'enjoy', 'enjoys', 'enjoyed', 'enjoying',
        'connect', 'connects', 'connected', 'connecting', 'complete', 'completes', 'completed', 'completing',
        'establish', 'establishes', 'established', 'establishing', 'exist', 'exists', 'existed', 'existing',
        'explain', 'explains', 'explained', 'explaining', 'help', 'helps', 'helped', 'helping',
        'talk', 'talks', 'talked', 'talking', 'listen', 'listens', 'listened', 'listening',
        'fight', 'fights', 'fought', 'fighting', 'travel', 'travels', 'traveled', 'travelling',
        'jump', 'jumps', 'jumped', 'jumping', 'catch', 'catches', 'caught', 'catching',
        'break', 'breaks', 'broke', 'broken', 'breaking', 'choose', 'chooses', 'chose', 'chosen', 'choosing',
        'wear', 'wears', 'wore', 'worn', 'wearing', 'draw', 'draws', 'drew', 'drawn', 'drawing',
        'sing', 'sings', 'sang', 'sung', 'singing', 'dance', 'dances', 'danced', 'dancing',
        'ride', 'rides', 'rode', 'ridden', 'riding', 'throw', 'throws', 'threw', 'thrown', 'throwing',
        'burn', 'burns', 'burned', 'burnt', 'burning', 'wake', 'wakes', 'woke', 'woken', 'waking',
        'hide', 'hides', 'hid', 'hidden', 'hiding', 'shut', 'shuts', 'shutting',
        'ring', 'rings', 'rang', 'rung', 'ringing', 'shake', 'shakes', 'shook', 'shaken', 'shaking',
        'shoot', 'shoots', 'shot', 'shooting', 'smell', 'smells', 'smelled', 'smelling',
        'steal', 'steals', 'stole', 'stolen', 'stealing', 'sweep', 'sweeps', 'swept', 'sweeping',
        'tear', 'tears', 'tore', 'torn', 'tearing', 'wish', 'wishes', 'wished', 'wishing',
        'hope', 'hopes', 'hoped', 'hoping', 'avoid', 'avoids', 'avoided', 'avoiding',
        'manage', 'manages', 'managed', 'managing', 'perform', 'performs', 'performed', 'performing',
        'prevent', 'prevents', 'prevented', 'preventing', 'treat', 'treats', 'treated', 'treating',
        'visit', 'visits', 'visited', 'visiting', 'control', 'controls', 'controlled', 'controlling',
        'depend', 'depends', 'depended', 'depending', 'express', 'expresses', 'expressed', 'expressing',
        'introduce', 'introduces', 'introduced', 'introducing', 'operate', 'operates', 'operated', 'operating',
        'replace', 'replaces', 'replaced', 'replacing', 'survive', 'survives', 'survived', 'surviving',
        'succeed', 'succeeds', 'succeeded', 'succeeding', 'participate', 'participates', 'participated', 'participating',
        'recognize', 'recognizes', 'recognized', 'recognizing', 'release', 'releases', 'released', 'releasing',
        'respond', 'responds', 'responded', 'responding', 'reveal', 'reveals', 'revealed', 'revealing',
        'satisfy', 'satisfies', 'satisfied', 'satisfying', 'examine', 'examines', 'examined', 'examining',
        'investigate', 'investigates', 'investigated', 'investigating', 'observe', 'observes', 'observed', 'observing',
        'practice', 'practices', 'practiced', 'practicing', 'code', 'codes', 'coded', 'coding'
    }

    def _has_predicate_verb(self, tokens: list) -> bool:
        """Kiểm tra xem câu có chứa động từ chính (vị ngữ) hoặc trợ động từ hay không."""
        for t in tokens:
            w = t.lower()
            if w in self.COMMON_VERB_LEXICON:
                return True
            # Kiểm tra hình thái đuôi động từ
            if len(w) > 4:
                if w.endswith(('ize', 'ised', 'ized', 'ising', 'izing', 'ify', 'ified', 'ifying', 'ate', 'ated', 'ating')):
                    return True
                if w.endswith('ed') and w not in {'red', 'bed', 'shed', 'seed', 'weed', 'feed', 'tired', 'bored', 'naked'}:
                    return True
                if w.endswith('ing') and w not in {'morning', 'evening', 'something', 'nothing', 'everything', 'ceiling', 'feeling'}:
                    return True
        return False

    def evaluate(self, text: str, user_level: str = "Beginner") -> dict:
        """
        Phân tích ngữ pháp chuyên sâu:
        - Kiểm tra tính hoàn chỉnh của câu (câu trọn vẹn vs. cụm từ rời rạc / từ đơn lẻ)
        - Phát hiện vị trí sai (offset, length)
        - Phân loại luật ngữ pháp vi phạm (rule_id, category)
        - Gợi ý từ thay thế (replacements)
        - Tự động sửa thành câu hoàn chỉnh (corrected_text)
        - Tính điểm khoa học theo mật độ lỗi và tính toàn vẹn cú pháp
        """
        if not text or len(text.strip()) == 0:
            msg = "[ĐÁNH GIÁ TỔNG QUAN]\nBạn chưa nhập nội dung nào. Hãy nhập một câu tiếng Anh hoàn chỉnh có chứa từ vựng nhiệm vụ."
            return {
                "score": 0.0,
                "feedback": msg,
                "master_g_critique": msg,
                "corrected_text": "",
                "errors": [],
                "error_count": 0,
                "is_fragment": True,
                "needs_llm_escalation": False,
                "uncertainty_score": 0.0,
                "escalation_reason": "Văn bản rỗng"
            }

        if not self.is_active:
            if not self._ensure_loaded():
                return self._trigger_fallback(text, "Local Brain Offline")

        try:
            clean_text = text.strip()
            # 1. Phân tích ngữ pháp hình thức bằng LanguageTool
            matches = self._lt_tool.check(clean_text)
            corrected = self._lt_tool.correct(clean_text).strip()

            words = clean_text.split()
            word_count = max(1, len(words))
            raw_tokens = [w.strip(".,!?;:\"'()[]{}").lower() for w in words if w.strip(".,!?;:\"'()[]{}")]

            # 2. Kiểm tra tính toàn vẹn của câu (Sentence Completeness Check)
            is_fragment = False
            has_verb = self._has_predicate_verb(raw_tokens)
            error_details = []
            total_penalty = 0.0

            # Trường hợp A: Người dùng chỉ nhập 1 từ đơn lẻ
            if len(raw_tokens) <= 1:
                is_fragment = True
                single_word = raw_tokens[0] if raw_tokens else clean_text
                error_details.append({
                    "rule_id": "SINGLE_WORD_INPUT",
                    "message": "Câu chưa hoàn chỉnh: Bạn mới chỉ nhập một từ đơn lẻ. Nhiệm vụ yêu cầu đặt một câu trọn vẹn (có đầy đủ Chủ ngữ và Vị ngữ).",
                    "offset": 0,
                    "error_length": len(clean_text),
                    "context": clean_text,
                    "replacements": [f"I learned about {single_word} today.", f"This is a {single_word}."],
                    "category": "GRAMMAR"
                })
                total_penalty += 7.0
                corrected = f"This is a {single_word}."

            # Trường hợp B: Cụm từ ngắn (2-4 từ) hoặc câu không hề có bất kỳ động từ nào
            elif not has_verb:
                is_fragment = True
                error_details.append({
                    "rule_id": "SENTENCE_FRAGMENT",
                    "message": "Cụm từ chưa thành câu (Sentence Fragment): Bạn mới chỉ nhập một cụm từ rời rạc, thiếu động từ chính (vị ngữ) để cấu thành một câu tiếng Anh hoàn chỉnh.",
                    "offset": 0,
                    "error_length": len(clean_text),
                    "context": clean_text,
                    "replacements": [
                        f"The {clean_text.lower().rstrip('.')} occurs rapidly.",
                        f"Scientists observed a {clean_text.lower().rstrip('.')}."
                    ],
                    "category": "GRAMMAR"
                })
                total_penalty += 6.0
                # Gợi ý một câu hoàn chỉnh mẫu chứa cụm từ đó
                phrase_core = clean_text.rstrip('.?!')
                if phrase_core.lower().startswith(('the ', 'a ', 'an ', 'this ', 'that ')):
                    corrected = f"{phrase_core} occurs rapidly."
                else:
                    corrected = f"The {phrase_core.lower()} occurs in the experiment."

            # 3. Phân tích các lỗi từ LanguageTool
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

                # Phạt tỉ lệ theo độ dài câu
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

            # Điểm từ 0.0 đến 10.0 (Nếu là fragment, điểm tối đa bị giới hạn ở 4.0)
            base_score = round(10.0 - total_penalty, 1)
            if is_fragment:
                score = max(1.0, min(4.0, base_score))
            else:
                score = max(0.0, min(10.0, base_score))

            # Đảm bảo câu chuẩn đề xuất có viết hoa đầu câu và dấu chấm kết thúc
            if corrected:
                corrected = corrected[0].upper() + corrected[1:]
                if not corrected.endswith(('.', '!', '?')):
                    corrected += '.'

            # 4. Tạo phản hồi nhận xét sư phạm chi tiết (Pedagogical Feedback)
            if len(error_details) == 0:
                feedback = "[ĐÁNH GIÁ TỔNG QUAN]\nCâu văn hoàn chỉnh, cấu trúc ngữ pháp chuẩn xác 100%."
            else:
                feedback_lines = [f"[Tìm thấy {len(error_details)} điểm cần lưu ý (Điểm: {score}/10)]:"]
                for i, err in enumerate(error_details[:4], 1):
                    rep_text = f" -> Gợi ý sửa: '{', '.join(err['replacements'])}'" if err['replacements'] else ""
                    feedback_lines.append(f"{i}. {err['message']}{rep_text}")

                if corrected != clean_text:
                    feedback_lines.append(f"\n=> Câu chuẩn đề xuất: \"{corrected}\"")

                feedback = "\n".join(feedback_lines)

            # 5. Kiểm tra Cổng Phân Luồng Thông Minh
            needs_escalation, uncertainty_score, reason = self._check_uncertainty(
                clean_text, word_count, len(error_details), total_penalty
            )

            # 6. Sinh nhận xét Master G Local (Đầy đủ tổng quan, chỉ rõ lỗi, có góp ý và dọn sạch icon)
            mock_res = {
                "score": score,
                "corrected_text": corrected,
                "errors": error_details,
                "is_fragment": is_fragment
            }
            synthesizer = get_critique_synthesizer()
            master_g_critique = synthesizer.synthesize(clean_text, mock_res, user_level=user_level)

            return {
                "score": score,
                "feedback": feedback,
                "master_g_critique": master_g_critique,
                "corrected_text": corrected,
                "errors": error_details,
                "error_count": len(error_details),
                "is_fragment": is_fragment,
                "needs_llm_escalation": needs_escalation,
                "uncertainty_score": uncertainty_score,
                "escalation_reason": reason
            }

        except Exception as e:
            print(f"[GEC ENGINE] Ngoại lệ khi phân tích câu: {e}. Kích hoạt Fallback.")
            return self._trigger_fallback(text, str(e))

    def _check_uncertainty(self, text: str, word_count: int, error_count: int, total_penalty: float):
        """
        Đo lường độ bất định (Uncertainty) và quyết định xem câu có cần chuyển giao cho LLM hay không:
        Returns: (needs_llm_escalation: bool, uncertainty_score: float, reason: str)
        """
        # 1. Câu dài phức hợp (> 30 từ) chứa nhiều lỗi ngữ pháp lồng nhau
        if word_count > 30 and error_count >= 5:
            return True, 0.85, "Câu phức dài với nhiều mệnh đề lồng nhau phức tạp."

        # 2. Câu quá ngắn hoặc mật độ lỗi dị thường (từ gõ bừa OOD)
        if word_count <= 3 and total_penalty > 8.0:
            return True, 0.80, "Mật độ lỗi dị thường hoặc từ ngữ nằm ngoài phân phối chuẩn."

        # 3. Thông thường: AI Local hoàn toàn làm chủ (85 - 90% trường hợp)
        return False, 0.15, "AI Local tự chủ hoàn toàn, không cần LLM."

    def _trigger_fallback(self, text: str, reason: str) -> dict:
        """Fallback LLM khi có ngoại lệ hệ thống hoặc độ bất định vượt ngưỡng."""
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
                "master_g_critique": final_feedback,
                "corrected_text": llm_result.get("corrected_text", text),
                "errors": [],
                "error_count": 0,
                "needs_llm_escalation": True,
                "uncertainty_score": 1.0,
                "escalation_reason": f"Fallback kích hoạt: {reason}"
            }
        except Exception as e:
            print(f"[GEC ENGINE] Lỗi nghiêm trọng khi Fallback: {e}")
            msg = "[SYSTEM WARNING] Lò phản ứng AI cạn kiệt. Master G đi vắng. Tạm cho 5 điểm."
            return {
                "score": 5.0,
                "feedback": msg,
                "master_g_critique": msg,
                "corrected_text": text,
                "errors": [],
                "error_count": 0,
                "needs_llm_escalation": True,
                "uncertainty_score": 1.0,
                "escalation_reason": f"Lỗi nghiêm trọng: {e}"
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