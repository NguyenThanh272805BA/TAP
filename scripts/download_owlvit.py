import os
import sys

# Đảm bảo stdout UTF-8 trên Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import torch
from transformers import OwlViTProcessor, OwlViTForObjectDetection
from PIL import Image
import numpy as np

def main():
    print(">>> Đang kiểm tra và tải mô hình OWL-ViT Cục bộ (Local)...")
    model_id = "google/owlvit-base-patch32"
    
    save_dir = os.path.join(os.path.dirname(__file__), "..", "app", "ml_models", "saved_models", "owlvit")
    os.makedirs(save_dir, exist_ok=True)
    
    # 1. Tải Processor
    processor = OwlViTProcessor.from_pretrained(model_id)
    processor.save_pretrained(save_dir)
    print("[x] Đã lưu Processor vào:", save_dir)
    
    # 2. Tải Model
    model = OwlViTForObjectDetection.from_pretrained(model_id)
    model.eval()
    model.save_pretrained(save_dir)
    print("[x] Đã lưu Model Weights vào:", save_dir)
    
    # 3. Test thử suy luận với ảnh giả lập
    print(">>> Chạy thử nghiệm suy luận (Inference Test)...")
    dummy_img = Image.fromarray((np.random.rand(400, 400, 3) * 255).astype(np.uint8))
    texts = [["a backpack", "a zipper", "a strap"]]
    inputs = processor(text=texts, images=dummy_img, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        
    print("[x] Suy luận thành công! Shape logits:", outputs.logits.shape)
    print(">>> Hoàn tất khởi tạo mô hình OWL-ViT Local 100% Offline!")

if __name__ == "__main__":
    main()
