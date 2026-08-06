# app/ml_models/generate_oxford.py
import os
import json
from wordfreq import top_n_list, zipf_frequency


def generate_oxford_5000():
    print("[*] Đang thu thập 5000 từ tiếng Anh phổ biến nhất...")

    # Lấy 5000 từ tiếng Anh cốt lõi
    top_words = top_n_list('en', 5000)

    vocab_dict = {}
    for word in top_words:
        # Bỏ qua các ký tự đơn lẻ, số, hoặc dấu câu
        if len(word) <= 1 or word.isnumeric():
            continue

        # Tính điểm Zipf Frequency
        zipf_score = zipf_frequency(word, 'en')

        # Phân loại CEFR nội suy từ độ phổ biến (Zipf)
        if zipf_score >= 6.0:
            level = "A1"
        elif zipf_score >= 5.0:
            level = "A2"
        elif zipf_score >= 4.0:
            level = "B1"
        elif zipf_score >= 3.0:
            level = "B2"
        else:
            level = "C1"

        vocab_dict[word] = level

    # Đường dẫn lưu file
    output_path = os.path.join(os.path.dirname(__file__), 'oxford_5000.json')

    # Ghi dữ liệu ra file JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_dict, f, indent=4, ensure_ascii=False)

    print(f"[+] Đã tạo thành công {len(vocab_dict)} từ vựng chuẩn CEFR.")
    print(f"[+] File được lưu tại: {output_path}")


if __name__ == "__main__":
    generate_oxford_5000()