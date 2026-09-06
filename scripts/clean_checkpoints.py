import os
import shutil
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_training_checkpoints(model_dir="app/ml_models/saved_models/gec_transformer"):
    """
    Dọn dẹp các thư mục checkpoint huấn luyện trung gian để giải phóng dung lượng đĩa (>2.3 GB),
    đồng thời bảo toàn 100% các tệp trọng số mô hình cuối cùng (model.safetensors, tokenizer, config).
    """
    base_path = os.path.abspath(model_dir)
    print(f"[*] Đang kiểm tra thư mục: {base_path}")

    if not os.path.exists(base_path):
        print(f"[!] Không tìm thấy thư mục: {base_path}")
        return

    # Danh sách các tệp cốt lõi bắt buộc phải giữ lại
    essential_files = ["model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt", "special_tokens_map.json"]

    total_freed_bytes = 0
    deleted_items = []

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        # Nếu là thư mục checkpoint trung gian
        if os.path.isdir(item_path) and item.startswith("checkpoint-"):
            dir_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(item_path) for f in fn)
            try:
                shutil.rmtree(item_path)
                total_freed_bytes += dir_size
                deleted_items.append((item, dir_size / (1024 * 1024)))
                print(f"[+] Đã xóa thư mục rác: {item} ({dir_size / (1024 * 1024):.2f} MB)")
            except Exception as e:
                print(f"[-] Lỗi khi xóa {item}: {e}")

    print("\n" + "="*50)
    print(f"[KẾT QUẢ DỌN DẸP]")
    print(f"Đã dọn dẹp thành công {len(deleted_items)} thư mục checkpoint.")
    print(f"Tổng dung lượng giải phóng: {total_freed_bytes / (1024 * 1024):.2f} MB (~{total_freed_bytes / (1024 * 1024 * 1024):.2f} GB)")
    print("="*50 + "\n")

    # Kiểm tra lại các file cốt lõi còn nguyên vẹn
    print("[*] Kiểm tra các tệp trọng số production còn lại:")
    for f in os.listdir(base_path):
        fp = os.path.join(base_path, f)
        if os.path.isfile(fp):
            print(f" - {f}: {os.path.getsize(fp) / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    clean_training_checkpoints()
