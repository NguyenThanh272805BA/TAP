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
    # Chọn lọc cân bằng giữa 4 miền thực thể để đảm bảo nhận diện mọi thứ
    selected_queries: List[str] = []

    # Đồ vật nổi bật
    objs = domain_items.get("objects", [])
    selected_queries.extend(objs[:10] if objs else ["laptop", "phone", "backpack", "book", "cup", "chair", "desk", "bottle"])

    # Sinh vật & con người
    creatures = domain_items.get("creatures", [])
    selected_queries.extend(creatures[:8] if creatures else ["person", "student", "cat", "dog", "plant", "tree", "bird"])

    # Khung cảnh không gian
    scenes = domain_items.get("scenes", [])
    selected_queries.extend(scenes[:8] if scenes else ["classroom", "office", "cafe", "living room", "street", "library", "park"])

    # Môi trường & thời tiết
    env = domain_items.get("environment", [])
    selected_queries.extend(env[:6] if env else ["sunlight", "window", "blue sky", "cloud", "shadow", "lamp"])

    return selected_queries[:32]
