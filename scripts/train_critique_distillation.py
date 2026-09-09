import os
import sys
import json
from typing import List, Dict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.critique_synthesizer import get_critique_synthesizer


def generate_distillation_corpus(output_path: str = "app/ml_models/critique_distillation_data.jsonl") -> int:
    """
    Tự động biên dịch bộ dữ liệu huấn luyện chưng cất tri thức (Knowledge Distillation):
    Tạo ra các cặp (sentence, target_correction, error_type, cefr_level, critique_feedback)
    để phục vụ huấn luyện mô hình ngôn ngữ cục bộ gọn nhẹ (Local Small LM / T5-Small).
    """
    print("=" * 70)
    print("   KHỞI ĐỘNG TIẾN TRÌNH TỔNG HỢP DATASET HUẤN LUYỆN AI LOCAL (DISTILLATION)")
    print("=" * 70)

    # Tập mẫu câu đa dạng bao gồm câu chuẩn, các nhóm lỗi ngữ pháp điển hình và từ vựng CEFR
    training_seeds = [
        # Nhóm 1: Hòa hợp Chủ vị (Subject-Verb Agreement)
        ("She do not likes apples.", "She does not like apples.", "S-V Agreement", "A2"),
        ("He have two cars and a bicycle.", "He has two cars and a bicycle.", "S-V Agreement", "A1"),
        ("The list of items are on the desk.", "The list of items is on the desk.", "S-V Agreement", "B1"),
        ("Everybody want to achieve great success.", "Everybody wants to achieve great success.", "S-V Agreement", "B2"),

        # Nhóm 2: Thì động từ (Verb Tense & Auxiliary)
        ("Yesterday I go to the supermarket with my sister.", "Yesterday I went to the supermarket with my sister.", "Past Tense", "A2"),
        ("I have saw that movie three times already.", "I have seen that movie three times already.", "Present Perfect", "B1"),
        ("She was sleeping when the earthquake happens.", "She was sleeping when the earthquake happened.", "Past Continuous", "B1"),

        # Nhóm 3: Mạo từ & Giới từ (Articles & Prepositions)
        ("He is an honest person with big dream.", "He is an honest person with a big dream.", "Articles", "B1"),
        ("I am interested on artificial intelligence.", "I am interested in artificial intelligence.", "Prepositions", "B2"),
        ("She arrived to London early in the morning.", "She arrived in London early in the morning.", "Prepositions", "B1"),

        # Nhóm 4: Từ vựng học thuật & Thành ngữ chuẩn (CEFR C1/C2)
        ("Ubiquitous computing facilitates seamless communication across networks.", "Ubiquitous computing facilitates seamless communication across networks.", "Academic Standard", "C1"),
        ("The government should take into account environmental factors.", "The government should take into account environmental factors.", "Collocation & Idiom", "B2"),
        ("He made a significant breakthrough in quantum algorithms.", "He made a significant breakthrough in quantum algorithms.", "Academic Standard", "C1"),

        # Nhóm 5: Câu hoàn hảo (Perfect baseline)
        ("I usually drink coffee before starting my daily coding tasks.", "I usually drink coffee before starting my daily coding tasks.", "Baseline Correct", "A2"),
        ("She loves reading classical literature in the evening.", "She loves reading classical literature in the evening.", "Baseline Correct", "B1")
    ]

    gec = LocalGECEngine()
    synthesizer = get_critique_synthesizer()

    records = []
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[*] Đang xử lý và gán nhãn tri thức cho {len(training_seeds)} mẫu huấn luyện...")

    for sentence, target_corr, err_category, target_cefr in training_seeds:
        gec_res = gec.evaluate(sentence)
        critique = synthesizer.synthesize(sentence, gec_res)

        record = {
            "input_text": sentence,
            "target_correction": target_corr,
            "error_category": err_category,
            "cefr_level": target_cefr,
            "score": gec_res["score"],
            "error_count": gec_res["error_count"],
            "master_g_critique": critique,
            "needs_llm_escalation": gec_res["needs_llm_escalation"]
        }
        records.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[+] Đã xuất thành công {len(records)} mẫu dữ liệu chưng cất vào: {output_path}")
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"[+] Kích thước file dữ liệu: {file_size_kb:.2f} KB (Rất gọn nhẹ, an toàn đẩy git)")
    print("=" * 70)
    return len(records)


if __name__ == "__main__":
    generate_distillation_corpus()
