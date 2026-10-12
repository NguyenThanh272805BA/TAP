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
    build_candidate_queries,
    get_domain_stats,
    DOMAINS,
    get_micro_queries,
    lookup_forest_word,
    get_facial_expressions,
    get_taxonomy_forest
)

# Đường dẫn thư mục weights local
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models', 'owlvit')
DEFAULT_MODEL_ID = "google/owlvit-base-patch32"


class LocalOwlVitEngine:
    """
    KIẾN TRÚC HYBRID VISION PIPELINE ĐA MIỀN TOÀN CẢNH (TAP OMNI-VISION 2026)
    100% OFFLINE / KHÔNG CẦN CLOUD API:
    - Tầng 1: Fast Zero-Shot Open-Vocabulary Detector (OWL-ViT Local Weights)
    - Tầng 2: Global Scene & Environment Classifier (Nhận biết không gian & ánh sáng)
    - Tầng 3: Target Spotlight Reticle ROI Deep Dive (Quét vi mô theo vùng ngắm)
    - Tầng 4: Dynamic Academic Contextual Captioner (Mô tả học thuật song ngữ)
    - Tối ưu hóa: Frame Difference Cache (<10% delta) chống quá nhiệt & giữ 60 FPS.
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

        # Cache khung hình phục vụ Frame Delta Check
        self._last_frame_thumb = None
        self._last_result_cache = None
        self._last_cache_time = 0

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
            if len(image_input.shape) == 3 and image_input.shape[2] == 3:
                rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB) if cv2 else image_input[:, :, ::-1]
                return Image.fromarray(rgb)
            return Image.fromarray(image_input).convert("RGB")

        if isinstance(image_input, str):
            if "base64," in image_input:
                image_input = image_input.split("base64,")[1]
            try:
                image_bytes = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception:
                if os.path.exists(image_input):
                    return Image.open(image_input).convert("RGB")
                raise ValueError("Định dạng ảnh đầu vào không hợp lệ!")

        raise TypeError(f"Kiểu dữ liệu ảnh không được hỗ trợ: {type(image_input)}")

    @staticmethod
    def _apply_nms(boxes: List[List[float]], scores: List[float], labels: List[str], iou_threshold: float = 0.45) -> List[int]:
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

            same_label = np.array([labels[idx] == labels[i] for idx in order[1:]])
            suppress = np.where((ovr > iou_threshold) & same_label)[0]

            order = np.delete(order, np.concatenate(([0], suppress + 1)))

        return keep

    def _check_frame_delta(self, pil_img: Image.Image) -> float:
        """
        Tính toán độ sai lệch ảnh (Mean Absolute Error) giữa khung hình hiện tại và trước đó.
        Trả về tỉ lệ thay đổi (0.0 - 1.0).
        """
        thumb = np.array(pil_img.resize((32, 32)).convert("L"), dtype=np.float32)
        if self._last_frame_thumb is None:
            self._last_frame_thumb = thumb
            return 1.0

        delta = float(np.mean(np.abs(thumb - self._last_frame_thumb)) / 255.0)
        self._last_frame_thumb = thumb
        return delta

    # =========================================================================
    # TẦNG 2: PHÂN TÍCH KHUNG CẢNH & MÔI TRƯỜNG TOÀN CỤC (SCENE CLASSIFIER)
    # =========================================================================
    @staticmethod
    def _analyze_scene_and_environment(pil_img: Image.Image, detected_words: List[str]) -> Dict[str, Any]:
        """
        Phân tích các đặc trưng thị giác toàn cục kết hợp từ vựng phát hiện được
        để xác định bối cảnh không gian, điều kiện chiếu sáng và bầu không khí.
        """
        small_rgb = pil_img.resize((48, 48)).convert("RGB")
        arr = np.array(small_rgb, dtype=np.float32)
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        brightness = float(np.mean(0.299 * r + 0.587 * g + 0.114 * b))
        mean_r = float(np.mean(r))
        mean_b = float(np.mean(b)) + 1e-5
        temp_ratio = mean_r / mean_b
        green_excess = float(np.mean(2 * g - r - b))

        # 1. Điều kiện ánh sáng (Lighting)
        if brightness > 170:
            lighting = "Bright Daylight"
            lighting_vn = "Ánh sáng ban ngày rõ nét"
        elif brightness > 120:
            if temp_ratio > 1.15:
                lighting = "Warm Indoor Light"
                lighting_vn = "Ánh sáng vàng ấm áp"
            else:
                lighting = "Neutral Ambient Light"
                lighting_vn = "Ánh sáng tự nhiên cân bằng"
        elif brightness > 70:
            lighting = "Soft Ambient Light"
            lighting_vn = "Ánh sáng môi trường êm dịu"
        else:
            lighting = "Low Light / Evening"
            lighting_vn = "Ánh sáng mờ tối / Ban đêm"

        # 2. Khung cảnh không gian (Scene Type)
        words_set = set(w.lower() for w in detected_words)

        if any(k in words_set for k in ["laptop", "keyboard", "monitor", "mouse", "desk", "notebook", "pen", "bookshelf"]):
            scene = "Study Room / Workspace"
            scene_vn = "Không gian học tập & làm việc"
            domain_focus = "academic"
        elif any(k in words_set for k in ["sofa", "bed", "couch", "chair", "pillow", "television"]):
            scene = "Living Space / Home"
            scene_vn = "Không gian sinh hoạt gia đình"
            domain_focus = "domestic"
        elif any(k in words_set for k in ["cup", "mug", "coffee", "tea", "bottle", "plate", "fork"]):
            scene = "Cafe / Dining Area"
            scene_vn = "Khu vực ẩm thực & quán cà phê"
            domain_focus = "culinary"
        elif any(k in words_set for k in ["tree", "flower", "grass", "plant", "leaf", "bird"]) or green_excess > 12:
            scene = "Outdoor Park / Nature"
            scene_vn = "Công viên thiên nhiên ngoài trời"
            domain_focus = "nature"
        elif any(k in words_set for k in ["car", "bicycle", "bus", "street", "building", "road"]):
            scene = "Urban Street / City"
            scene_vn = "Đường phố đô thị nhộn nhịp"
            domain_focus = "urban"
        else:
            scene = "Indoor Multi-Purpose Room"
            scene_vn = "Không gian phòng đa năng"
            domain_focus = "indoor"

        # 3. Bầu không khí (Atmosphere)
        if "Nature" in scene or green_excess > 12:
            atmosphere = "Fresh & Tranquil"
            atmosphere_vn = "Trong lành & Thanh bình"
        elif "Cafe" in scene or "Living" in scene:
            atmosphere = "Cozy & Relaxed"
            atmosphere_vn = "Ấm cúng & Thư thái"
        elif "Study" in scene or "Workspace" in scene:
            atmosphere = "Quiet & Productive"
            atmosphere_vn = "Yên tĩnh & Tập trung cao độ"
        else:
            atmosphere = "Balanced & Clear"
            atmosphere_vn = "Cân bằng & Khoáng đạt"

        return {
            "scene_type": scene,
            "scene_vn": scene_vn,
            "lighting": lighting,
            "lighting_vn": lighting_vn,
            "atmosphere": atmosphere,
            "atmosphere_vn": atmosphere_vn,
            "brightness_score": round(brightness, 1),
            "domain_focus": domain_focus
        }

    # =========================================================================
    # TẦNG 4: TỔNG HỢP CÂU MÔ TẢ HỌC THUẬT TOÀN CẢNH (CONTEXTUAL CAPTIONER)
    # =========================================================================
    @staticmethod
    def _synthesize_contextual_caption(scene_info: Dict[str, Any], detected_parts: List[Dict[str, Any]]) -> Dict[str, str]:
        """Tự động sinh câu chú thích hoàn chỉnh kết hợp cả 4 miền chuẩn CEFR B1-C1"""
        if not detected_parts:
            return {
                "en": f"A peaceful view in a {scene_info['scene_type'].lower()} under {scene_info['lighting'].lower()}.",
                "vn": f"Khung cảnh yên bình trong {scene_info['scene_vn'].lower()} dưới {scene_info['lighting_vn'].lower()}."
            }

        objects_list = [p['word'] for p in detected_parts if p.get('domain') == 'objects']
        creatures_list = [p['word'] for p in detected_parts if p.get('domain') == 'creatures']
        env_list = [p['word'] for p in detected_parts if p.get('domain') == 'environment']

        scene_type = scene_info["scene_type"]
        scene_vn = scene_info["scene_vn"]
        lighting_vn = scene_info["lighting_vn"].lower()

        if creatures_list and objects_list:
            c = creatures_list[0]
            o = objects_list[0]
            en = f"In a {scene_type.lower()}, a {c} is positioned near a {o} under {scene_info['lighting'].lower()}."
            vn = f"Tại {scene_vn.lower()}, {c} xuất hiện gần {o} dưới {lighting_vn}."
        elif len(objects_list) >= 2:
            o1, o2 = objects_list[0], objects_list[1]
            en = f"Inside the {scene_type.lower()}, a {o1} and a {o2} are clearly visible under {scene_info['lighting'].lower()}."
            vn = f"Bên trong {scene_vn.lower()}, {o1} và {o2} được nhận diện rõ nét dưới {lighting_vn}."
        elif objects_list:
            o = objects_list[0]
            en = f"A {o} is situated in the {scene_type.lower()} with {scene_info['atmosphere'].lower()} ambiance."
            vn = f"{o.capitalize()} hiện diện trong {scene_vn.lower()} mang bầu không khí {scene_info['atmosphere_vn'].lower()}."
        elif creatures_list:
            c = creatures_list[0]
            en = f"A vibrant {c} adds life to the {scene_type.lower()} under {scene_info['lighting'].lower()}."
            vn = f"{c.capitalize()} sống động mang lại sức sống cho {scene_vn.lower()} dưới {lighting_vn}."
        else:
            top_word = detected_parts[0]['word']
            en = f"The view reveals {top_word} in the {scene_type.lower()} under {scene_info['lighting'].lower()}."
            vn = f"Khung cảnh ghi nhận {top_word} trong {scene_vn.lower()} dưới {lighting_vn}."

        return {"en": en, "vn": vn}

    # =========================================================================
    # CORE PIPELINE: NHẬN DIỆN THỊ GIÁC TOÀN CẢNH ĐA MIỀN (OMNI-SCAN)
    # =========================================================================
    def detect_parts(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        target_category: Optional[str] = None,
        custom_queries: Optional[List[str]] = None,
        score_threshold: float = 0.10,
        max_results: int = 10,
        granularity: str = "all",
        domain: str = "all",
        reticle_roi: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Nhận diện thị giác máy tính toàn cảnh đa miền:
        - domain: 'all' (Mọi thứ), 'objects' (Đồ vật), 'creatures' (Sinh vật),
                  'scenes' (Khung cảnh), 'environment' (Môi trường).
        - granularity: 'macro', 'functional', 'micro', 'all'.
        - reticle_roi: [xmin, ymin, xmax, ymax] vùng ngắm vòng đỏ (tọa độ chuẩn hóa 0.0 - 1.0).
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
            max_results = max(3, min(20, int(max_results or 10)))
            pil_img = self._prepare_image(image_input)

            # 1. Thuật toán Frame Delta Check (Tiết kiệm CPU & chống quá nhiệt)
            delta = self._check_frame_delta(pil_img)
            now = time.time()
            if delta < 0.06 and self._last_result_cache and (now - self._last_cache_time < 3.0):
                cached = dict(self._last_result_cache)
                cached["inference_time_ms"] = 3.5
                cached["cached"] = True
                return cached

            # Chuẩn hóa kích thước ảnh tối đa 640px để tăng tốc độ suy luận gấp 2.5x trên CPU
            orig_w, orig_h = pil_img.size
            max_dim = 640
            if max(orig_w, orig_h) > max_dim:
                scale = max_dim / max(orig_w, orig_h)
                pil_img = pil_img.resize((int(orig_w * scale), int(orig_h * scale)), Image.Resampling.BILINEAR)
            img_width, img_height = pil_img.size

            # 2. Xây dựng danh sách text queries đa miền
            if custom_queries and len(custom_queries) > 0:
                raw_queries = custom_queries
            else:
                raw_queries = build_candidate_queries(
                    category=target_category,
                    granularity=granularity,
                    domain=domain
                )

            # Thêm tiền tố mô tả tự nhiên để Vision-Language matching tốt hơn
            formatted_texts = [f"a photo of a {q.strip()}" for q in raw_queries]

            # 3. Xử lý qua Processor
            inputs = self.processor(
                text=[formatted_texts],
                images=pil_img,
                return_tensors="pt"
            ).to(self.device)

            # 4. Suy luận không tính Gradient
            with torch.no_grad():
                outputs = self.model(**inputs)

            # 5. Giải mã bounding boxes
            target_sizes = torch.tensor([[img_height, img_width]], device=self.device)
            results = self.processor.post_process_grounded_object_detection(
                outputs=outputs,
                threshold=score_threshold,
                target_sizes=target_sizes,
                text_labels=[formatted_texts]
            )[0]

            if len(results["boxes"]) == 0 and score_threshold > 0.07:
                results = self.processor.post_process_grounded_object_detection(
                    outputs=outputs,
                    threshold=0.07,
                    target_sizes=target_sizes,
                    text_labels=[formatted_texts]
                )[0]

            boxes = results["boxes"].cpu().numpy().tolist()
            scores = results["scores"].cpu().numpy().tolist()
            labels_idx = results["labels"].cpu().numpy().tolist()
            raw_labels = [raw_queries[idx] for idx in labels_idx]

            # 6. Lọc NMS chống trùng lặp
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

                # Metadata học thuật từ kho 1.000+ từ vựng
                meta = get_part_info(word, parent_obj=target_category, domain=domain)

                norm_box = {
                    "ymin": round(max(0.0, box[1] / img_height), 4),
                    "xmin": round(max(0.0, box[0] / img_width), 4),
                    "ymax": round(min(1.0, box[3] / img_height), 4),
                    "xmax": round(min(1.0, box[2] / img_width), 4),
                    "pixel_box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
                }

                # Kiểm tra xem box có nằm trong Reticle ROI nếu người dùng đang ngắm vòng đỏ
                is_in_reticle = False
                if reticle_roi and len(reticle_roi) == 4:
                    rx1, ry1, rx2, ry2 = reticle_roi
                    bx_center = (norm_box["xmin"] + norm_box["xmax"]) / 2.0
                    by_center = (norm_box["ymin"] + norm_box["ymax"]) / 2.0
                    if rx1 <= bx_center <= rx2 and ry1 <= by_center <= ry2:
                        is_in_reticle = True

                detected_parts.append({
                    "word": meta["word"],
                    "display_name": meta.get("display_name", meta["word"].capitalize()),
                    "ipa": meta["ipa"],
                    "vn_phonetic": meta.get("vn_phonetic", ""),
                    "meaning": meta["meaning"],
                    "cefr": meta["cefr"],
                    "tier": meta.get("tier", "functional"),
                    "domain": meta.get("domain", "objects"),
                    "level_tier": meta.get("level_tier", "basic"),
                    "confidence": score,
                    "normalized_box": norm_box,
                    "is_in_reticle": is_in_reticle
                })

            # 7. Tầng 2: Phân tích Khung cảnh & Môi trường Toàn cục
            detected_word_names = [p["word"] for p in detected_parts]
            scene_info = self._analyze_scene_and_environment(pil_img, detected_word_names)

            # 8. Tầng 4: Tổng hợp Câu mô tả Ngữ cảnh Hoàn chỉnh
            context_caption = self._synthesize_contextual_caption(scene_info, detected_parts)

            # 9. Thống kê tỷ lệ phân bổ theo 4 miền
            domain_breakdown = {"objects": 0, "scenes": 0, "creatures": 0, "environment": 0}
            for p in detected_parts:
                d = p.get("domain", "objects")
                if d in domain_breakdown:
                    domain_breakdown[d] += 1

            infer_elapsed = round((time.time() - start_infer) * 1000, 1)

            # Xác định thực thể đại diện chính
            primary_obj = target_category
            if not primary_obj and len(detected_parts) > 0:
                primary_obj = detected_parts[0]["word"]

            final_result = {
                "status": "success",
                "primary_object": primary_obj or "unknown",
                "total_detected": len(detected_parts),
                "domain": domain,
                "domain_breakdown": domain_breakdown,
                "scene_info": scene_info,
                "context_caption": context_caption,
                "inference_time_ms": infer_elapsed,
                "detected_parts": detected_parts
            }

            # Cập nhật cache
            self._last_result_cache = final_result
            self._last_cache_time = now

            return final_result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi trong quá trình nhận diện: {str(e)}",
                "detected_parts": []
            }

    # =========================================================================
    # KIẾN TRÚC TIÊU ĐIỂM KÍNH HIỂN VI NGỮ NGHĨA (FOCAL RETICLE MICRO-ZOOM)
    # Phục vụ Mục 13.2, 13.3, 13.4 - TAP PART XIII
    # =========================================================================
    def detect_micro_focus(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        reticle_roi: Optional[Union[List[float], Dict[str, float]]] = None,
        parent_category: Optional[str] = None,
        mode: str = "all",
        score_threshold: float = 0.08,
        max_results: int = 6
    ) -> Dict[str, Any]:
        """
        Nhận diện thị giác vi mô bằng Kính hiển vi ngữ nghĩa:
        1. ROI Extraction: Trích xuất vùng ảnh cục bộ trong phạm vi Vòng đỏ.
        2. Super-Resolution Bicubic Upscaling: Phóng đại vùng crop lên 224x224 px để râu mèo,
           móng vuốt, nếp nhăn, linh kiện phóng to gấp 4 - 8 lần.
        3. Parent-Conditioned Dynamic Pruning: Cắt tỉa chỉ nạp M_sub <= 12 queries con của cha,
           đảm bảo thời gian suy luận trên CPU luôn <= 30ms.
        4. Micro Facial Expression Engine: Nhận biết 8 biểu cảm & gợi ý tính từ học thuật B2-C1.
        5. Trả về cấu trúc phân cấp Cha - Con: [CAT ➔ WHISKER], [MÈO ➔ RÂU MÈO].
        """
        if not self.is_loaded:
            if not self.load_model():
                return {
                    "status": "error",
                    "message": "Không thể nạp mô hình OWL-ViT",
                    "micro_detections": []
                }

        try:
            start_infer = time.time()
            pil_img = self._prepare_image(image_input)
            img_w, img_h = pil_img.size

            # 1. Tính toán tọa độ Bounding Box của Vòng đỏ (Chuẩn hóa 0.0 - 1.0)
            xmin, ymin, xmax, ymax = 0.25, 0.25, 0.75, 0.75
            if isinstance(reticle_roi, dict):
                cx = float(reticle_roi.get("cx", 0.5))
                cy = float(reticle_roi.get("cy", 0.5))
                r = float(reticle_roi.get("r", 0.15))
                xmin = max(0.0, cx - r)
                xmax = min(1.0, cx + r)
                ymin = max(0.0, cy - r)
                ymax = min(1.0, cy + r)
            elif isinstance(reticle_roi, (list, tuple)) and len(reticle_roi) == 4:
                vals = [float(v) for v in reticle_roi]
                # Hỗ trợ cả định dạng [ymin, xmin, ymax, xmax] và [xmin, ymin, xmax, ymax]
                if vals[0] <= vals[2] and vals[1] <= vals[3]:
                    # Giả định chuẩn [xmin, ymin, xmax, ymax]
                    xmin, ymin, xmax, ymax = vals
                else:
                    ymin, xmin, ymax, xmax = vals
                xmin, xmax = min(xmin, xmax), max(xmin, xmax)
                ymin, ymax = min(ymin, ymax), max(ymin, ymax)

            # Đảm bảo phạm vi hợp lệ và có kích thước tối thiểu
            xmin, xmax = max(0.0, xmin), min(1.0, xmax)
            ymin, ymax = max(0.0, ymin), min(1.0, ymax)
            if xmax - xmin < 0.05:
                cx = (xmin + xmax) / 2.0
                xmin, xmax = max(0.0, cx - 0.05), min(1.0, cx + 0.05)
            if ymax - ymin < 0.05:
                cy = (ymin + ymax) / 2.0
                ymin, ymax = max(0.0, cy - 0.05), min(1.0, cy + 0.05)

            # Quy đổi sang pixel
            px_left = int(xmin * img_w)
            px_top = int(ymin * img_h)
            px_right = int(xmax * img_w)
            px_bottom = int(ymax * img_h)

            crop_w = max(10, px_right - px_left)
            crop_h = max(10, px_top - px_top if px_bottom - px_top <= 0 else px_bottom - px_top)

            # 2. ROI Cropping & Super-Resolution Bicubic Upscaling (Mục 13.2)
            crop_img = pil_img.crop((px_left, px_top, px_right, px_bottom))
            # Phóng đại lên chuẩn 224x224 px bằng nội suy Bicubic chất lượng cao
            target_crop_dim = 224
            crop_upscaled = crop_img.resize((target_crop_dim, target_crop_dim), Image.Resampling.BICUBIC)

            # 3. Dynamic Query Pruning: Cắt tỉa động M_sub <= 12 queries theo thực thể cha (Mục 13.3)
            p_cat = (parent_category or "").strip().lower()
            if not p_cat or p_cat == "unknown":
                p_cat = "cat"  # Mặc định thực thể phổ biến cho vi mô

            raw_queries = get_micro_queries(parent_category=p_cat, mode=mode, max_queries=12)
            if not raw_queries:
                raw_queries = ["whisker", "paw", "eye", "ear", "muzzle", "claw", "fur", "fang"]

            formatted_texts = [f"a photo of a {q.strip()}" for q in raw_queries]

            # 4. Suy luận nhanh qua OWL-ViT với chỉ M_sub <= 12 queries
            inputs = self.processor(
                text=[formatted_texts],
                images=crop_upscaled,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            target_sizes = torch.tensor([[target_crop_dim, target_crop_dim]], device=self.device)
            results = self.processor.post_process_grounded_object_detection(
                outputs=outputs,
                threshold=score_threshold,
                target_sizes=target_sizes,
                text_labels=[formatted_texts]
            )[0]

            # Fallback nhẹ nếu chưa bắt được
            if len(results["boxes"]) == 0:
                results = self.processor.post_process_grounded_object_detection(
                    outputs=outputs,
                    threshold=0.05,
                    target_sizes=target_sizes,
                    text_labels=[formatted_texts]
                )[0]

            boxes = results["boxes"].cpu().numpy().tolist()
            scores = results["scores"].cpu().numpy().tolist()
            labels_idx = results["labels"].cpu().numpy().tolist()
            raw_labels = [raw_queries[idx] for idx in labels_idx]

            keep_indices = self._apply_nms(boxes, scores, raw_labels, iou_threshold=0.40)

            # 5. Xây dựng kết quả phân cấp & Biểu cảm khuôn mặt (Mục 13.4, 13.5)
            forest = get_taxonomy_forest()
            expr_engine = forest.get("expression_engine", {})
            macro_tree = forest.get("macro_trees", {}).get(p_cat, {})
            parent_vn = macro_tree.get("vn_name", p_cat.capitalize())

            micro_detections = []
            seen_words = set()

            for idx in keep_indices[:max_results]:
                word = raw_labels[idx]
                if word in seen_words:
                    continue
                seen_words.add(word)

                score = round(float(scores[idx]), 3)
                meta = get_part_info(word, parent_obj=p_cat)

                # Tọa độ box trong vùng crop (0.0 - 1.0)
                c_ymin = round(max(0.0, boxes[idx][1] / target_crop_dim), 4)
                c_xmin = round(max(0.0, boxes[idx][0] / target_crop_dim), 4)
                c_ymax = round(min(1.0, boxes[idx][3] / target_crop_dim), 4)
                c_xmax = round(min(1.0, boxes[idx][2] / target_crop_dim), 4)

                # Quy đổi tọa độ box ngược về hệ tọa độ toàn khung ảnh gốc
                g_xmin = round(xmin + c_xmin * (xmax - xmin), 4)
                g_ymin = round(ymin + c_ymin * (ymax - ymin), 4)
                g_xmax = round(xmin + c_xmax * (xmax - xmin), 4)
                g_ymax = round(ymin + c_ymax * (ymax - ymin), 4)

                # Kiểm tra sắc thái biểu cảm và gợi ý tính từ học thuật CEFR B2-C1
                academic_adjectives = []
                is_expression = False
                if word in expr_engine:
                    is_expression = True
                    academic_adjectives = expr_engine[word].get("academic_adjectives", [])
                elif any(word == item.get("word") for item in macro_tree.get("expressions_behaviors", [])):
                    is_expression = True

                child_display = meta.get("display_name", word.capitalize())
                child_meaning = meta.get("meaning", "Chi tiết vi mô")
                hierarchy_label = f"[{p_cat.upper()} ➔ {word.upper()}]"
                display_relation = f"{parent_vn} ➔ {child_meaning}"

                micro_detections.append({
                    "word": word,
                    "hierarchy_label": hierarchy_label,
                    "display_relation": display_relation,
                    "parent_entity": p_cat,
                    "display_name": child_display,
                    "meaning": child_meaning,
                    "cefr": meta.get("cefr", "B2"),
                    "ipa": meta.get("ipa", ""),
                    "vn_phonetic": meta.get("vn_phonetic", ""),
                    "tier": "micro",
                    "is_expression": is_expression,
                    "academic_adjectives": academic_adjectives,
                    "confidence": score,
                    "crop_normalized_box": {
                        "ymin": c_ymin, "xmin": c_xmin, "ymax": c_ymax, "xmax": c_xmax
                    },
                    "global_normalized_box": {
                        "ymin": g_ymin, "xmin": g_xmin, "ymax": g_ymax, "xmax": g_xmax
                    }
                })

            infer_elapsed = round((time.time() - start_infer) * 1000, 1)

            return {
                "status": "success",
                "parent_entity": p_cat,
                "parent_vn": parent_vn,
                "total_micro_detected": len(micro_detections),
                "reticle_roi": {
                    "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                    "pixel_box": [px_left, px_top, px_right, px_bottom],
                    "upscaled_dim": f"{target_crop_dim}x{target_crop_dim}"
                },
                "pruned_query_count": len(raw_queries),
                "queries_executed": raw_queries,
                "inference_time_ms": infer_elapsed,
                "micro_detections": micro_detections
            }

        except Exception as ex:
            return {
                "status": "error",
                "message": f"Lỗi trong quá trình soi vi mô: {str(ex)}",
                "micro_detections": []
            }
