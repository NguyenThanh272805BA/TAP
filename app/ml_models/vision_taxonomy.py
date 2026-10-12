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
            "handle": {"vn": "Quai cầm", "cefr": "B1"},
            "rim": {"vn": "Vành miệng cốc", "cefr": "B2"},
            "cup base": {"vn": "Đáy cốc", "cefr": "A2"}
        }
    },
    "book": {
        "vn_name": "Quyển sách",
        "cefr": "A1",
        "parts": {
            "cover": {"vn": "Bìa sách", "cefr": "A2"},
            "page": {"vn": "Trang giấy", "cefr": "A1"},
            "spine": {"vn": "Gáy sách", "cefr": "B2"},
            "bookmark": {"vn": "Thẻ đánh dấu trang", "cefr": "B1"}
        }
    },
    "glasses": {
        "vn_name": "Kính mắt",
        "cefr": "A1",
        "parts": {
            "frame": {"vn": "Gọng kính", "cefr": "B1"},
            "lens": {"vn": "Tròng kính", "cefr": "B1"},
            "temple": {"vn": "Càng kính / Gọng đeo tai", "cefr": "B2"},
            "nose pad": {"vn": "Đệm mũi kính", "cefr": "B2"}
        }
    },
    "watch": {
        "vn_name": "Đồng hồ đeo tay",
        "cefr": "A1",
        "parts": {
            "strap": {"vn": "Dây đeo đồng hồ", "cefr": "B1"},
            "dial": {"vn": "Mặt số đồng hồ", "cefr": "B2"},
            "watch hand": {"vn": "Kim đồng hồ", "cefr": "A2"},
            "crown": {"vn": "Nút xoay chỉnh giờ", "cefr": "B2"}
        }
    },
    "chair": {
        "vn_name": "Chiếc ghế",
        "cefr": "A1",
        "parts": {
            "seat": {"vn": "Mặt ghế ngồi", "cefr": "A2"},
            "backrest": {"vn": "Lưng tựa ghế", "cefr": "B1"},
            "armrest": {"vn": "Tay vịn ghế", "cefr": "B2"},
            "chair leg": {"vn": "Chân ghế", "cefr": "A2"}
        }
    },
    "phone": {
        "vn_name": "Điện thoại di động",
        "cefr": "A1",
        "parts": {
            "screen": {"vn": "Màn hình điện thoại", "cefr": "A2"},
            "camera lens": {"vn": "Ống kính máy ảnh", "cefr": "B1"},
            "flash": {"vn": "Đèn flash", "cefr": "B1"},
            "speaker": {"vn": "Loa ngoài", "cefr": "A2"}
        }
    }
}


def get_part_info(part_word: str, parent_obj: Optional[str] = None) -> Dict[str, Any]:
    """
    Truy xuất đầy đủ metadata học thuật: Phiên âm IPA, Nghĩa tiếng Việt, Cấp độ CEFR
    """
    clean_word = part_word.strip().lower()
    oxford = get_oxford_dict()
    
    # 1. Tìm nghĩa và CEFR từ TAXONOMY
    vn_meaning = "Bộ phận chi tiết"
    cefr = oxford.get(clean_word, "B1")
    
    if parent_obj and parent_obj in OBJECT_PARTS_TAXONOMY:
        parts_dict = OBJECT_PARTS_TAXONOMY[parent_obj].get("parts", {})
        if clean_word in parts_dict:
            vn_meaning = parts_dict[clean_word].get("vn", vn_meaning)
            cefr = parts_dict[clean_word].get("cefr", cefr)
    else:
        # Tìm trong tất cả taxonomy
        for obj, obj_data in OBJECT_PARTS_TAXONOMY.items():
            if clean_word == obj:
                vn_meaning = obj_data.get("vn_name", vn_meaning)
                cefr = obj_data.get("cefr", cefr)
                break
            if clean_word in obj_data.get("parts", {}):
                vn_meaning = obj_data["parts"][clean_word].get("vn", vn_meaning)
                cefr = obj_data["parts"][clean_word].get("cefr", cefr)
                break
                
    # 2. Sinh phiên âm IPA
    phonetic_ipa = ""
    if ipa is not None:
        try:
            phonetic_ipa = f"/{ipa.convert(clean_word)}/"
        except Exception:
            phonetic_ipa = ""
            
    return {
        "word": clean_word,
        "ipa": phonetic_ipa,
        "meaning": vn_meaning,
        "cefr": cefr.upper()
    }


def build_candidate_queries(category: Optional[str] = None) -> List[str]:
    """
    Sinh danh sách text queries để đưa vào OWL-ViT Text Encoder
    """
    queries = []
    if category and category in OBJECT_PARTS_TAXONOMY:
        # Nếu đã biết loại vật thể cha, chỉ quét các chi tiết con của nó
        queries.append(category)
        queries.extend(list(OBJECT_PARTS_TAXONOMY[category]["parts"].keys()))
    else:
        # Quét các vật thể phổ biến + các bộ phận đặc trưng
        for obj_key, data in OBJECT_PARTS_TAXONOMY.items():
            queries.append(obj_key)
            for part_key in list(data["parts"].keys())[:4]: # lấy 4 chi tiết nổi bật nhất của mỗi vật thể
                if part_key not in queries:
                    queries.append(part_key)
    return queries
