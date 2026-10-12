import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import base64
import io
import time
from typing import Dict, List, Any, Optional, Union

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import torch
    from transformers import OwlViTProcessor, OwlViTForObjectDetection
except ImportError:
    torch = None
    OwlViTProcessor = None
    OwlViTForObjectDetection = None

from app.ml_models.vision_taxonomy import (
    OBJECT_PARTS_TAXONOMY,
    get_part_info,
    build_candidate_queries
)

# Đường dẫn thư mục weights local
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models', 'owlvit')
DEFAULT_MODEL_ID = "google/owlvit-base-patch32"


class LocalOwlVitEngine:
    """
    ĐỘNG CƠ THỊ GIÁC MÁY TÍNH NHẬN DIỆN BỘ PHẬN ĐA CẤP BẬC (100% LOCAL / NO-LLM)
    Sử dụng Vision Transformer Open-Vocabulary (OWL-ViT).
    Không phụ thuộc Cloud API hay Generative LLM.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LocalOwlVitEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_dir: Optional[str] = None, lazy: bool = True):
        if getattr(self, '_initialized', False):
            return

        self.model_dir = model_dir or (MODEL_DIR if os.path.exists(MODEL_DIR) else DEFAULT_MODEL_ID)
        self.device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
        self.processor = None
        self.model = None
        self.is_loaded = False
        self._initialized = True

        if not lazy:
            self.load_model()

    def load_model(self) -> bool:
        """Nạp weights của mô hình OWL-ViT vào bộ nhớ RAM / VRAM"""
        if self.is_loaded:
            return True

        if torch is None or OwlViTProcessor is None:
            print("[!] PyTorch hoặc Transformers chưa được cài đặt.")
            return False

        try:
            start_time = time.time()
            target_path = MODEL_DIR if os.path.exists(MODEL_DIR) else DEFAULT_MODEL_ID
            print(f">>> [OwlViT Engine] Đang nạp mô hình từ {target_path} (Thiết bị: {self.device})...")

            self.processor = OwlViTProcessor.from_pretrained(target_path)
            self.model = OwlViTForObjectDetection.from_pretrained(target_path)
            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            load_elapsed = time.time() - start_time
            print(f">>> [OwlViT Engine] Nạp thành công trong {load_elapsed:.2f}s!")
            return True
        except Exception as e:
            print(f"[!] [OwlViT Engine] Lỗi khi nạp mô hình: {e}")
            return False

    @staticmethod
    def _prepare_image(image_input: Union[str, Image.Image, np.ndarray]) -> Image.Image:
        """Chuẩn hóa mọi định dạng ảnh đầu vào (Base64, Numpy OpenCV, PIL) về PIL RGB"""
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")

        if isinstance(image_input, np.ndarray):
            # Nếu là ảnh OpenCV BGR -> chuyển sang RGB
            if len(image_input.shape) == 3 and image_input.shape[2] == 3:
                rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB) if cv2 else image_input[:, :, ::-1]
                return Image.fromarray(rgb)
            return Image.fromarray(image_input).convert("RGB")

        if isinstance(image_input, str):
            # Kiểm tra nếu là chuỗi Base64 Data URI
            if "base64," in image_input:
                image_input = image_input.split("base64,")[1]
            try:
                # Thử giải mã Base64
                image_bytes = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception:
                # Nếu không phải Base64, thử mở file path
                if os.path.exists(image_input):
                    return Image.open(image_input).convert("RGB")
                raise ValueError("Định dạng ảnh đầu vào không hợp lệ!")

        raise TypeError(f"Kiểu dữ liệu ảnh không được hỗ trợ: {type(image_input)}")

    @staticmethod
    def _apply_nms(boxes: List[List[float]], scores: List[float], labels: List[str], iou_threshold: float = 0.5) -> List[int]:
        """Thuật toán Non-Maximum Suppression (NMS) lọc bớt bounding box trùng lặp"""
        if len(boxes) == 0:
            return []

        boxes_arr = np.array(boxes)
        scores_arr = np.array(scores)

        x1 = boxes_arr[:, 0]
        y1 = boxes_arr[:, 1]
        x2 = boxes_arr[:, 2]
        y2 = boxes_arr[:, 3]

        areas = (x2 - x1) * (y2 - y1)
        order = scores_arr.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(int(i))

            if order.size == 1:
                break

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

            # Chỉ lọc NMS nếu 2 box cùng nhãn hoặc đè lên nhau quá nhiều
            same_label = np.array([labels[idx] == labels[i] for idx in order[1:]])
            suppress = np.where((ovr > iou_threshold) & same_label)[0]

            order = np.delete(order, np.concatenate(([0], suppress + 1)))

        return keep

    def detect_parts(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        target_category: Optional[str] = None,
        custom_queries: Optional[List[str]] = None,
        score_threshold: float = 0.14,
        max_results: int = 8
    ) -> Dict[str, Any]:
        """
        Nhận diện vật thể và trích xuất các bộ phận con chi tiết.
        Trả về kết quả JSON với tọa độ chuẩn hóa, nhãn tiếng Anh, IPA, nghĩa tiếng Việt và CEFR.
        """
        if not self.is_loaded:
            if not self.load_model():
                return {
                    "status": "error",
                    "message": "Không thể nạp mô hình OWL-ViT",
                    "detected_parts": []
                }

        try:
            start_infer = time.time()
            pil_img = self._prepare_image(image_input)
            img_width, img_height = pil_img.size

            # 1. Xây dựng danh sách text queries
            if custom_queries and len(custom_queries) > 0:
                raw_queries = custom_queries
            else:
                raw_queries = build_candidate_queries(category=target_category)

            # Thêm tiền tố mô tả tự nhiên để Vision-Language matching tốt hơn
            formatted_texts = [f"a photo of a {q.strip()}" for q in raw_queries]

            # 2. Xử lý qua Processor
            inputs = self.processor(
                text=[formatted_texts],
                images=pil_img,
                return_tensors="pt"
            ).to(self.device)

            # 3. Suy luận không tính Gradient
            with torch.no_grad():
                outputs = self.model(**inputs)

            # 4. Giải mã bounding boxes bằng post_process_grounded_object_detection chuẩn Transformers
            target_sizes = torch.tensor([[img_height, img_width]], device=self.device)
            results = self.processor.post_process_grounded_object_detection(
                outputs=outputs,
                threshold=score_threshold,
                target_sizes=target_sizes,
                text_labels=[formatted_texts]
            )[0]

            boxes = results["boxes"].cpu().numpy().tolist()
            scores = results["scores"].cpu().numpy().tolist()
            labels_idx = results["labels"].cpu().numpy().tolist()

            raw_labels = [raw_queries[idx] for idx in labels_idx]

            # 5. Lọc NMS chống trùng lặp
            keep_indices = self._apply_nms(boxes, scores, raw_labels, iou_threshold=0.45)

            detected_parts = []
            seen_words = set()

            for idx in keep_indices[:max_results]:
                word = raw_labels[idx]
                if word in seen_words:
                    continue
                seen_words.add(word)

                box = boxes[idx]
                score = round(float(scores[idx]), 3)

                # Metadata tiếng Anh học thuật
                meta = get_part_info(word, parent_obj=target_category)

                # Tọa độ chuẩn hóa theo phần trăm (0.0 - 1.0) để vẽ Web Canvas responsive
                norm_box = {
                    "ymin": round(max(0.0, box[1] / img_height), 4),
                    "xmin": round(max(0.0, box[0] / img_width), 4),
                    "ymax": round(min(1.0, box[3] / img_height), 4),
                    "xmax": round(min(1.0, box[2] / img_width), 4),
                    "pixel_box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
                }

                detected_parts.append({
                    "word": meta["word"],
                    "ipa": meta["ipa"],
                    "meaning": meta["meaning"],
                    "cefr": meta["cefr"],
                    "confidence": score,
                    "normalized_box": norm_box
                })

            infer_elapsed = round((time.time() - start_infer) * 1000, 1)

            # Suy đoán vật thể chính
            primary_obj = target_category
            if not primary_obj and len(detected_parts) > 0:
                # Tìm vật thể cha có diện tích lớn nhất hoặc xuất hiện đầu tiên
                for p in detected_parts:
                    if p["word"] in OBJECT_PARTS_TAXONOMY:
                        primary_obj = p["word"]
                        break
                if not primary_obj:
                    primary_obj = detected_parts[0]["word"]

            return {
                "status": "success",
                "primary_object": primary_obj or "unknown",
                "total_detected": len(detected_parts),
                "inference_time_ms": infer_elapsed,
                "detected_parts": detected_parts
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi trong quá trình nhận diện: {str(e)}",
                "detected_parts": []
            }
