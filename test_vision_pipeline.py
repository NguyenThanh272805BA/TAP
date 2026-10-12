import os
import sys
import json
import base64
import io
import numpy as np
from PIL import Image, ImageDraw

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("TEST TOÀN TRÌNH PHÂN HỆ THỊ GIÁC MÁY TÍNH & GỬI NHẬN DIỆN CỤC BỘ")
print("=" * 70)

# 1. Khởi tạo ảnh giả lập một chiếc Balo có khóa kéo và quai đeo
img = Image.new("RGB", (640, 480), color=(220, 220, 220))
draw = ImageDraw.Draw(img)

# Vẽ thân balo (khối chữ nhật lớn màu xanh tím)
draw.rectangle([160, 80, 480, 420], fill=(40, 50, 100), outline=(20, 30, 70), width=4)

# Vẽ quai đeo (hai dải màu đen)
draw.rectangle([180, 100, 220, 380], fill=(20, 20, 20))
draw.rectangle([420, 100, 460, 380], fill=(20, 20, 20))

# Vẽ khóa kéo ở giữa (đường màu bạc)
draw.line([(320, 120), (320, 360)], fill=(200, 200, 200), width=6)
draw.rectangle([310, 200, 330, 230], fill=(240, 240, 0)) # con trượt khóa

buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

print("[1] Đã tạo ảnh mẫu giả lập (640x480). Kích thước Base64:", len(img_b64))

# 2. Khởi tạo LocalOwlVitEngine
from app.ml_models.owl_vit_engine import LocalOwlVitEngine

engine = LocalOwlVitEngine(lazy=False)
assert engine.is_loaded, "OwlViT Engine phải nạp thành công!"
print("[2] Local OWL-ViT Engine đã nạp xong từ saved_models/owlvit!")

# 3. Chạy phát hiện bộ phận
res = engine.detect_parts(
    image_input=img_b64,
    target_category="backpack",
    score_threshold=0.10,
    max_results=6
)

print(f"[3] Kết quả phát hiện:")
print(f"    - Trạng thái: {res.get('status')}")
print(f"    - Thời gian suy luận: {res.get('inference_time_ms')} ms")
print(f"    - Vật thể chính: {res.get('primary_object')}")
print(f"    - Số bộ phận tìm thấy: {len(res.get('detected_parts', []))}")

for p in res.get("detected_parts", []):
    print(f"      + [{p['cefr']}] {p['word']} ({p['meaning']}) - IPA: {p['ipa']} - Tin cậy: {p['confidence']}")

# 4. Kiểm tra tích hợp Flask App và các Endpoint
from app import create_app
app = create_app()

with app.test_client() as client:
    print("\n[4] Kiểm tra API Endpoints:")
    
    # 4.1 Test GET /vision-arena
    r_arena = client.get('/vision-arena')
    assert r_arena.status_code == 200, f"GET /vision-arena lỗi {r_arena.status_code}"
    print("    [✓] GET /vision-arena: 200 OK (Giao diện tải hoàn tất)")

    # 4.2 Test POST /api/vision/scan
    r_scan = client.post('/api/vision/scan', json={
        "image": f"data:image/jpeg;base64,{img_b64}",
        "target_category": "backpack",
        "threshold": 0.10
    })
    assert r_scan.status_code == 200, f"POST /api/vision/scan lỗi {r_scan.status_code}"
    scan_data = r_scan.get_json()
    print(f"    [✓] POST /api/vision/scan: 200 OK (Trả về {scan_data.get('total_detected')} chi tiết)")

    # 4.3 Test POST /api/vision/submit-sentence
    r_submit = client.post('/api/vision/submit-sentence', json={
        "sentence": "The zipper of my backpack is broken.",
        "words_used": ["zipper", "backpack"],
        "primary_object": "backpack"
    })
    assert r_submit.status_code == 200, f"POST /api/vision/submit-sentence lỗi {r_submit.status_code}"
    sub_data = r_submit.get_json()
    print(f"    [✓] POST /api/vision/submit-sentence: 200 OK")
    print(f"        - Điểm số: {sub_data.get('score')}/100")
    print(f"        - Câu sửa lỗi (GEC): '{sub_data.get('corrected_sentence')}'")
    print(f"        - Lời phê Master G: '{sub_data.get('feedback')}'")
    print(f"        - Thưởng EXP: +{sub_data.get('exp_awarded')} EXP")

print("\n" + "=" * 70)
print(">>> TẤT CẢ CÁC BÀI KIỂM THỬ PHÂN HỆ THỊ GIÁC ĐỀU VƯỢT QUA 100%!")
print("=" * 70)
