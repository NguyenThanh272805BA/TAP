import os
import json
from typing import Dict, List, Any, Optional

try:
    import eng_to_ipa as ipa
except ImportError:
    ipa = None

from app.ml_models.vietnamese_phonetics import get_vietnamese_phonetic

# Đường dẫn tới các file dữ liệu
CURRENT_DIR = os.path.dirname(__file__)
OXFORD_PATH = os.path.join(CURRENT_DIR, 'oxford_5000.json')
OMNI_VOCAB_PATH = os.path.join(CURRENT_DIR, 'omni_vocab_1000.json')
TAXONOMY_FOREST_PATH = os.path.join(CURRENT_DIR, 'taxonomy_forest_5000.json')

_OXFORD_CACHE: Optional[Dict[str, str]] = None
_OMNI_VOCAB_CACHE: Optional[Dict[str, Dict[str, Any]]] = None
_OMNI_STATS_CACHE: Optional[Dict[str, Any]] = None
_TAXONOMY_FOREST_CACHE: Optional[Dict[str, Any]] = None

def get_taxonomy_forest() -> Dict[str, Any]:
    global _TAXONOMY_FOREST_CACHE
    if _TAXONOMY_FOREST_CACHE is None:
        if os.path.exists(TAXONOMY_FOREST_PATH):
            try:
                with open(TAXONOMY_FOREST_PATH, 'r', encoding='utf-8') as f:
                    _TAXONOMY_FOREST_CACHE = json.load(f)
            except Exception as ex:
                print(f"[!] Lỗi đọc taxonomy_forest_5000.json: {ex}")
                _TAXONOMY_FOREST_CACHE = {"macro_trees": {}, "expression_engine": {}, "flat_registry": {}}
        else:
            _TAXONOMY_FOREST_CACHE = {"macro_trees": {}, "expression_engine": {}, "flat_registry": {}}
    return _TAXONOMY_FOREST_CACHE

def get_oxford_dict() -> Dict[str, str]:
    global _OXFORD_CACHE
    if _OXFORD_CACHE is None:
        if os.path.exists(OXFORD_PATH):
            try:
                with open(OXFORD_PATH, 'r', encoding='utf-8') as f:
                    _OXFORD_CACHE = json.load(f)
            except Exception:
                _OXFORD_CACHE = {}
        else:
            _OXFORD_CACHE = {}
    return _OXFORD_CACHE

def get_omni_registry() -> Dict[str, Dict[str, Any]]:
    global _OMNI_VOCAB_CACHE, _OMNI_STATS_CACHE
    if _OMNI_VOCAB_CACHE is None:
        _OMNI_VOCAB_CACHE = {}
        if os.path.exists(OMNI_VOCAB_PATH):
            try:
                with open(OMNI_VOCAB_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entries = data.get("entries", [])
                    for e in entries:
                        w_key = e.get("word", "").strip().lower()
                        if w_key:
                            _OMNI_VOCAB_CACHE[w_key] = e
                    _OMNI_STATS_CACHE = {
                        "total": data.get("total", len(_OMNI_VOCAB_CACHE)),
                        "domain_stats": data.get("domain_stats", {}),
                        "cefr_stats": data.get("cefr_stats", {})
                    }
            except Exception as ex:
                print(f"[!] Lỗi đọc omni_vocab_1000.json: {ex}")
    return _OMNI_VOCAB_CACHE

def get_domain_stats() -> Dict[str, Any]:
    global _OMNI_STATS_CACHE
    get_omni_registry()
    if _OMNI_STATS_CACHE:
        return _OMNI_STATS_CACHE
    return {"total": 0, "domain_stats": {}, "cefr_stats": {}}

# =========================================================================
# 1. KHÔNG GIAN 4 MIỀN THỰC THỂ CỐT LÕI (OMNI-MODAL DOMAINS)
# =========================================================================
DOMAINS: Dict[str, Dict[str, str]] = {
    "all": {
        "name": "Toàn Cảnh",
        "description": "Nhận diện vạn vật xuyên suốt mọi miền thực thể",
        "icon": "globe"
    },
    "objects": {
        "name": "Đồ Vật & Công Cụ",
        "description": "Thiết bị, đồ gia dụng, nội thất, dụng cụ học tập & thời trang",
        "icon": "box"
    },
    "creatures": {
        "name": "Sinh Vật & Thực Thể Sống",
        "description": "Động vật, thực vật, hoa cỏ và dáng vẻ con người",
        "icon": "feather"
    },
    "scenes": {
        "name": "Khung Cảnh & Không Gian",
        "description": "Phòng học, quán cafe, đường phố, thư viện & danh lam thắng cảnh",
        "icon": "building"
    },
    "environment": {
        "name": "Môi Trường & Hiện Tượng",
        "description": "Bầu trời, thời tiết, ánh sáng, địa hình tự nhiên & khí quyển",
        "icon": "sun"
    }
}

# =========================================================================
# 2. TỪ ĐIỂN PHÂN CẤP ĐỒ VẬT -> BỘ PHẬN (OBJECT-TO-PARTS TAXONOMY)
# (Giữ tính tương thích ngược 100% với các phiên bản trước)
# =========================================================================
OBJECT_PARTS_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "backpack": {
        "vn_name": "Cặp sách / Ba lô",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "zipper": {"vn": "Khóa kéo", "cefr": "B1", "tier": "micro"},
            "shoulder strap": {"vn": "Quai đeo vai", "cefr": "B1", "tier": "functional"},
            "buckle": {"vn": "Khóa bấm / Khóa cài", "cefr": "B2", "tier": "micro"},
            "pocket": {"vn": "Ngăn túi", "cefr": "A2", "tier": "functional"},
            "handle": {"vn": "Quai xách / Tay cầm", "cefr": "B1", "tier": "functional"},
            "seam": {"vn": "Đường may ranh giới", "cefr": "B2", "tier": "micro"},
            "logo": {"vn": "Nhãn hiệu / Logo", "cefr": "B1", "tier": "micro"}
        }
    },
    "laptop": {
        "vn_name": "Máy tính xách tay",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "keyboard": {"vn": "Bàn phím", "cefr": "A2", "tier": "functional"},
            "screen": {"vn": "Màn hình hiển thị", "cefr": "A2", "tier": "functional"},
            "trackpad": {"vn": "Bàn di chuột cảm ứng", "cefr": "B1", "tier": "micro"},
            "webcam": {"vn": "Camera máy tính", "cefr": "B1", "tier": "functional"},
            "key": {"vn": "Phím bấm", "cefr": "A2", "tier": "micro"},
            "hinge": {"vn": "Bản lề gập máy", "cefr": "B2", "tier": "micro"},
            "logo": {"vn": "Biểu tượng thương hiệu", "cefr": "B1", "tier": "micro"}
        }
    },
    "shirt": {
        "vn_name": "Áo sơ mi / Áo",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "collar": {"vn": "Cổ áo", "cefr": "B1", "tier": "functional"},
            "sleeve": {"vn": "Tay áo", "cefr": "B1", "tier": "functional"},
            "button": {"vn": "Cúc áo / Khuy", "cefr": "A2", "tier": "micro"},
            "pocket": {"vn": "Túi áo", "cefr": "A2", "tier": "functional"},
            "cuff": {"vn": "Cổ tay áo", "cefr": "B2", "tier": "micro"}
        }
    },
    "bicycle": {
        "vn_name": "Xe đạp",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "handlebar": {"vn": "Ghi-đông / Tay lái", "cefr": "B2", "tier": "functional"},
            "wheel": {"vn": "Bánh xe", "cefr": "A2", "tier": "functional"},
            "pedal": {"vn": "Bàn đạp", "cefr": "B1", "tier": "functional"},
            "saddle": {"vn": "Yên xe", "cefr": "B2", "tier": "functional"},
            "chain": {"vn": "Xích xe đạp", "cefr": "B1", "tier": "micro"},
            "tire": {"vn": "Lốp xe", "cefr": "B1", "tier": "functional"},
            "brake": {"vn": "Phanh / Thắng xe", "cefr": "B1", "tier": "functional"}
        }
    },
    "bottle": {
        "vn_name": "Chai nước / Bình nước",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "cap": {"vn": "Nắp chai", "cefr": "A2", "tier": "functional"},
            "label": {"vn": "Nhãn dán thương hiệu", "cefr": "B1", "tier": "micro"},
            "bottle neck": {"vn": "Cổ chai", "cefr": "B1", "tier": "functional"},
            "bottle base": {"vn": "Đáy chai", "cefr": "A2", "tier": "functional"}
        }
    },
    "shoes": {
        "vn_name": "Đôi giày",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "shoelace": {"vn": "Dây buộc giày", "cefr": "B1", "tier": "micro"},
            "sole": {"vn": "Đế giày", "cefr": "B2", "tier": "functional"},
            "tongue": {"vn": "Lưỡi gà giày", "cefr": "B2", "tier": "micro"},
            "heel": {"vn": "Gót giày", "cefr": "B1", "tier": "functional"}
        }
    },
    "cup": {
        "vn_name": "Cốc / Ly tách",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "handle": {"vn": "Quai cầm", "cefr": "B1", "tier": "functional"},
            "rim": {"vn": "Vành miệng cốc", "cefr": "B2", "tier": "micro"},
            "cup base": {"vn": "Đáy cốc", "cefr": "A2", "tier": "functional"}
        }
    },
    "book": {
        "vn_name": "Quyển sách",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "cover": {"vn": "Bìa sách", "cefr": "A2", "tier": "functional"},
            "page": {"vn": "Trang giấy", "cefr": "A1", "tier": "functional"},
            "spine": {"vn": "Gáy sách", "cefr": "B2", "tier": "micro"},
            "bookmark": {"vn": "Thẻ đánh dấu trang", "cefr": "B1", "tier": "micro"}
        }
    },
    "glasses": {
        "vn_name": "Kính mắt",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "frame": {"vn": "Gọng kính", "cefr": "B1", "tier": "functional"},
            "lens": {"vn": "Tròng kính", "cefr": "B1", "tier": "functional"},
            "temple": {"vn": "Càng kính / Gọng đeo tai", "cefr": "B2", "tier": "micro"},
            "nose pad": {"vn": "Đệm mũi kính", "cefr": "B2", "tier": "micro"}
        }
    },
    "watch": {
        "vn_name": "Đồng hồ đeo tay",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "strap": {"vn": "Dây đeo đồng hồ", "cefr": "B1", "tier": "functional"},
            "dial": {"vn": "Mặt số đồng hồ", "cefr": "B2", "tier": "micro"},
            "watch hand": {"vn": "Kim đồng hồ", "cefr": "A2", "tier": "micro"},
            "crown": {"vn": "Nút xoay chỉnh giờ", "cefr": "B2", "tier": "micro"}
        }
    },
    "chair": {
        "vn_name": "Chiếc ghế",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "seat": {"vn": "Mặt ghế ngồi", "cefr": "A2", "tier": "functional"},
            "backrest": {"vn": "Lưng tựa ghế", "cefr": "B1", "tier": "functional"},
            "armrest": {"vn": "Tay vịn ghế", "cefr": "B2", "tier": "micro"},
            "chair leg": {"vn": "Chân ghế", "cefr": "A2", "tier": "functional"}
        }
    },
    "phone": {
        "vn_name": "Điện thoại di động",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "screen": {"vn": "Màn hình điện thoại", "cefr": "A2", "tier": "functional"},
            "camera lens": {"vn": "Ống kính máy ảnh", "cefr": "B1", "tier": "functional"},
            "flash": {"vn": "Đèn flash", "cefr": "B1", "tier": "micro"},
            "speaker": {"vn": "Loa ngoài", "cefr": "A2", "tier": "micro"}
        }
    },
    "pen": {
        "vn_name": "Bút viết",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "cap": {"vn": "Nắp bút", "cefr": "A2", "tier": "functional"},
            "clip": {"vn": "Kẹp cài bút", "cefr": "B1", "tier": "micro"},
            "nib": {"vn": "Ngòi bút", "cefr": "B2", "tier": "micro"},
            "barrel": {"vn": "Thân bút", "cefr": "B1", "tier": "functional"}
        }
    },
    "desk": {
        "vn_name": "Bàn làm việc",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "tabletop": {"vn": "Mặt bàn", "cefr": "A2", "tier": "functional"},
            "drawer": {"vn": "Ngăn kéo bàn", "cefr": "A2", "tier": "functional"},
            "desk leg": {"vn": "Chân bàn", "cefr": "A2", "tier": "functional"}
        }
    },
    "monitor": {
        "vn_name": "Màn hình vi tính",
        "cefr": "A2",
        "domain": "objects",
        "parts": {
            "screen": {"vn": "Mặt hiển thị", "cefr": "A2", "tier": "functional"},
            "stand": {"vn": "Chân đế màn hình", "cefr": "B1", "tier": "functional"},
            "bezel": {"vn": "Viền màn hình", "cefr": "B2", "tier": "micro"}
        }
    },
    "plant": {
        "vn_name": "Chậu cây cảnh",
        "cefr": "A1",
        "domain": "creatures",
        "parts": {
            "leaf": {"vn": "Lá cây", "cefr": "A1", "tier": "functional"},
            "stem": {"vn": "Cành thân cây", "cefr": "B1", "tier": "functional"},
            "pot": {"vn": "Chậu trồng", "cefr": "A2", "tier": "functional"}
        }
    },
    "burger": {
        "vn_name": "Bánh kẹp Burger",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "bun": {"vn": "Bánh mì kẹp", "cefr": "A2", "tier": "functional"},
            "patty": {"vn": "Miếng thịt kẹp", "cefr": "B1", "tier": "functional"},
            "lettuce": {"vn": "Rau xà lách", "cefr": "A2", "tier": "functional"},
            "tomato": {"vn": "Cà chua", "cefr": "A1", "tier": "functional"},
            "cheese": {"vn": "Phô mai", "cefr": "A1", "tier": "functional"},
            "sauce": {"vn": "Nước sốt", "cefr": "A2", "tier": "functional"},
            "sesame": {"vn": "Hạt vừng / mè", "cefr": "B2", "tier": "micro"},
            "onion": {"vn": "Hành tây", "cefr": "A2", "tier": "functional"}
        }
    },
    "dish": {
        "vn_name": "Món ăn / Đĩa thức ăn",
        "cefr": "A1",
        "domain": "objects",
        "parts": {
            "plate": {"vn": "Đĩa đựng", "cefr": "A1", "tier": "functional"},
            "food": {"vn": "Thức ăn", "cefr": "A1", "tier": "functional"},
            "fork": {"vn": "Dĩa ăn", "cefr": "A1", "tier": "functional"},
            "spoon": {"vn": "Thìa / muỗng", "cefr": "A1", "tier": "functional"},
            "tablecloth": {"vn": "Khăn trải bàn", "cefr": "B1", "tier": "functional"},
            "napkin": {"vn": "Khăn ăn", "cefr": "A2", "tier": "functional"}
        }
    },
    "wine glass": {
        "vn_name": "Ly rượu vang",
        "cefr": "A2",
        "domain": "objects",
        "parts": {
            "wine": {"vn": "Rượu vang", "cefr": "A2", "tier": "functional"},
            "glass rim": {"vn": "Vành ly", "cefr": "B2", "tier": "micro"},
            "stem": {"vn": "Chân cuống ly", "cefr": "B1", "tier": "functional"},
            "glass base": {"vn": "Đế ly", "cefr": "A2", "tier": "functional"}
        }
    },
    "grapes": {
        "vn_name": "Chùm nho",
        "cefr": "A2",
        "domain": "creatures",
        "parts": {
            "grape": {"vn": "Quả nho", "cefr": "A2", "tier": "functional"},
            "cluster": {"vn": "Chùm quả", "cefr": "B1", "tier": "macro"},
            "stem": {"vn": "Cuống nho", "cefr": "B1", "tier": "micro"},
            "vine": {"vn": "Cành nhánh nho", "cefr": "B1", "tier": "functional"},
            "grape skin": {"vn": "Vỏ quả nho", "cefr": "B2", "tier": "micro"},
            "leaf": {"vn": "Lá nho", "cefr": "A1", "tier": "functional"}
        }
    },
    "fruit": {
        "vn_name": "Trái cây / Hoa quả",
        "cefr": "A1",
        "domain": "creatures",
        "parts": {
            "grapes": {"vn": "Chùm nho", "cefr": "A2", "tier": "macro"},
            "skin": {"vn": "Vỏ quả", "cefr": "A2", "tier": "functional"},
            "stem": {"vn": "Cuống quả", "cefr": "B1", "tier": "functional"},
            "seed": {"vn": "Hạt quả", "cefr": "A2", "tier": "micro"},
            "pulp": {"vn": "Thịt quả / Ruột", "cefr": "B2", "tier": "micro"}
        }
    }
}

def lookup_forest_word(word_query: str) -> Optional[Dict[str, Any]]:
    """Tra cứu một từ vựng trong Rừng phân cấp 5.830 từ vựng với tốc độ O(1)"""
    clean = (word_query or "").strip().lower()
    forest = get_taxonomy_forest()
    flat = forest.get("flat_registry", {})
    if clean in flat:
        entry = flat[clean]
        cefr_val = (entry.get("cefr") or "B1").upper()
        ipa_val = entry.get("ipa", "")
        vn_phonetic = entry.get("vn_phonetic") or get_vietnamese_phonetic(clean, ipa_val)
        return {
            "word": clean,
            "display_name": clean.capitalize(),
            "meaning": entry.get("meaning", "Chi tiết nhận diện"),
            "cefr": cefr_val,
            "ipa": ipa_val,
            "vn_phonetic": vn_phonetic,
            "tier": entry.get("tier", "micro"),
            "domain": entry.get("domain", "objects"),
            "parent": entry.get("parent"),
            "category": entry.get("category", ""),
            "level_tier": "basic" if cefr_val in ["A1", "A2"] else "advanced"
        }
    return None

def get_facial_expressions() -> Dict[str, Any]:
    """Lấy danh sách 8 trạng thái biểu cảm khuôn mặt cốt lõi và các tính từ CEFR B2-C1"""
    forest = get_taxonomy_forest()
    return forest.get("expression_engine", {})

def get_micro_queries(
    parent_category: Optional[str] = None,
    mode: str = "all",
    max_queries: int = 12
) -> List[str]:
    """
    Trích xuất và cắt tỉa động danh sách truy vấn vi mô theo thực thể cha (Parent-Conditioned Dynamic Pruning).
    Đảm bảo M_sub <= 12 queries để độ trễ suy luận trên CPU luôn <= 30ms.
    - parent_category: 'cat', 'dog', 'human', 'laptop', 'backpack', v.v.
    - mode: 'micro_anatomy' (bộ phận giải phẫu/linh kiện), 'expressions' (biểu cảm/hành vi), 'all' (kết hợp).
    """
    forest = get_taxonomy_forest()
    macro_trees = forest.get("macro_trees", {})
    max_queries = max(3, min(16, max_queries))

    # Chuẩn hóa tên thực thể cha
    p_key = (parent_category or "").strip().lower()
    if p_key in ["person", "student", "teacher", "man", "woman", "boy", "girl"]:
        p_key = "human"

    if p_key and p_key in macro_trees:
        tree = macro_trees[p_key]
        anatomy = [item["word"] for item in tree.get("micro_anatomy", [])]
        expressions = [item["word"] for item in tree.get("expressions_behaviors", [])]
        textures = [item["word"] for item in tree.get("textures_materials", [])]

        if mode == "micro_anatomy":
            return anatomy[:max_queries]
        elif mode == "expressions":
            return expressions[:max_queries]
        else: # "all"
            # Cân đối: 7 bộ phận giải phẫu + 3 biểu cảm/hành vi + 2 chất liệu
            selected = anatomy[:7] + expressions[:3] + textures[:2]
            return selected[:max_queries]

    # Nếu cha có trong OBJECT_PARTS_TAXONOMY
    if p_key and p_key in OBJECT_PARTS_TAXONOMY:
        parts_dict = OBJECT_PARTS_TAXONOMY[p_key].get("parts", {})
        micro_parts = [p for p, info in parts_dict.items() if info.get("tier") == "micro"]
        func_parts = [p for p, info in parts_dict.items() if info.get("tier") != "micro"]
        candidate = micro_parts + func_parts
        return candidate[:max_queries]

    # Nếu không xác định được cha cụ thể (General Micro Spotlight)
    # Lấy các chi tiết vi mô phổ quát thường gặp trong đời sống & học tập
    fallback_micro = [
        "eye", "whisker", "paw", "smile", "frown", "keycap", "screen",
        "zipper", "petal", "leaf vein", "button", "lens"
    ]
    return fallback_micro[:max_queries]

# =========================================================================
# 3. TRUY XUẤT THÔNG TIN HỌC THUẬT OMNI-MODAL METADATA (O(1))
# =========================================================================
def get_part_info(part_word: str, parent_obj: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Truy xuất đầy đủ metadata học thuật: Phiên âm IPA, Nghĩa tiếng Việt, Cấp độ CEFR,
    Miền thực thể (domain) và Level Tier từ Rừng phân cấp 5.830 từ vựng.
    """
    clean_word = (part_word or "").strip().lower()

    # 1. Tìm trong Rừng phân cấp 5.830 từ vựng (Dynamic Taxonomy Forest)
    forest_entry = lookup_forest_word(clean_word)
    if forest_entry:
        if domain:
            forest_entry["domain"] = domain
        return forest_entry

    # 2. Tìm trực tiếp trong Registry 1.000+ từ vựng Omni
    registry = get_omni_registry()
    oxford = get_oxford_dict()

    if clean_word in registry:
        entry = registry[clean_word]
        cefr = entry.get("cefr") or oxford.get(clean_word, "B1")
        cefr_upper = cefr.upper()
        ipa_val = entry.get("ipa", "")
        vn_phonetic = entry.get("vn_phonetic") or get_vietnamese_phonetic(clean_word, ipa_val)
        return {
            "word": clean_word,
            "display_name": entry.get("display_name", clean_word.capitalize()),
            "ipa": ipa_val,
            "vn_phonetic": vn_phonetic,
            "meaning": entry.get("meaning", "Chi tiết nhận diện"),
            "cefr": cefr_upper,
            "tier": entry.get("tier", "functional"),
            "domain": entry.get("domain", domain or "objects"),
            "level_tier": "basic" if cefr_upper in ["A1", "A2"] else "advanced"
        }

    # 3. Tìm trong OBJECT_PARTS_TAXONOMY (Nếu có cha hoặc là đồ vật chính)
    vn_meaning = "Chi tiết nhận diện"
    cefr = oxford.get(clean_word, "B1")
    tier = "functional"
    ent_domain = domain or "objects"

    if parent_obj and parent_obj in OBJECT_PARTS_TAXONOMY:
        parts_dict = OBJECT_PARTS_TAXONOMY[parent_obj].get("parts", {})
        if clean_word in parts_dict:
            vn_meaning = parts_dict[clean_word].get("vn", vn_meaning)
            cefr = parts_dict[clean_word].get("cefr", cefr)
            tier = parts_dict[clean_word].get("tier", "functional")
            ent_domain = OBJECT_PARTS_TAXONOMY[parent_obj].get("domain", "objects")
    else:
        for obj, obj_data in OBJECT_PARTS_TAXONOMY.items():
            if clean_word == obj:
                vn_meaning = obj_data.get("vn_name", vn_meaning)
                cefr = obj_data.get("cefr", cefr)
                tier = "macro"
                ent_domain = obj_data.get("domain", "objects")
                break
            if clean_word in obj_data.get("parts", {}):
                vn_meaning = obj_data["parts"][clean_word].get("vn", vn_meaning)
                cefr = obj_data["parts"][clean_word].get("cefr", cefr)
                tier = obj_data["parts"][clean_word].get("tier", "functional")
                ent_domain = obj_data.get("domain", "objects")
                break

    # 4. Sinh phiên âm IPA & phiên âm tiếng Việt nếu chưa có
    phonetic_ipa = ""
    if ipa is not None:
        try:
            phonetic_ipa = f"/{ipa.convert(clean_word)}/"
        except Exception:
            phonetic_ipa = ""

    vn_phonetic = get_vietnamese_phonetic(clean_word, phonetic_ipa)
    cefr_upper = cefr.upper()
    level_tier = "basic" if cefr_upper in ["A1", "A2"] else "advanced"

    return {
        "word": clean_word,
        "display_name": clean_word.capitalize(),
        "ipa": phonetic_ipa,
        "vn_phonetic": vn_phonetic,
        "meaning": vn_meaning,
        "cefr": cefr_upper,
        "tier": tier,
        "domain": ent_domain,
        "level_tier": level_tier
    }

get_omni_word_info = get_part_info


# =========================================================================
# 4. SINH DANH SÁCH TEXT QUERIES ĐA MIỀN CHO VISION-LANGUAGE DETECTOR
# =========================================================================
def build_candidate_queries(
    category: Optional[str] = None,
    granularity: str = "all",
    domain: str = "all"
) -> List[str]:
    """
    Sinh danh sách text queries đưa vào OWL-ViT Text Encoder dựa theo:
    - category: Lọc theo danh mục cụ thể hoặc quét tự động.
    - granularity: 'macro' (Cơ bản), 'functional' (Trung cấp), 'micro' (Chuyên sâu), 'all' (Toàn diện).
    - domain: 'all' (Toàn cảnh), 'objects' (Đồ vật), 'creatures' (Sinh vật),
              'scenes' (Khung cảnh), 'environment' (Môi trường).
    """
    granularity = (granularity or "all").lower()
    domain = (domain or "all").lower()
    registry = get_omni_registry()

    # 1. Nếu người dùng chọn một danh mục cụ thể trong OBJECT_PARTS_TAXONOMY
    if category and category in OBJECT_PARTS_TAXONOMY:
        cat_data = OBJECT_PARTS_TAXONOMY[category]
        parts = cat_data.get("parts", {})

        if granularity == "macro":
            return [category]
        elif granularity == "functional":
            func_parts = [p for p, info in parts.items() if info.get("tier") == "functional" or info.get("cefr") in ["A1", "A2"]]
            return [category] + (func_parts if func_parts else list(parts.keys())[:3])
        elif granularity == "micro":
            micro_parts = [p for p, info in parts.items() if info.get("tier") == "micro" or info.get("cefr") in ["B1", "B2", "C1"]]
            return micro_parts if micro_parts else list(parts.keys())
        else: # "all"
            return [category] + list(parts.keys())

    # 2. Gom nhóm các từ vựng theo miền từ Registry
    domain_items = {"objects": [], "scenes": [], "creatures": [], "environment": []}
    for word, item in registry.items():
        d = item.get("domain", "objects")
        t = item.get("tier", "functional")
        if d in domain_items:
            # Lọc theo granularity nếu được chỉ định
            if granularity == "macro" and t != "macro":
                continue
            elif granularity == "micro" and t != "micro":
                continue
            elif granularity == "functional" and t not in ["functional", "macro"]:
                continue
            domain_items[d].append(word)

    # 3. Chế độ lọc theo từng miền cụ thể
    if domain in domain_items and len(domain_items[domain]) > 0:
        target_words = domain_items[domain]
        # Giới hạn tối đa 32 queries để giữ độ trễ inference <100ms
        return target_words[:32]

    # 4. Chế độ TOÀN CẢNH (Universal Open-World: domain="all"):
    # Chọn lọc cân bằng giữa các miền thực thể cốt lõi đời sống & học tập
    # Đặc biệt bổ sung đồ ăn, ẩm thực, bàn tiệc, công nghệ, vật nuôi
    selected_queries: List[str] = [
        # Trái cây & Nông sản tươi (Fresh Fruits & Produce)
        "grapes", "grape", "fruit", "apple", "banana",
        # Ẩm thực & Bàn ăn (Culinary & Dining)
        "burger", "dish", "plate", "wine glass", "wine", "food", "bread",
        # Công nghệ & Dụng cụ học tập (Tech & Study)
        "laptop", "phone", "backpack", "book", "cup", "bottle",
        # Sinh vật & Thú cưng (Living Creatures)
        "cat", "dog", "person", "plant", "bird",
        # Đồ dùng gia đình & Bàn ghế (Furniture & Objects)
        "chair", "tablecloth", "desk",
        # Khung cảnh không gian (Scenes)
        "dining room", "cafe", "classroom", "office", "living room", "street", "park",
        # Môi trường & Ánh sáng (Environment)
        "sunlight", "window", "lamp", "shadow"
    ]

    return selected_queries[:36]


# =========================================================================
# 5. CỤM TỪ VỰNG NGỮ NGHĨA LIÊN TƯỞNG TOÀN CẢNH (SEMANTIC VOCABULARY CLUSTERS)
# Tự động mở rộng từ 1 thực thể chính thành 15-22 từ vựng sinh động, đa cấp độ CEFR
# =========================================================================
SEMANTIC_CLUSTERS: Dict[str, Dict[str, Any]] = {
    "fruits_nature": {
        "keywords": ["grapes", "grape", "fruit", "cluster", "vine", "berry", "apple", "banana", "orange", "fresh fruit"],
        "display_topic": "Hoa quả tươi & Trái cây",
        "words": [
            {"word": "grapes", "ipa": "/ɡreɪps/", "vn": "Chùm nho tươi", "cefr": "A2", "tier": "macro", "domain": "creatures"},
            {"word": "grape", "ipa": "/ɡreɪp/", "vn": "Quả nho", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "fruit", "ipa": "/fruːt/", "vn": "Trái cây tươi", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "cluster", "ipa": "/ˈklʌstər/", "vn": "Chùm quả", "cefr": "B1", "tier": "macro", "domain": "creatures"},
            {"word": "vine", "ipa": "/vaɪn/", "vn": "Cành nhánh nho", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "stem", "ipa": "/stem/", "vn": "Cuống quả nho", "cefr": "B1", "tier": "micro", "domain": "creatures"},
            {"word": "leaf", "ipa": "/liːf/", "vn": "Lá cây tươi", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "sweet", "ipa": "/swiːt/", "vn": "Ngọt ngào thanh mát", "cefr": "A1", "tier": "functional", "domain": "scenes"},
            {"word": "juicy", "ipa": "/ˈdʒuːsi/", "vn": "Mọng nước thơm ngon", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "fresh", "ipa": "/freʃ/", "vn": "Tươi sạch tự nhiên", "cefr": "A2", "tier": "functional", "domain": "environment"},
            {"word": "ripe", "ipa": "/raɪp/", "vn": "Chín mọng", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "harvest", "ipa": "/ˈhɑːrvɪst/", "vn": "Mùa thu hoạch quả", "cefr": "B1", "tier": "functional", "domain": "scenes"},
            {"word": "berry", "ipa": "/ˈberi/", "vn": "Quả mọng", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "organic", "ipa": "/ɔːrˈɡænɪk/", "vn": "Hữu cơ an lành", "cefr": "B2", "tier": "functional", "domain": "environment"},
            {"word": "nutritious", "ipa": "/nuːˈtrɪʃəs/", "vn": "Giàu dinh dưỡng", "cefr": "B2", "tier": "functional", "domain": "scenes"}
        ]
    },
    "food_dining": {
        "keywords": ["burger", "hamburger", "sandwich", "food", "dish", "plate", "wine", "glass", "meal", "pizza", "bread", "dining"],
        "display_topic": "Ẩm thực & Bàn ăn",
        "words": [
            {"word": "burger", "ipa": "/ˈbɜːrɡər/", "vn": "Bánh kẹp burger", "cefr": "A1", "tier": "macro", "domain": "objects"},
            {"word": "bun", "ipa": "/bʌn/", "vn": "Bánh mì tròn", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "patty", "ipa": "/ˈpæti/", "vn": "Miếng thịt kẹp", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "lettuce", "ipa": "/ˈletɪs/", "vn": "Rau xà lách", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "tomato", "ipa": "/təˈmeɪtoʊ/", "vn": "Cà chua", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "cheese", "ipa": "/tʃiːz/", "vn": "Phô mai", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "beef", "ipa": "/biːf/", "vn": "Thịt bò", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "sauce", "ipa": "/sɔːs/", "vn": "Nước sốt", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "plate", "ipa": "/pleɪt/", "vn": "Đĩa đựng thức ăn", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "wine", "ipa": "/waɪn/", "vn": "Rượu vang", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "glass", "ipa": "/ɡlæs/", "vn": "Ly thủy tinh", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "tablecloth", "ipa": "/ˈteɪblklɔːθ/", "vn": "Khăn trải bàn", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "napkin", "ipa": "/ˈnæpkɪn/", "vn": "Khăn ăn", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "fork", "ipa": "/fɔːrk/", "vn": "Dĩa ăn", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "delicious", "ipa": "/dɪˈlɪʃəs/", "vn": "Ngon miệng", "cefr": "A1", "tier": "functional", "domain": "scenes"},
            {"word": "crispy", "ipa": "/ˈkrɪspi/", "vn": "Giòn rụm", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "juicy", "ipa": "/ˈdʒuːsi/", "vn": "Mọng nước / thơm ngọt", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "savory", "ipa": "/ˈseɪvəri/", "vn": "Đậm đà hương vị", "cefr": "B2", "tier": "functional", "domain": "objects"},
            {"word": "fresh", "ipa": "/freʃ/", "vn": "Tươi ngon", "cefr": "A2", "tier": "functional", "domain": "environment"},
            {"word": "taste", "ipa": "/teɪst/", "vn": "Nếm thử / Thưởng thức", "cefr": "A2", "tier": "functional", "domain": "scenes"},
            {"word": "serve", "ipa": "/sɜːrv/", "vn": "Phục vụ món", "cefr": "B1", "tier": "functional", "domain": "scenes"}
        ]
    },
    "creature_cat": {
        "keywords": ["cat", "kitten", "feline"],
        "display_topic": "Mèo cưng & Động vật",
        "words": [
            {"word": "cat", "ipa": "/kæt/", "vn": "Con mèo", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "kitten", "ipa": "/ˈkɪtn/", "vn": "Mèo con", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "paw", "ipa": "/pɔː/", "vn": "Bàn chân vuốt", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "fur", "ipa": "/fɜːr/", "vn": "Lông thú", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "tail", "ipa": "/teɪl/", "vn": "Cái đuôi", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "whisker", "ipa": "/ˈwɪskər/", "vn": "Râu mèo", "cefr": "B1", "tier": "micro", "domain": "creatures"},
            {"word": "claw", "ipa": "/klɔː/", "vn": "Móng vuốt", "cefr": "B2", "tier": "micro", "domain": "creatures"},
            {"word": "ear", "ipa": "/ɪər/", "vn": "Đôi tai", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "eye", "ipa": "/aɪ/", "vn": "Mắt tròn", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "purr", "ipa": "/pɜːr/", "vn": "Tiếng kêu gừ gừ âu yếm", "cefr": "B2", "tier": "functional", "domain": "creatures"},
            {"word": "meow", "ipa": "/miˈaʊ/", "vn": "Tiếng kêu meo meo", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "fluffy", "ipa": "/ˈflʌfi/", "vn": "Mềm mại bông xù", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "playful", "ipa": "/ˈpleɪfəl/", "vn": "Hiếu động tinh nghịch", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "cute", "ipa": "/kjuːt/", "vn": "Dễ thương đáng yêu", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "cuddle", "ipa": "/ˈkʌdl/", "vn": "Ôm ấp cưng nựng", "cefr": "B2", "tier": "functional", "domain": "creatures"},
            {"word": "sleepy", "ipa": "/ˈsliːpi/", "vn": "Buồn ngủ / Say giấc", "cefr": "A2", "tier": "functional", "domain": "creatures"}
        ]
    },
    "creature_dog": {
        "keywords": ["dog", "puppy", "canine"],
        "display_topic": "Chó cưng & Vật nuôi",
        "words": [
            {"word": "dog", "ipa": "/dɔːɡ/", "vn": "Con chó", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "puppy", "ipa": "/ˈpʌpi/", "vn": "Chó con", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "tail", "ipa": "/teɪl/", "vn": "Cái đuôi", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "bark", "ipa": "/bɑːrk/", "vn": "Tiếng sủa", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "snout", "ipa": "/snaʊt/", "vn": "Mõm chó", "cefr": "B2", "tier": "micro", "domain": "creatures"},
            {"word": "paw", "ipa": "/pɔː/", "vn": "Bàn chân", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "collar", "ipa": "/ˈkɑːlər/", "vn": "Vòng cổ", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "leash", "ipa": "/liːʃ/", "vn": "Dây dắt chó", "cefr": "B2", "tier": "functional", "domain": "objects"},
            {"word": "bone", "ipa": "/boʊn/", "vn": "Khúc xương gặm", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "friendly", "ipa": "/ˈfrendli/", "vn": "Thân thiện hiền hòa", "cefr": "A2", "tier": "functional", "domain": "creatures"},
            {"word": "loyal", "ipa": "/ˈlɔɪəl/", "vn": "Trung thành", "cefr": "B2", "tier": "functional", "domain": "creatures"},
            {"word": "energetic", "ipa": "/ˌenərˈdʒetɪk/", "vn": "Năng động hoạt bát", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "fetch", "ipa": "/fetʃ/", "vn": "Bắt bóng / Nhặt đồ", "cefr": "B1", "tier": "functional", "domain": "creatures"}
        ]
    },
    "tech_workspace": {
        "keywords": ["laptop", "computer", "desk", "keyboard", "monitor", "workspace", "office", "study"],
        "display_topic": "Công nghệ & Bàn làm việc",
        "words": [
            {"word": "laptop", "ipa": "/ˈlæptɑːp/", "vn": "Máy tính xách tay", "cefr": "A1", "tier": "macro", "domain": "objects"},
            {"word": "keyboard", "ipa": "/ˈkiːbɔːrd/", "vn": "Bàn phím", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "screen", "ipa": "/skriːn/", "vn": "Màn hình", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "trackpad", "ipa": "/ˈtrækpæd/", "vn": "Bàn di chuột cảm ứng", "cefr": "B1", "tier": "micro", "domain": "objects"},
            {"word": "mouse", "ipa": "/maʊs/", "vn": "Chuột máy tính", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "desk", "ipa": "/desk/", "vn": "Bàn làm việc", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "chair", "ipa": "/tʃer/", "vn": "Chiếc ghế", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "cable", "ipa": "/ˈkeɪbl/", "vn": "Dây cáp sạc", "cefr": "B1", "tier": "functional", "domain": "objects"},
            {"word": "headphones", "ipa": "/ˈhedfoʊnz/", "vn": "Tai nghe", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "type", "ipa": "/taɪp/", "vn": "Gõ phím", "cefr": "A1", "tier": "functional", "domain": "scenes"},
            {"word": "click", "ipa": "/klɪk/", "vn": "Bấm chuột", "cefr": "A2", "tier": "functional", "domain": "scenes"},
            {"word": "modern", "ipa": "/ˈmɑːdərn/", "vn": "Hiện đại tiên tiến", "cefr": "A2", "tier": "functional", "domain": "scenes"},
            {"word": "efficient", "ipa": "/ɪˈfɪʃnt/", "vn": "Hiệu quả tối ưu", "cefr": "B2", "tier": "functional", "domain": "scenes"},
            {"word": "focus", "ipa": "/ˈfoʊkəs/", "vn": "Tập trung cao độ", "cefr": "B1", "tier": "functional", "domain": "scenes"}
        ]
    },
    "cafe_beverage": {
        "keywords": ["coffee", "cup", "mug", "tea", "cafe", "beverage", "drink"],
        "display_topic": "Cà phê & Đồ uống",
        "words": [
            {"word": "coffee", "ipa": "/ˈkɔːfi/", "vn": "Cà phê thơm", "cefr": "A1", "tier": "macro", "domain": "objects"},
            {"word": "cup", "ipa": "/kʌp/", "vn": "Cốc tách", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "mug", "ipa": "/mʌɡ/", "vn": "Cốc uống lớn", "cefr": "A2", "tier": "functional", "domain": "objects"},
            {"word": "foam", "ipa": "/foʊm/", "vn": "Lớp bọt sữa", "cefr": "B1", "tier": "micro", "domain": "objects"},
            {"word": "steam", "ipa": "/stiːm/", "vn": "Hơi nước nóng", "cefr": "B1", "tier": "environment", "domain": "environment"},
            {"word": "table", "ipa": "/ˈteɪbl/", "vn": "Bàn cà phê", "cefr": "A1", "tier": "functional", "domain": "objects"},
            {"word": "cafe", "ipa": "/kæˈfeɪ/", "vn": "Quán cà phê", "cefr": "A1", "tier": "macro", "domain": "scenes"},
            {"word": "sip", "ipa": "/sɪp/", "vn": "Nhấp từng ngụm", "cefr": "B1", "tier": "functional", "domain": "scenes"},
            {"word": "brew", "ipa": "/bruː/", "vn": "Pha chế cà phê", "cefr": "B2", "tier": "functional", "domain": "scenes"},
            {"word": "aromatic", "ipa": "/ˌærəˈmætɪk/", "vn": "Thơm ngát quyến rũ", "cefr": "B2", "tier": "functional", "domain": "scenes"},
            {"word": "cozy", "ipa": "/ˈkoʊzi/", "vn": "Ấm cúng dễ chịu", "cefr": "B1", "tier": "functional", "domain": "scenes"},
            {"word": "warm", "ipa": "/wɔːrm/", "vn": "Ấm áp", "cefr": "A1", "tier": "functional", "domain": "environment"}
        ]
    },
    "nature_green": {
        "keywords": ["tree", "plant", "flower", "leaf", "garden", "park", "nature", "forest"],
        "display_topic": "Thiên nhiên & Cây xanh",
        "words": [
            {"word": "tree", "ipa": "/triː/", "vn": "Cây xanh", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "leaf", "ipa": "/liːf/", "vn": "Chiếc lá", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "flower", "ipa": "/ˈflaʊər/", "vn": "Bông hoa", "cefr": "A1", "tier": "macro", "domain": "creatures"},
            {"word": "petal", "ipa": "/ˈpetl/", "vn": "Cánh hoa", "cefr": "B1", "tier": "micro", "domain": "creatures"},
            {"word": "branch", "ipa": "/bræntʃ/", "vn": "Cành cây", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "stem", "ipa": "/stem/", "vn": "Thân cuống cây", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "grass", "ipa": "/ɡræs/", "vn": "Thảm cỏ", "cefr": "A1", "tier": "functional", "domain": "creatures"},
            {"word": "sunlight", "ipa": "/ˈsʌnlaɪt/", "vn": "Ánh nắng mặt trời", "cefr": "A2", "tier": "functional", "domain": "environment"},
            {"word": "shadow", "ipa": "/ˈʃædoʊ/", "vn": "Bóng râm", "cefr": "A2", "tier": "functional", "domain": "environment"},
            {"word": "fresh", "ipa": "/freʃ/", "vn": "Tươi mát trong lành", "cefr": "A2", "tier": "functional", "domain": "environment"},
            {"word": "green", "ipa": "/ɡriːn/", "vn": "Xanh tươi", "cefr": "A1", "tier": "functional", "domain": "scenes"},
            {"word": "bloom", "ipa": "/bluːm/", "vn": "Khoe sắc nở hoa", "cefr": "B1", "tier": "functional", "domain": "creatures"},
            {"word": "peaceful", "ipa": "/ˈpiːsfəl/", "vn": "Thanh bình yên ả", "cefr": "B1", "tier": "functional", "domain": "scenes"}
        ]
    }
}

def get_associated_vocabulary(primary_word: str, detected_parts: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Sinh danh sách từ vựng liên tưởng phong phú (15 - 22 từ vựng hoàn chỉnh kèm IPA,
    phiên âm tiếng Việt, nghĩa tiếng Việt, cấp độ CEFR) theo chủ đề bức ảnh vừa quét.
    """
    p_norm = (primary_word or "").strip().lower()
    all_context_words = [p_norm]
    if detected_parts:
        for p in detected_parts:
            w = (p.get("word") or "").lower()
            if w:
                all_context_words.append(w)

    # 1. Tìm cluster phù hợp nhất
    best_cluster = None
    max_score = 0
    for c_id, c_data in SEMANTIC_CLUSTERS.items():
        kw_set = set(k.lower() for k in c_data["keywords"])
        match_count = sum(1 for w in all_context_words if w in kw_set or any(kw in w for kw in kw_set))
        if match_count > max_score:
            max_score = match_count
            best_cluster = c_data

    # Mặc định rơi vào food_dining nếu có từ liên quan đến món ăn/bàn ăn, hoặc tech nếu có laptop
    if not best_cluster:
        if any(w in ["food", "dish", "plate", "wine", "meat", "bread", "burger"] for w in all_context_words):
            best_cluster = SEMANTIC_CLUSTERS["food_dining"]
        elif any(w in ["cat", "kitten", "pet"] for w in all_context_words):
            best_cluster = SEMANTIC_CLUSTERS["creature_cat"]
        elif any(w in ["dog", "puppy"] for w in all_context_words):
            best_cluster = SEMANTIC_CLUSTERS["creature_dog"]
        else:
            best_cluster = SEMANTIC_CLUSTERS.get("food_dining")

    if not best_cluster:
        return []

    # 2. Xây dựng danh sách từ vựng hoàn chỉnh
    results: List[Dict[str, Any]] = []
    seen = set()

    # Ưu tiên các từ thực tế đã phát hiện được
    if detected_parts:
        for part in detected_parts:
            w = (part.get("word") or "").lower()
            if w and w not in seen:
                seen.add(w)
                results.append({
                    "word": w,
                    "display_name": part.get("display_name", w.capitalize()),
                    "ipa": part.get("ipa", ""),
                    "vn_phonetic": part.get("vn_phonetic") or get_vietnamese_phonetic(w, part.get("ipa", "")),
                    "meaning": part.get("meaning", "Chi tiết phát hiện"),
                    "cefr": (part.get("cefr") or "A1").upper(),
                    "tier": part.get("tier", "functional"),
                    "domain": part.get("domain", "objects"),
                    "level_tier": part.get("level_tier", "basic"),
                    "parentObject": primary_word,
                    "isObjectPart": True,
                    "is_learned": bool(part.get("is_learned", False))
                })

    # Sau đó bổ sung từ trong semantic cluster
    for item in best_cluster["words"]:
        w = item["word"].lower()
        if w not in seen:
            seen.add(w)
            ipa_val = item.get("ipa", "")
            vn_phon = get_vietnamese_phonetic(w, ipa_val)
            cefr_u = (item.get("cefr") or "A1").upper()
            results.append({
                "word": w,
                "display_name": w.capitalize(),
                "ipa": ipa_val,
                "vn_phonetic": vn_phon,
                "meaning": item.get("vn", "Từ vựng liên quan"),
                "cefr": cefr_u,
                "tier": item.get("tier", "functional"),
                "domain": item.get("domain", "objects"),
                "level_tier": "basic" if cefr_u in ["A1", "A2"] else "advanced",
                "parentObject": primary_word,
                "isObjectPart": True,
                "is_learned": False
            })

    return results

