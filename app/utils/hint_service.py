import re
import json
import random
from typing import Dict, List, Optional
from app import db
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.ml_models.scramble_engine import LocalScrambleEngine
from app.ml_models.vocab_classifier import VocabCEFRClassifier
from app.utils.grammar_quiz_generator import generate_grammar_collocations

scramble_engine = LocalScrambleEngine()
cefr_classifier = VocabCEFRClassifier()


def clean_str(val: Optional[str]) -> str:
    """Loại bỏ triệt để các ký tự markdown thô (asterisk, backtick, hash, bullet...)"""
    if not val:
        return ""
    text = str(val).strip()
    text = re.sub(r'[*_#`~]', '', text)
    text = re.sub(r'^[•\-\d\.]+\s*', '', text)
    return text.strip()


def highlight_word_in_sentence(sentence: str, target: str) -> str:
    """Tô đậm từ mục tiêu bằng thẻ span styled màu neon thay vì dùng markdown asterisk"""
    if not sentence or not target:
        return sentence or ""
    pattern = re.compile(rf'\b({re.escape(target)})\b', re.IGNORECASE)
    return pattern.sub(r'<span style="color: var(--neon-pink); font-weight: 700; text-decoration: underline;">\1</span>', sentence)


def get_offline_vocab_hint(word: str, meaning: str = "", cefr: str = "B1") -> Dict:
    """
    Tạo gợi ý dự phòng cục bộ (100% Offline Non-LLM) khi không có Internet.
    Lấy từ vựng làm trung tâm và dựng câu chuẩn mực dựa trên hình thái từ.
    """
    clean_w = word.strip()
    w_lower = clean_w.lower()
    clean_m = clean_str(meaning)
    if not clean_m or clean_m == "Từ vựng mục tiêu":
        try:
            v_match = Vocabulary.query.filter(db.func.lower(Vocabulary.word) == w_lower).first()
            if v_match and v_match.meaning:
                clean_m = clean_str(v_match.meaning)
                if v_match.cefr_level:
                    cefr = v_match.cefr_level
        except Exception:
            pass
    if not clean_m:
        clean_m = "Từ vựng mục tiêu"

    # Kho từ vựng mẫu phổ biến được biên soạn chuyên sâu
    curated_knowledge = {
        "arrogant": {
            "meaning": "Kiêu ngạo, ngạo mạn, tự phụ",
            "pos": "Tính từ (Adjective)",
            "collocations": ["arrogant attitude", "too arrogant to admit", "sound arrogant", "arrogant behavior"],
            "main_sentence": "He was too arrogant to admit his mistake.",
            "main_sentence_vi": "Anh ấy đã quá kiêu ngạo để thừa nhận sai lầm của mình.",
            "extra_sentences": [
                {"en": "His arrogant behavior annoyed the entire team.", "vi": "Thái độ kiêu ngạo của anh ấy khiến cả đội khó chịu."},
                {"en": "Don't sound arrogant when speaking about your achievements.", "vi": "Đừng tỏ ra kiêu ngạo khi nói về những thành tựu của bạn."}
            ],
            "formula": "S + be / seem / sound + arrogant (+ to V / about N)",
            "tip": "Tính từ chỉ thái độ tiêu cực. Thường kết hợp với 'too arrogant to V' (quá kiêu ngạo để làm gì) hoặc đi kèm danh từ 'attitude/behavior'."
        },
        "resilient": {
            "meaning": "Kiên cường, bền bỉ, có khả năng phục hồi nhanh",
            "pos": "Tính từ (Adjective)",
            "collocations": ["resilient economy", "highly resilient", "stay resilient"],
            "main_sentence": "The local community remained resilient after the disaster.",
            "main_sentence_vi": "Cộng đồng địa phương vẫn kiên cường sau thảm họa.",
            "extra_sentences": [
                {"en": "She proved to be resilient during difficult times.", "vi": "Cô ấy đã chứng tỏ sự kiên cường trong những giai đoạn khó khăn."}
            ],
            "formula": "S + remain / be + resilient (+ to / against N)",
            "tip": "Tính từ tích cực, chỉ khả năng chống chịu và vượt qua thử thách."
        },
        "ubiquitous": {
            "meaning": "Phổ biến ở khắp mọi nơi, nhan nhản",
            "pos": "Tính từ (Adjective)",
            "collocations": ["ubiquitous influence", "become ubiquitous", "almost ubiquitous"],
            "main_sentence": "Smartphones have become ubiquitous in modern daily life.",
            "main_sentence_vi": "Điện thoại thông minh đã trở nên phổ biến khắp nơi trong đời sống hiện đại.",
            "extra_sentences": [
                {"en": "Coffee shops are ubiquitous in this bustling city.", "vi": "Các quán cà phê có mặt ở khắp mọi nơi tại thành phố nhộn nhịp này."}
            ],
            "formula": "S + become / be + ubiquitous (+ in / across N)",
            "tip": "Tính từ học thuật C1 miêu tả sự hiện diện rộng khắp."
        }
    }

    if w_lower in curated_knowledge:
        data = curated_knowledge[w_lower]
        data["word"] = clean_w
        data["cefr"] = cefr
        return data

    # Heuristic sinh câu cục bộ theo hậu tố từ vựng (Morphological heuristic)
    is_adj = any(w_lower.endswith(sfx) for sfx in ['ant', 'ent', 'ive', 'ous', 'ful', 'able', 'ible', 'al', 'ic', 'less'])
    is_verb = any(w_lower.endswith(sfx) for sfx in ['ize', 'ise', 'ate', 'ify', 'en'])

    if is_adj:
        pos = "Tính từ (Adjective)"
        collocs = [f"{clean_w} attitude", f"too {clean_w} to ignore", f"seem {clean_w}"]
        main_sen = f"He was too {clean_w} to accept the advice."
        main_vi = f"Anh ấy đã quá {clean_m.lower()} để chấp nhận lời khuyên."
        extras = [
            {"en": f"His {clean_w} manner made an impression on everyone.", "vi": f"Phong thái {clean_m.lower()} của anh ấy đã để lại ấn tượng cho mọi người."}
        ]
        formula = f"S + be / seem + {clean_w} (+ to V / in N)"
        tip = f"Tính từ '{clean_w}' bổ nghĩa cho danh từ hoặc đứng sau các liên hệ động từ (be, feel, seem, become)."
    elif is_verb:
        pos = "Động từ (Verb)"
        collocs = [f"try to {clean_w}", f"{clean_w} effectively", f"need to {clean_w}"]
        main_sen = f"They decided to {clean_w} the plan immediately."
        main_vi = f"Họ quyết định {clean_m.lower()} kế hoạch ngay lập tức."
        extras = [
            {"en": f"You should {clean_w} carefully to avoid unexpected errors.", "vi": f"Bạn nên {clean_m.lower()} cẩn thận để tránh lỗi phát sinh."}
        ]
        formula = f"S + {clean_w} + Object (+ Adverb)"
        tip = f"Động từ '{clean_w}' diễn tả hành động cụ thể, hãy chú ý chia đúng thì ngữ pháp."
    else:
        pos = "Danh từ / Từ vựng (Noun)"
        collocs = [f"important {clean_w}", f"the role of {clean_w}", f"understand {clean_w}"]
        main_sen = f"The {clean_w} played a key role in our project."
        main_vi = f"{clean_m.capitalize()} đóng vai trò then chốt trong dự án của chúng tôi."
        extras = [
            {"en": f"We need to evaluate this {clean_w} with great care.", "vi": f"Chúng ta cần đánh giá {clean_m.lower()} này với sự cẩn trọng cao."}
        ]
        formula = f"The + {clean_w} + Verb + Object / S + Verb + {clean_w}"
        tip = f"Từ vựng '{clean_w}' ({clean_m}) có thể đóng vai trò làm chủ ngữ hoặc tân ngữ trong câu."

    return {
        "word": clean_w,
        "meaning": clean_m,
        "cefr": cefr,
        "pos": pos,
        "collocations": collocs,
        "main_sentence": main_sen,
        "main_sentence_vi": main_vi,
        "extra_sentences": extras,
        "formula": formula,
        "tip": tip
    }


def query_llm_for_vocab_hint(word: str, meaning: str = "", cefr: str = "B1") -> Optional[Dict]:
    """
    Truy vấn Gemini với chỉ thị nghiêm ngặt để sinh ngữ cảnh câu quanh từ vựng mục tiêu.
    Chỉ nhận JSON thuần túy, tuyệt đối cấm markdown asterisks hay văn phong chào hỏi thừa thãi.
    """
    from app.utils.gemini_helper import call_gemini_with_retry

    clean_w = word.strip()
    clean_m = clean_str(meaning) or "Từ vựng tiếng Anh"

    system_instruction = (
        "Bạn là Chuyên gia Ngôn ngữ học kiêm Tác tử Master G trong hệ thống Global Fluent. "
        "Nhiệm vụ: Trợ giúp học viên đặt câu với TỪ VỰNG MỤC TIÊU làm trung tâm tuyệt đối. "
        "YÊU CẦU NGHIÊM NGẶT: "
        "1. Toàn bộ các câu ví dụ và cụm từ PHẢI chứa đúng từ vựng mục tiêu. "
        "2. TUYỆT ĐỐI KHÔNG sử dụng ký tự lạ, không dùng dấu sao markdown (** hay *), không dùng dấu thăng (#). "
        "3. KHÔNG chào hỏi, không xã giao, không thêm văn bản dẫn xuất bên ngoài JSON. "
        "4. Chỉ trả về duy nhất 1 chuỗi JSON hợp lệ theo đúng cấu trúc yêu cầu."
    )

    prompt = f"""
Hãy tạo tài liệu gợi ý đặt câu cho từ vựng mục tiêu: "{clean_w}" (Nghĩa tiếng Việt: {clean_m}, Trình độ: {cefr}).

ĐỊNH DẠNG JSON BẮT BUỘC:
{{
    "word": "{clean_w}",
    "meaning": "{clean_m}",
    "pos": "<từ loại tiếng Việt, ví dụ: Tính từ (Adjective), Động từ (Verb), Danh từ (Noun)>",
    "collocations": ["<cụm từ hay đi kèm 1 chứa hoặc liên quan {clean_w}>", "<cụm từ 2>", "<cụm từ 3>"],
    "main_sentence": "<1 câu tiếng Anh chuẩn mực, tự nhiên, dài từ 7-12 từ chứa từ '{clean_w}' để làm bài tập sắp xếp câu>",
    "main_sentence_vi": "<Bản dịch tiếng Việt chuẩn xác của câu main_sentence>",
    "extra_sentences": [
        {{"en": "<Câu ví dụ ứng dụng khác 1 chứa '{clean_w}'>", "vi": "<Dịch nghĩa tiếng Việt 1>"}},
        {{"en": "<Câu ví dụ ứng dụng khác 2 chứa '{clean_w}'>", "vi": "<Dịch nghĩa tiếng Việt 2>"}}
    ],
    "formula": "<Công thức đặt câu, ví dụ: S + be + {clean_w} + to V>",
    "tip": "<1 lời khuyên ngắn gọn bằng tiếng Việt về sắc thái hoặc lưu ý khi dùng từ '{clean_w}'>"
}}
"""
    try:
        raw_response = call_gemini_with_retry(prompt, system_instruction=system_instruction, enforce_json=True)
        if not raw_response:
            return None

        # Làm sạch chuỗi JSON nếu có code block thừa
        cleaned_json = raw_response.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r'^```(?:json)?\s*', '', cleaned_json)
            cleaned_json = re.sub(r'\s*```$', '', cleaned_json)

        parsed = json.loads(cleaned_json)

        main_sen = clean_str(parsed.get("main_sentence", ""))
        # Xác minh câu chính có chứa từ mục tiêu hay không (case-insensitive)
        if clean_w.lower() not in main_sen.lower():
            return None

        # Làm sạch toàn bộ các chuỗi trong JSON
        res_data = {
            "word": clean_w,
            "meaning": clean_str(parsed.get("meaning")) or clean_m,
            "cefr": cefr,
            "pos": clean_str(parsed.get("pos")) or "Từ vựng (Vocabulary)",
            "collocations": [clean_str(c) for c in parsed.get("collocations", []) if clean_str(c)][:4],
            "main_sentence": main_sen,
            "main_sentence_vi": clean_str(parsed.get("main_sentence_vi", "")),
            "extra_sentences": [
                {"en": clean_str(item.get("en")), "vi": clean_str(item.get("vi"))}
                for item in parsed.get("extra_sentences", [])
                if clean_str(item.get("en"))
            ][:2],
            "formula": clean_str(parsed.get("formula", "")),
            "tip": clean_str(parsed.get("tip", ""))
        }
        return res_data
    except Exception as e:
        print(f"[HINT SERVICE] Gemini hint generation fallback: {e}")
        return None


def generate_grammar_hint(target_text: str) -> Dict:
    """Tạo gợi ý cho phân hệ ngữ pháp với cấu trúc mục tiêu làm trung tâm"""
    clean_target = clean_str(target_text)
    g_match = Grammar.query.filter(Grammar.structure.ilike(f"%{clean_target}%")).first()
    if not g_match:
        g_match = Grammar.query.first()

    structure_name = g_match.structure if g_match else clean_target
    explanation = g_match.explanation if g_match else "Cấu trúc ngữ pháp chuẩn"
    example_sentence = g_match.example if g_match and g_match.example else "She has worked here for three years."
    cefr = g_match.cefr_level if g_match else "B1"

    collocations = generate_grammar_collocations(structure_name, explanation, example_sentence)

    # Sử dụng thuật toán xáo trộn câu cú pháp
    scramble_res = scramble_engine.scramble_sentence(example_sentence)

    return {
        "mode": "grammar",
        "word": structure_name,
        "meaning": explanation,
        "cefr": cefr,
        "pos": "Cấu trúc Ngữ pháp (Grammar Structure)",
        "collocations": collocations[:4],
        "main_sentence": example_sentence,
        "main_sentence_vi": "Ví dụ chuẩn ứng dụng cấu trúc trong thực tế.",
        "extra_sentences": [
            {"en": f"Make sure to follow the pattern: {structure_name}", "vi": f"Đảm bảo tuân thủ đúng trật tự: {structure_name}"}
        ],
        "formula": structure_name,
        "tip": f"Áp dụng chính xác quy tắc: {explanation}",
        "scramble": scramble_res
    }


# Bí danh tương thích cho hệ thống gợi ý ngữ pháp offline
get_offline_grammar_hint = generate_grammar_hint


def render_hint_html(data: Dict) -> str:
    """
    Sinh giao diện HTML cực đẹp, chuẩn retro/cyberpunk, không chứa bất kỳ ký tự markdown thô nào.
    Tích hợp các mảnh ghép cú pháp (Syntax Scramble) từ thuật toán hệ thống và nút áp dụng tức thì.
    """
    word = data.get("word", "")
    meaning = data.get("meaning", "")
    cefr = data.get("cefr", "B1")
    pos = data.get("pos", "")
    main_sentence = data.get("main_sentence", "")
    main_sentence_vi = data.get("main_sentence_vi", "")
    collocations = data.get("collocations", [])
    extra_sentences = data.get("extra_sentences", [])
    formula = data.get("formula", "")
    tip = data.get("tip", "")
    scramble = data.get("scramble", {})
    shuffled_chunks = scramble.get("shuffled_chunks", [])

    escaped_main = main_sentence.replace("'", "\\'").replace('"', '&quot;')
    highlighted_main = highlight_word_in_sentence(main_sentence, word)

    # Render các nút mảnh ghép cú pháp từ thuật toán Scramble
    chunks_html = ""
    for ch in shuffled_chunks:
        esc_ch = ch.replace("'", "\\'").replace('"', '&quot;')
        chunks_html += f"""
        <button type="button" class="pixel-btn" onclick="insertChunkToInput('{esc_ch}')" 
                style="background: rgba(30, 41, 59, 0.9); border: 1.5px solid var(--neon-cyan); color: #fff; padding: 6px 12px; font-size: 11px; border-radius: 6px; cursor: pointer; transition: 0.15s; font-family: var(--text-mono);"
                title="Bấm để ghép mảnh này vào ô bài làm">
            {ch}
        </button>
        """

    # Render cụm từ collocations
    colloc_html = ""
    for c in collocations:
        if isinstance(c, dict):
            c_text = c.get("collocation", "") or c.get("text", "")
            c_mean = c.get("meaning", "")
            disp = f"{c_text} ({c_mean})" if c_mean else c_text
        else:
            disp = str(c)
        if not disp or disp == "undefined":
            continue
        colloc_html += f"""
        <span style="display: inline-block; background: rgba(236, 72, 153, 0.15); border: 1px solid var(--neon-pink); color: #f472b6; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-family: var(--text-mono); font-weight: 600;">
            🔗 {disp}
        </span>
        """

    # Render câu ví dụ bổ sung
    extras_html = ""
    for ex in extra_sentences:
        ex_en = highlight_word_in_sentence(ex.get("en", ""), word)
        ex_vi = ex.get("vi", "")
        extras_html += f"""
        <div style="background: rgba(0,0,0,0.25); border-left: 2px solid var(--neon-cyan); padding: 6px 10px; border-radius: 4px; margin-bottom: 6px;">
            <div style="font-size: 13px; color: #f1f5f9; font-weight: 500;">• {ex_en}</div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px; font-style: italic;">{ex_vi}</div>
        </div>
        """

    html = f"""
    <div style="display: flex; flex-direction: column; gap: 12px; font-family: var(--text-main);">
        <!-- HEADER MỤC TIÊU TỪ VỰNG -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px dashed rgba(245, 158, 11, 0.4); padding-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="font-size: 15px;">🎯</span>
                <span style="font-size: 14px; font-weight: 700; color: var(--neon-cyan); letter-spacing: 0.5px; text-transform: uppercase;">MỤC TIÊU: {word}</span>
                <span style="background: rgba(245, 158, 11, 0.2); border: 1px solid var(--neon-amber); color: var(--neon-amber); font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-family: var(--text-mono);">{cefr}</span>
                <span style="font-size: 11px; color: #94a3b8;">({pos})</span>
            </div>
            <div style="font-size: 12px; color: #fef08a; font-weight: 600;">{meaning}</div>
        </div>

        <!-- THỬ THÁCH SẮP XẾP CÂU TỪ THUẬT TOÁN HỆ THỐNG -->
        <div style="background: rgba(0, 0, 0, 0.4); border: 1.5px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 12px; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);">
            <div style="font-size: 12px; font-weight: 700; color: var(--neon-amber); margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>🧩</span> THỬ THÁCH SẮP XẾP CÂU (ALGORITHM SYNTAX SCRAMBLE):
                </div>
                <span style="font-size: 10px; color: #94a3b8; font-weight: normal;">(Bấm mảnh ghép để thử đặt câu)</span>
            </div>

            <!-- Các mảnh ghép xáo trộn -->
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
                {chunks_html}
            </div>

            <!-- Câu chuẩn sau khi sắp xếp -->
            <div style="background: rgba(15, 23, 42, 0.85); border-left: 3px solid var(--pixel-green); padding: 10px 14px; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div style="font-size: 11px; color: var(--pixel-green); font-weight: 700; letter-spacing: 0.5px;">✨ CÂU HOÀN CHỈNH ĐỀ XUẤT:</div>
                    <button type="button" onclick="applyTemplateToInput('{escaped_main}')" 
                            style="background: var(--neon-cyan); border: none; color: #000; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; cursor: pointer;">
                        📝 DÙNG CÂU NÀY
                    </button>
                </div>
                <div style="font-size: 14px; color: #fff; font-weight: 600; line-height: 1.5;">"{highlighted_main}"</div>
                <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px; font-style: italic;">➔ Dịch nghĩa: {main_sentence_vi}</div>
            </div>
        </div>

        <!-- CỤM TỪ HAY ĐI KÈM (COLLOCATIONS) -->
        {f'''
        <div>
            <div style="font-size: 11px; font-weight: 700; color: var(--neon-pink); margin-bottom: 6px; letter-spacing: 0.3px;">
                🔗 CỤM TỪ HAY ĐI KÈM (COLLOCATIONS):
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                {colloc_html}
            </div>
        </div>
        ''' if collocations else ''}

        <!-- CÁC CÂU MẪU MỞ RỘNG -->
        {f'''
        <div>
            <div style="font-size: 11px; font-weight: 700; color: #67e8f9; margin-bottom: 6px; letter-spacing: 0.3px;">
                📖 CÂU VÍ DỤ ỨNG DỤNG MỞ RỘNG:
            </div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
                {extras_html}
            </div>
        </div>
        ''' if extra_sentences else ''}

        <!-- MẸO & CẤU TRÚC ĐẶT CÂU -->
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); padding: 8px 12px; border-radius: 6px; font-size: 12px; color: #e2e8f0; line-height: 1.5;">
            {f'<div style="margin-bottom: 4px;"><strong style="color: var(--neon-amber);">💡 Cấu trúc gợi ý:</strong> <code style="color: #67e8f9; background: rgba(0,0,0,0.4); padding: 1px 6px; border-radius: 4px; font-family: var(--text-mono);">{formula}</code></div>' if formula else ''}
            <div><strong style="color: #cbd5e1;">Mẹo:</strong> {tip}</div>
        </div>
    </div>
    """
    return html


def get_smart_hint(target_text: str, mode: str = "vocab") -> Dict:
    """
    API điều phối sinh gợi ý đặt câu thông minh:
    1. Lấy từ vựng/ngữ pháp mục tiêu làm trung tâm.
    2. Khai thác dữ liệu từ điển hệ thống và sinh câu ví dụ chuẩn mực.
    3. Áp dụng thuật toán Scramble Engine để xáo trộn cú pháp tạo mảnh ghép câu.
    4. Trả về giao diện sạch 100%, không chứa ký tự markdown thô.
    """
    clean_target = clean_str(target_text)
    if not clean_target:
        clean_target = "Arrogant" if mode == "vocab" else "Present Simple"

    if mode == "grammar":
        data = generate_grammar_hint(clean_target)
        data["html"] = render_hint_html(data)
        return data

    # Xử lý chế độ từ vựng (mode == "vocab")
    vocab_obj = Vocabulary.query.filter(db.func.lower(Vocabulary.word) == clean_target.lower()).first()
    word_val = vocab_obj.word if vocab_obj else clean_target
    meaning_val = vocab_obj.meaning if vocab_obj else "Từ vựng tiếng Anh"
    cefr_val = vocab_obj.cefr_level if vocab_obj else cefr_classifier.predict_cefr(word_val)

    # Ưu tiên bộ não thuật toán Cục bộ (Local Engine) để phản hồi siêu tốc (< 15ms) và không phụ thuộc LLM
    hint_data = get_offline_vocab_hint(word_val, meaning_val, cefr_val)

    # Ứng dụng thuật toán phân tách cú pháp & xáo trộn câu
    scramble_res = scramble_engine.scramble_sentence(hint_data["main_sentence"])
    hint_data["scramble"] = scramble_res

    # Sinh mã HTML sạch sẽ, bảo đảm không có ký tự lạ
    hint_data["html"] = render_hint_html(hint_data)
    hint_data["hint"] = hint_data["main_sentence"]  # Giữ backward-compatibility

    return hint_data
