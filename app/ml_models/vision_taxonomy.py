import os
import json
from typing import Dict, List, Any, Optional

try:
    import eng_to_ipa as ipa
except ImportError:
    ipa = None

# Đường dẫn tới oxford_5000.json
OXFORD_PATH = os.path.join(os.path.dirname(__file__), 'oxford_5000.json')

_OXFORD_CACHE: Optional[Dict[str, str]] = None

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


# 1. TỪ ĐIỂN PHÂN CẤP ĐỒ VẬT -> BỘ PHẬN CON (OBJECT-TO-PARTS TAXONOMY)
OBJECT_PARTS_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "backpack": {
        "vn_name": "Cặp sách / Ba lô",
        "cefr": "A1",
        "parts": {
            "zipper": {"vn": "Khóa kéo", "cefr": "B1"},
            "shoulder strap": {"vn": "Quai đeo vai", "cefr": "B1"},
            "buckle": {"vn": "Khóa bấm / Khóa cài", "cefr": "B2"},
            "pocket": {"vn": "Ngăn túi", "cefr": "A2"},
            "handle": {"vn": "Quai xách / Tay cầm", "cefr": "B1"},
            "seam": {"vn": "Đường may ranh giới", "cefr": "B2"},
            "logo": {"vn": "Nhãn hiệu / Logo", "cefr": "B1"}
        }
    },
    "laptop": {
        "vn_name": "Máy tính xách tay",
        "cefr": "A1",
        "parts": {
            "keyboard": {"vn": "Bàn phím", "cefr": "A2"},
            "screen": {"vn": "Màn hình hiển thị", "cefr": "A2"},
            "trackpad": {"vn": "Bàn di chuột cảm ứng", "cefr": "B1"},
            "webcam": {"vn": "Camera máy tính", "cefr": "B1"},
            "key": {"vn": "Phím bấm", "cefr": "A2"},
            "hinge": {"vn": "Bản lề gập máy", "cefr": "B2"},
            "logo": {"vn": "Biểu tượng thương hiệu", "cefr": "B1"}
        }
    },
    "shirt": {
        "vn_name": "Áo sơ mi / Áo",
        "cefr": "A1",
        "parts": {
            "collar": {"vn": "Cổ áo", "cefr": "B1"},
            "sleeve": {"vn": "Tay áo", "cefr": "B1"},
            "button": {"vn": "Cúc áo / Khuy", "cefr": "A2"},
            "pocket": {"vn": "Túi áo", "cefr": "A2"},
            "cuff": {"vn": "Cổ tay áo", "cefr": "B2"}
        }
    },
    "bicycle": {
        "vn_name": "Xe đạp",
        "cefr": "A1",
        "parts": {
            "handlebar": {"vn": "Ghi-đông / Tay lái", "cefr": "B2"},
            "wheel": {"vn": "Bánh xe", "cefr": "A2"},
            "pedal": {"vn": "Bàn đạp", "cefr": "B1"},
            "saddle": {"vn": "Yên xe", "cefr": "B2"},
            "chain": {"vn": "Xích xe đạp", "cefr": "B1"},
            "tire": {"vn": "Lốp xe", "cefr": "B1"},
            "brake": {"vn": "Phanh / Thắng xe", "cefr": "B1"}
        }
    },
    "bottle": {
        "vn_name": "Chai nước / Bình nước",
        "cefr": "A1",
        "parts": {
            "cap": {"vn": "Nắp chai", "cefr": "A2"},
            "label": {"vn": "Nhãn dán thương hiệu", "cefr": "B1"},
            "bottle neck": {"vn": "Cổ chai", "cefr": "B1"},
            "bottle base": {"vn": "Đáy chai", "cefr": "A2"}
        }
    },
    "shoes": {
        "vn_name": "Đôi giày",
        "cefr": "A1",
        "parts": {
            "shoelace": {"vn": "Dây buộc giày", "cefr": "B1"},
            "sole": {"vn": "Đế giày", "cefr": "B2"},
            "tongue": {"vn": "Lưỡi gà giày", "cefr": "B2"},
            "heel": {"vn": "Gót giày", "cefr": "B1"}
        }
    },
    "cup": {
        "vn_name": "Cốc / Ly tách",
        "cefr": "A1",
        "parts": {
            "handle": {"vn": "Quai cầm", "cefr": "B1", "tier": "functional"},
            "rim": {"vn": "Vành miệng cốc", "cefr": "B2", "tier": "micro"},
            "cup base": {"vn": "Đáy cốc", "cefr": "A2", "tier": "functional"}
        }
    },
    "book": {
        "vn_name": "Quyển sách",
        "cefr": "A1",
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
        "parts": {
            "cap": {"vn": "Nắp bút", "cefr": "A2", "tier": "functional"},
            "clip": {"vn": "Kẹp cài bút", "cefr": "B1", "tier": "micro"},
            "nib": {"vn": "Ngòi bút", "cefr": "B2", "tier": "micro"},
            "barrel": {"vn": "Thân bút", "cefr": "B1", "tier": "functional"}
        }
    },
    "notebook": {
        "vn_name": "Sổ tay / Quyển vở",
        "cefr": "A1",
        "parts": {
            "cover": {"vn": "Bìa sổ", "cefr": "A2", "tier": "functional"},
            "spiral": {"vn": "Lò xo gáy sổ", "cefr": "B2", "tier": "micro"},
            "page": {"vn": "Trang giấy", "cefr": "A1", "tier": "functional"}
        }
    },
    "scissors": {
        "vn_name": "Cây kéo",
        "cefr": "A2",
        "parts": {
            "blade": {"vn": "Lưỡi kéo", "cefr": "B1", "tier": "functional"},
            "handle": {"vn": "Quai cầm kéo", "cefr": "B1", "tier": "functional"},
            "pivot": {"vn": "Trục ốc xoay", "cefr": "B2", "tier": "micro"}
        }
    },
    "desk": {
        "vn_name": "Bàn làm việc",
        "cefr": "A1",
        "parts": {
            "tabletop": {"vn": "Mặt bàn", "cefr": "A2", "tier": "functional"},
            "drawer": {"vn": "Ngăn kéo bàn", "cefr": "A2", "tier": "functional"},
            "desk leg": {"vn": "Chân bàn", "cefr": "A2", "tier": "functional"}
        }
    },
    "monitor": {
        "vn_name": "Màn hình vi tính",
        "cefr": "A2",
        "parts": {
            "screen": {"vn": "Mặt hiển thị", "cefr": "A2", "tier": "functional"},
            "stand": {"vn": "Chân đế màn hình", "cefr": "B1", "tier": "functional"},
            "bezel": {"vn": "Viền màn hình", "cefr": "B2", "tier": "micro"}
        }
    },
    "mouse": {
        "vn_name": "Chuột máy tính",
        "cefr": "A1",
        "parts": {
            "scroll wheel": {"vn": "Con lăn chuột", "cefr": "B1", "tier": "functional"},
            "button": {"vn": "Nút bấm chuột", "cefr": "A2", "tier": "functional"},
            "cable": {"vn": "Dây cáp chuột", "cefr": "B1", "tier": "micro"}
        }
    },
    "clock": {
        "vn_name": "Đồng hồ treo tường / Để bàn",
        "cefr": "A1",
        "parts": {
            "clock face": {"vn": "Mặt số đồng hồ", "cefr": "B1", "tier": "functional"},
            "hour hand": {"vn": "Kim giờ", "cefr": "A2", "tier": "micro"},
            "minute hand": {"vn": "Kim phút", "cefr": "A2", "tier": "micro"},
            "frame": {"vn": "Khung đồng hồ", "cefr": "B1", "tier": "functional"}
        }
    },
    "lamp": {
        "vn_name": "Đèn bàn / Đèn ngủ",
        "cefr": "A1",
        "parts": {
            "lampshade": {"vn": "Chao đèn", "cefr": "B2", "tier": "micro"},
            "bulb": {"vn": "Bóng đèn", "cefr": "A2", "tier": "functional"},
            "switch": {"vn": "Công tắc đèn", "cefr": "B1", "tier": "micro"},
            "base": {"vn": "Đế đèn", "cefr": "B1", "tier": "functional"}
        }
    },
    "headphone": {
        "vn_name": "Tai nghe",
        "cefr": "A2",
        "parts": {
            "earpad": {"vn": "Đệm tai nghe", "cefr": "B2", "tier": "micro"},
            "headband": {"vn": "Vòng trùm đầu", "cefr": "B2", "tier": "micro"},
            "ear cup": {"vn": "Chụp tai", "cefr": "B2", "tier": "functional"},
            "cable": {"vn": "Dây tai nghe", "cefr": "B1", "tier": "functional"}
        }
    },
    "wallet": {
        "vn_name": "Ví tiền",
        "cefr": "A2",
        "parts": {
            "zipper": {"vn": "Khóa kéo ví", "cefr": "B1", "tier": "functional"},
            "card slot": {"vn": "Ngăn cắm thẻ", "cefr": "B1", "tier": "micro"},
            "pocket": {"vn": "Ngăn ví", "cefr": "A2", "tier": "functional"}
        }
    },
    "umbrella": {
        "vn_name": "Cây dù / Ô",
        "cefr": "A1",
        "parts": {
            "canopy": {"vn": "Tán vải ô", "cefr": "B2", "tier": "functional"},
            "handle": {"vn": "Tay cầm ô", "cefr": "B1", "tier": "functional"},
            "rib": {"vn": "Nan hoa xương ô", "cefr": "B2", "tier": "micro"},
            "shaft": {"vn": "Cán gậy ô", "cefr": "B2", "tier": "micro"}
        }
    },
    "plant": {
        "vn_name": "Chậu cây cảnh",
        "cefr": "A1",
        "parts": {
            "leaf": {"vn": "Lá cây", "cefr": "A1", "tier": "functional"},
            "stem": {"vn": "Cành thân cây", "cefr": "B1", "tier": "micro"},
            "pot": {"vn": "Chậu trồng", "cefr": "A2", "tier": "functional"}
        }
    }
}


def get_part_info(part_word: str, parent_obj: Optional[str] = None) -> Dict[str, Any]:
    """
    Truy xuất đầy đủ metadata học thuật: Phiên âm IPA, Nghĩa tiếng Việt, Cấp độ CEFR và Level Tier
    """
    clean_word = part_word.strip().lower()
    oxford = get_oxford_dict()
    
    # 1. Tìm nghĩa và CEFR từ TAXONOMY
    vn_meaning = "Chi tiết vật thể"
    cefr = oxford.get(clean_word, "B1")
    tier = "functional"
    
    if parent_obj and parent_obj in OBJECT_PARTS_TAXONOMY:
        parts_dict = OBJECT_PARTS_TAXONOMY[parent_obj].get("parts", {})
        if clean_word in parts_dict:
            vn_meaning = parts_dict[clean_word].get("vn", vn_meaning)
            cefr = parts_dict[clean_word].get("cefr", cefr)
            tier = parts_dict[clean_word].get("tier", "functional")
    else:
        # Tìm trong tất cả taxonomy
        for obj, obj_data in OBJECT_PARTS_TAXONOMY.items():
            if clean_word == obj:
                vn_meaning = obj_data.get("vn_name", vn_meaning)
                cefr = obj_data.get("cefr", cefr)
                tier = "macro"
                break
            if clean_word in obj_data.get("parts", {}):
                vn_meaning = obj_data["parts"][clean_word].get("vn", vn_meaning)
                cefr = obj_data["parts"][clean_word].get("cefr", cefr)
                tier = obj_data["parts"][clean_word].get("tier", "functional")
                break
                
    # 2. Sinh phiên âm IPA
    phonetic_ipa = ""
    if ipa is not None:
        try:
            phonetic_ipa = f"/{ipa.convert(clean_word)}/"
        except Exception:
            phonetic_ipa = ""

    cefr_upper = cefr.upper()
    level_tier = "basic" if cefr_upper in ["A1", "A2"] else "advanced"
            
    return {
        "word": clean_word,
        "ipa": phonetic_ipa,
        "meaning": vn_meaning,
        "cefr": cefr_upper,
        "tier": tier,
        "level_tier": level_tier
    }


def build_candidate_queries(category: Optional[str] = None, granularity: str = "all") -> List[str]:
    """
    Sinh danh sách text queries để đưa vào OWL-ViT Text Encoder dựa theo:
    - category: Lọc theo vật thể cụ thể hoặc quét đa vật thể.
    - granularity: 'macro' (Cơ bản - chỉ vật thể), 'functional' (Trung cấp - bộ phận chính),
                   'micro' (Chuyên sâu - chi tiết vi mô), 'all' (Toàn diện).
    """
    granularity = (granularity or "all").lower()

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

    # Chế độ tự động quét đa vật thể
    all_objects = list(OBJECT_PARTS_TAXONOMY.keys())

    if granularity == "macro":
        # Chỉ quét các vật thể nguyên khối
        return all_objects[:24]

    elif granularity == "functional":
        # Quét vật thể chính + các bộ phận chức năng nổi bật
        queries = all_objects[:12]
        for obj in all_objects[:10]:
            parts = OBJECT_PARTS_TAXONOMY[obj].get("parts", {})
            for p, info in parts.items():
                if info.get("tier") == "functional" or info.get("cefr") in ["A1", "A2"]:
                    if p not in queries:
                        queries.append(p)
        return queries[:32]

    elif granularity == "micro":
        # Quét chuyên sâu các chi tiết vi mô / linh kiện con
        queries = []
        for obj in all_objects:
            parts = OBJECT_PARTS_TAXONOMY[obj].get("parts", {})
            for p, info in parts.items():
                if info.get("tier") == "micro" or info.get("cefr") in ["B1", "B2", "C1"]:
                    if p not in queries:
                        queries.append(p)
        return queries[:32]

    else: # "all"
        queries = all_objects[:14]
        for obj in all_objects[:12]:
            parts = list(OBJECT_PARTS_TAXONOMY[obj].get("parts", {}).keys())[:2]
            for p in parts:
                if p not in queries:
                    queries.append(p)
        return queries[:32]
