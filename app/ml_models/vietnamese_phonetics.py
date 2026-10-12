"""
MODULE SINH PHIÊN ÂM TIẾNG VIỆT TỰ ĐỘNG (VIETNAMESE PHONETIC READING ENGINE)
Chuyển đổi âm vị học IPA và từ vựng tiếng Anh sang cách đọc phiên âm tiếng Việt chuẩn mực.
"""
import re
from typing import Optional, Dict

try:
    import eng_to_ipa as ipa_module
except ImportError:
    ipa_module = None

# 1. Từ điển tra cứu nhanh cho các từ vựng thường gặp trong TAP (Quick Overrides)
VIETNAMESE_PHONETIC_OVERRIDES: Dict[str, str] = {
    # Sinh vật & Động vật
    "cat": "két",
    "dog": "đooc",
    "bird": "bớt",
    "fish": "phích",
    "whisker": "uýt-x-cơ",
    "paw": "po",
    "claw": "clo",
    "muzzle": "mát-zồ",
    "fang": "pheng",
    "pupil": "piu-pồ",
    "fur": "phơ",
    "tail": "tây-ồ",
    "snout": "x-nao-t",
    "beak": "bic",
    "talon": "ta-lơn",
    "feather": "phe-đơ",
    "fin": "phin",
    "gill": "gil",
    "ear tuft": "ia-tắp-ph",
    "whisker pad": "uýt-cơ-pét",
    "tail tip": "tây-tip",
    "purring": "pơ-ring",
    "hissing": "hít-xinh",
    "crouching": "crao-chinh",
    "prowling": "prao-linh",
    "stretching": "x-trét-chinh",
    "grooming": "gru-minh",
    "napping": "nép-pinh",
    "fluffy": "phlắp-phi",
    "silky": "xiu-ki",
    "striped": "x-traip-t",
    "sleek": "x-lic",

    # Thực vật & Thiên nhiên
    "tree": "tri",
    "flower": "phlao-ơ",
    "leaf": "lip",
    "petal": "pe-tồ",
    "stem": "x-tem",
    "root": "rut",
    "branch": "b-ranch",
    "bark": "ba-c",
    "seed": "xít",
    "pistil": "pít-xtồ",
    "stamen": "x-tây-mơn",
    "sepal": "xe-pồ",
    "leaf vein": "lip-vein",
    "twig": "tuýt-g",
    "bud": "bắt-đ",
    "pollen": "pol-lơn",
    "plant": "plen-t",
    "grass": "gra-x",

    # Đồ vật & Công nghệ
    "laptop": "lép-tóp",
    "phone": "phôn",
    "backpack": "bách-pách",
    "book": "búc",
    "cup": "cắp",
    "chair": "che",
    "desk": "đéc-x-k",
    "table": "tây-bồ",
    "bottle": "bo-tồ",
    "keyboard": "ki-booc",
    "mouse": "mao-x",
    "screen": "x-crin",
    "keycap": "ki-kép",
    "trackpad": "trác-pét",
    "hinge": "hin-gi",
    "bezel": "be-zồ",
    "webcam": "oép-khem",
    "port": "pooc",
    "zipper": "díp-pơ",
    "buckle": "bắc-cồ",
    "seam": "xim",
    "strap": "x-trép",
    "car": "ca",
    "bicycle": "bai-xi-cồ",
    "headlight": "hét-lai-t",
    "tire": "tai-ơ",
    "mirror": "mi-rơ",
    "camera": "khem-rơ",
    "glasses": "gla-xịt",
    "watch": "oót-ch",
    "clock": "clooc",
    "lamp": "lem-p",
    "pen": "pen",
    "pencil": "pen-xồ",
    "door": "đo",
    "window": "uyn-đâu",
    "wall": "o-ồ",
    "floor": "phlo",

    # Con người & Sắc thái biểu cảm
    "human": "hiu-mơn",
    "person": "pơ-sơn",
    "student": "x-tiu-đần-t",
    "teacher": "ti-chơ",
    "face": "phây-x",
    "eye": "ai",
    "ear": "ia",
    "nose": "nâu-z",
    "mouth": "mao-th",
    "lip": "lip",
    "tongue": "tăng",
    "tooth": "tút",
    "teeth": "tít",
    "smile": "x-mai-ồ",
    "smirk": "x-mớc",
    "frown": "ph-rao-n",
    "grimace": "gri-mết-x",
    "wink": "uyn-k",
    "pout": "pao-t",
    "squint": "x-cuyn-t",
    "grin": "grin",
    "happy": "hép-pi",
    "sad": "xét",
    "blush": "b-lát-s",
    "yawn": "yo-n",
    "eyebrow": "ai-brao",
    "eyelash": "ai-lát-s",
    "cheek": "chic",
    "chin": "chin",
    "forehead": "pho-hét",
    "dimple": "đim-pồ",
    "wrinkle": "rin-cồ",
    "scowl": "x-cao-l",
    "gasp": "ga-x-p",
    "glare": "g-le-ơ",

    # Tính từ học thuật B2-C1
    "ecstatic": "éc-x-ta-tíc",
    "contemplative": "con-têm-plơ-típ",
    "perplexed": "pơ-pléc-x-t",
    "apprehensive": "ép-pri-hen-xíp",
    "serene": "xơ-rin",
    "skeptical": "x-kép-ti-cồ",
    "amused": "ơ-miu-z-đ",
    "focused": "phâu-cơ-x-t",
    "fatigued": "phơ-tíc-đ",
    "thoughtful": "thót-phu-ồ"
}

def clean_ipa(ipa_str: str) -> str:
    """Loại bỏ ký tự bao bọc và trọng âm"""
    s = ipa_str.strip()
    s = re.sub(r'[/\[\]ˈˌ]', '', s)
    return s

def ipa_to_vietnamese_phonetic(ipa_str: str, word: str = "") -> str:
    """
    Quy tắc chuyển đổi âm vị IPA sang âm tiết tiếng Việt có gạch nối
    """
    if not ipa_str:
        return word.lower()

    ipa_clean = clean_ipa(ipa_str)

    # Chia các âm tiết theo dấu chấm '.' nếu có
    if '.' in ipa_clean:
        syllables = ipa_clean.split('.')
    else:
        # Tách dựa trên ranh giới nguyên âm
        vowels_pattern = r'([aɪeəɒɔʊuʌiæɜː]+)'
        parts = re.split(vowels_pattern, ipa_clean)
        syllables = []
        curr = ""
        for p in parts:
            if not p:
                continue
            curr += p
            if re.search(vowels_pattern, p):
                syllables.append(curr)
                curr = ""
        if curr:
            if syllables:
                syllables[-1] += curr
            else:
                syllables.append(curr)

    vn_parts = []
    for syl in syllables:
        s = syl

        # 1. Chuyển đổi các nguyên âm phức tạp / nguyên âm đôi
        s = s.replace("eɪ", "ây")
        s = s.replace("aɪ", "ai")
        s = s.replace("aʊ", "ao")
        s = s.replace("ɔɪ", "oi")
        s = s.replace("əʊ", "âu").replace("oʊ", "âu")
        s = s.replace("ɪə", "ia").replace("iə", "ia")
        s = s.replace("eə", "e-ơ")
        s = s.replace("ʊə", "ua")
        s = s.replace("iː", "i")
        s = s.replace("uː", "u")
        s = s.replace("ɔː", "o")
        s = s.replace("ɜːr", "ơ").replace("ɜː", "ơ")
        s = s.replace("ɑː", "a")
        s = s.replace("æ", "e")
        s = s.replace("ɛ", "e")
        s = s.replace("ɒ", "o")
        s = s.replace("ɔ", "o")
        s = s.replace("ʌ", "ă")
        s = s.replace("ə", "ơ")
        s = s.replace("ɪ", "i")
        s = s.replace("ʊ", "u")

        # 2. Chuyển đổi các phụ âm đặc biệt
        s = s.replace("tʃ", "ch")
        s = s.replace("dʒ", "gi")
        s = s.replace("θ", "th")
        s = s.replace("ð", "đ")
        s = s.replace("ʃ", "s")
        s = s.replace("ʒ", "d")
        s = s.replace("ŋ", "ng")
        s = s.replace("ɡ", "g")
        s = s.replace("j", "d")
        s = s.replace("w", "u")
        s = s.replace("z", "z")

        # 3. Phụ âm đầu cụm
        s = re.sub(r'^str', 'x-tr', s)
        s = re.sub(r'^sk', 'x-c', s)
        s = re.sub(r'^st', 'x-t', s)
        s = re.sub(r'^sp', 'x-p', s)
        s = re.sub(r'^sm', 'x-m', s)
        s = re.sub(r'^sn', 'x-n', s)
        s = re.sub(r'^kl', 'clo', s)
        s = re.sub(r'^pl', 'plo', s)
        s = re.sub(r'^bl', 'blo', s)
        s = re.sub(r'^fl', 'phlo', s)
        s = re.sub(r'^gl', 'glo', s)

        # 4. Phụ âm đơn
        s = s.replace("f", "ph")
        s = s.replace("k", "c")
        s = s.replace("s", "x")

        # Chuẩn hóa âm cuối l -> ồ
        if s.endswith("l") and len(s) > 1 and not s.endswith("ồ"):
            s = s[:-1] + "ồ"

        vn_parts.append(s.strip())

    res = "-".join([p for p in vn_parts if p])
    res = re.sub(r'-+', '-', res).strip('-')
    return res if res else word.lower()

def get_vietnamese_phonetic(word: str, ipa_str: Optional[str] = None) -> str:
    """
    Lấy phiên âm tiếng Việt cho bất kỳ từ vựng nào.
    1. Tra cứu Override
    2. Chuyển đổi từ IPA có sẵn
    3. Tra cứu eng_to_ipa nếu chưa có IPA
    """
    clean_w = (word or "").strip().lower()
    if clean_w in VIETNAMESE_PHONETIC_OVERRIDES:
        return VIETNAMESE_PHONETIC_OVERRIDES[clean_w]

    # Kiểm tra theo từng từ nếu là cụm từ (ví dụ "leaf vein", "ear tuft")
    if " " in clean_w:
        sub_words = clean_w.split()
        sub_phonetics = [get_vietnamese_phonetic(sw) for sw in sub_words]
        return " ".join(sub_phonetics)

    target_ipa = ipa_str
    if not target_ipa and ipa_module:
        try:
            converted = ipa_module.convert(clean_w)
            if converted and not converted.endswith("*"):
                target_ipa = f"/{converted}/"
        except Exception:
            pass

    if target_ipa:
        return ipa_to_vietnamese_phonetic(target_ipa, clean_w)

    return clean_w
