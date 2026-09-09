import re
import math
import sys
from collections import Counter
from typing import List, Dict, Tuple, Optional
from wordfreq import zipf_frequency

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.ml_models.vocab_classifier import VocabCEFRClassifier


class AutonomousCorpusMiner:
    """
    Máy Khai Phá Tri Thức Ngữ Liệu Tự Động (Autonomous Corpus & Collocation Miner)
    Thuật toán tự động trích xuất từ vựng, cụm từ cố định (Collocations) từ văn bản tiếng Anh thô
    dựa trên Định luật Zipf và Độ đo Thông tin Tương hỗ (Pointwise Mutual Information - PMI).
    Hoàn toàn độc lập với việc gán nhãn thủ công hoặc phụ thuộc vào API sinh nội dung bên ngoài.
    """

    def __init__(self):
        self.cefr_classifier = VocabCEFRClassifier()
        self.stopwords = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on',
            'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we',
            'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make',
            'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only',
            'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work',
            'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }

        # Bảng ánh xạ chủ đề heuristic từ vựng
        self.theme_anchors = {
            'Technology': {'computer', 'algorithm', 'data', 'system', 'software', 'network', 'cyber', 'digital', 'tech', 'device', 'artificial', 'intelligence'},
            'Science': {'energy', 'climate', 'planet', 'chemical', 'biology', 'gravity', 'physics', 'quantum', 'experiment', 'cell', 'particle'},
            'Business': {'market', 'economy', 'finance', 'company', 'industry', 'investor', 'profit', 'trade', 'corporate', 'revenue', 'management'},
            'Health': {'health', 'disease', 'patient', 'medical', 'hospital', 'doctor', 'virus', 'treatment', 'drug', 'medicine', 'clinic'},
            'Gaming & RPG': {'sword', 'magic', 'shield', 'dragon', 'dungeon', 'warrior', 'spell', 'quest', 'battle', 'armor', 'hero', 'guild'}
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tách từ và chuẩn hóa."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return words

    def calculate_pmi(self, words: List[str], min_count: int = 2) -> List[Dict]:
        """
        Tính toán Pointwise Mutual Information (PMI) cho các cặp từ liền kề (Bigrams):
        PMI(w1, w2) = log2( P(w1, w2) / (P(w1) * P(w2)) )
        Giúp phát hiện tự động các cụm từ vựng/thành ngữ đi liền nhau tự nhiên.
        """
        if len(words) < 2:
            return []

        word_counts = Counter(words)
        total_words = len(words)
        bigrams = list(zip(words[:-1], words[1:]))
        bigram_counts = Counter(bigrams)
        total_bigrams = len(bigrams)

        collocations = []
        for (w1, w2), count in bigram_counts.items():
            if count < min_count:
                continue
            # Bỏ qua nếu cả 2 từ đều là stopwords
            if w1 in self.stopwords and w2 in self.stopwords:
                continue

            # Xác suất đồng xuất hiện
            p_w1_w2 = count / total_bigrams
            p_w1 = word_counts[w1] / total_words
            p_w2 = word_counts[w2] / total_words

            # Công thức PMI
            pmi = math.log2(p_w1_w2 / (p_w1 * p_w2))
            
            # Chỉ lấy các cụm từ có sự liên kết ngữ nghĩa mạnh (PMI > 2.0)
            if pmi >= 2.0:
                collocations.append({
                    "phrase": f"{w1} {w2}",
                    "pmi": round(pmi, 2),
                    "frequency": count
                })

        collocations.sort(key=lambda x: (x["pmi"], x["frequency"]), reverse=True)
        return collocations

    def infer_theme(self, text: str) -> str:
        """Thuật toán suy diễn chủ đề của văn bản dựa trên khoảng cách từ vựng neo."""
        tokens = set(self._tokenize(text))
        best_theme = "General"
        max_overlap = 0

        for theme, anchors in self.theme_anchors.items():
            overlap = len(tokens.intersection(anchors))
            if overlap > max_overlap:
                max_overlap = overlap
                best_theme = theme

        return best_theme

    def mine_from_text(self, text: str, min_zipf: float = 2.5, max_zipf: float = 5.5, top_n: int = 15) -> List[Dict]:
        """
        Khai phá toàn bộ từ vựng mục tiêu và cụm từ từ văn bản thô:
        1. Lọc từ đơn học thuật mục tiêu theo thang Zipf (B1 -> C1)
        2. Bóc tách cụm từ cố định (Collocations) bằng PMI
        3. Phân cấp độ CEFR tự động
        4. Gán chủ đề ngữ cảnh
        """
        if not text or len(text.strip()) == 0:
            return []

        words = self._tokenize(text)
        detected_theme = self.infer_theme(text)
        word_freq = Counter(words)

        mined_items = []
        seen_words = set()

        # 1. Trích xuất Cụm từ hay (Collocations qua PMI)
        collocations = self.calculate_pmi(words, min_count=1)
        for col in collocations[:5]:
            phrase = col["phrase"]
            seen_words.update(phrase.split())
            mined_items.append({
                "word": phrase,
                "type": "collocation",
                "cefr_level": "B2",
                "theme": detected_theme,
                "score_metric": f"PMI={col['pmi']}",
                "meaning": f"Cụm từ cố định chủ đề {detected_theme}"
            })

        # 2. Trích xuất Từ vựng đơn lẻ trong dải học thuật (Zipf filter)
        for word, count in word_freq.most_common():
            if word in self.stopwords or word in seen_words:
                continue

            z_score = zipf_frequency(word, 'en')
            # Lọc từ: loại bỏ từ quá dễ (Zipf > 5.5) và từ hiếm/rác (Zipf < 2.5)
            if min_zipf <= z_score <= max_zipf:
                cefr = self.cefr_classifier.predict_cefr(word)
                mined_items.append({
                    "word": word,
                    "type": "vocabulary",
                    "cefr_level": cefr,
                    "theme": detected_theme,
                    "score_metric": f"Zipf={z_score:.2f}",
                    "meaning": f"Từ vựng cấp độ {cefr} ({detected_theme})"
                })
                seen_words.add(word)

            if len(mined_items) >= top_n:
                break

        return mined_items

    def save_to_database(self, mined_items: List[Dict], app, db) -> int:
        """Lưu trữ an toàn các từ vựng mới khai phá vào MySQL, bỏ qua từ đã tồn tại."""
        from app.models.vocabulary import Vocabulary
        added_count = 0
        with app.app_context():
            for item in mined_items:
                existing = Vocabulary.query.filter_by(word=item["word"]).first()
                if not existing:
                    new_vocab = Vocabulary(
                        word=item["word"],
                        meaning=item["meaning"],
                        theme=item["theme"],
                        cefr_level=item["cefr_level"],
                        image_url="default.png",
                        is_unlocked=False,
                        is_memorized=False
                    )
                    db.session.add(new_vocab)
                    added_count += 1
            if added_count > 0:
                db.session.commit()
                print(f"[AUTONOMOUS MINER] Đã tự động nạp thành công {added_count} mục tri thức mới vào Database!")
        return added_count


if __name__ == "__main__":
    miner = AutonomousCorpusMiner()
    sample_article = """
    Artificial intelligence and machine learning have made significant progress in natural language processing.
    Deep neural networks take into account vast amounts of contextual information to generate coherent responses.
    However, algorithmic autonomous systems must be developed to reduce reliance on massive labeled datasets.
    Researchers are investigating cyber security, quantum computing, and ethical principles to ensure robust software systems.
    """

    print("=== KIỂM THỬ KHAI PHÁ NGỮ LIỆU TỰ ĐỘNG (PMI + ZIPF) ===")
    results = miner.mine_from_text(sample_article, top_n=10)
    for r in results:
        print(f"[{r['type'].upper():12}] {r['word']:25} -> Cấp độ: {r['cefr_level']:4} | Chủ đề: {r['theme']:12} | Chỉ số: {r['score_metric']}")
