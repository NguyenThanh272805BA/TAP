import sys
import numpy as np
import pandas as pd
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app import db

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class VocabRecommender:
    """
    Bộ não 5: Hệ Gợi Ý Dựa Trên Đồ Thị Khái Niệm & Vùng Phát Triển Gần Nhất (ZPD Ontology Recommender)
    Kết hợp quan hệ chủ đề (Theme Graph), độ khó tiệm tiến theo chuẩn CEFR (Zone of Proximal Development)
    và tương đồng ngữ nghĩa. Hoàn toàn không cần tập dữ liệu hành vi người dùng khổng lồ.
    """

    CEFR_MAP = {
        'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def _get_cefr_level_val(self, cefr_str: str) -> int:
        return self.CEFR_MAP.get(str(cefr_str).upper(), 1)

    def recommend_next_words(self, user_id: int, top_n: int = 5) -> List[Dict]:
        all_vocabs = Vocabulary.query.all()
        if not all_vocabs:
            return []

        # 1. Truy vấn danh sách từ người dùng đã thuộc
        learned_vocabs = db.session.query(
            UserVocabulary.vocab_id
        ).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.memorization_level == 'DA_THUOC'
        ).all()
        learned_ids = set([v[0] for v in learned_vocabs])

        # 2. Xử lý Cold-Start: Người dùng chưa thuộc từ nào
        # Thuật toán ZPD: Gợi ý các từ vựng nền tảng A1/A2 có tính ứng dụng cao nhất
        if not learned_ids:
            foundational_vocabs = [v for v in all_vocabs if self._get_cefr_level_val(v.cefr_level) <= 2]
            if not foundational_vocabs:
                foundational_vocabs = all_vocabs
            
            selected = foundational_vocabs[:top_n]
            return [
                {
                    'vocab_id': int(v.id),
                    'word': v.word,
                    'cefr_level': v.cefr_level or 'A1',
                    'theme': v.theme or 'General',
                    'score': 1.0,
                    'reason': 'Từ vựng nền tảng khởi đầu (Cold-start ZPD)'
                }
                for v in selected
            ]

        # 3. Phân tích hồ sơ năng lực học viên (User Learning Profile)
        learned_objs = [v for v in all_vocabs if v.id in learned_ids]
        learned_themes = [v.theme for v in learned_objs if v.theme]
        learned_levels = [self._get_cefr_level_val(v.cefr_level) for v in learned_objs]

        # Trình độ CEFR trung bình của học viên hiện tại
        avg_level = float(np.mean(learned_levels)) if learned_levels else 1.0
        # Mục tiêu tiệm tiến tiếp theo (Vygotsky ZPD: Học từ ở mức hiện tại + 1 bậc)
        target_level = min(6.0, avg_level + 0.8)

        # Đếm tần suất chủ đề học viên quan tâm
        theme_counts = {}
        for t in learned_themes:
            theme_counts[t] = theme_counts.get(t, 0) + 1
        top_user_themes = set(sorted(theme_counts, key=theme_counts.get, reverse=True)[:3])

        # 4. Tính ma trận tương đồng ngữ nghĩa TF-IDF cho văn bản mô tả
        df = pd.DataFrame([{
            'id': v.id,
            'word': v.word,
            'theme': v.theme or 'General',
            'cefr': v.cefr_level or 'A1',
            'features': f"{v.theme or ''} {v.word} {v.meaning or ''}"
        } for v in all_vocabs])

        try:
            tfidf_matrix = self.vectorizer.fit_transform(df['features'])
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        except Exception:
            cosine_sim = None

        id_to_idx = {row['id']: idx for idx, row in df.iterrows()}
        learned_indices = [id_to_idx[lid] for lid in learned_ids if lid in id_to_idx]

        candidates = []
        for v in all_vocabs:
            if v.id in learned_ids:
                continue

            v_level = self._get_cefr_level_val(v.cefr_level)
            v_theme = v.theme or 'General'

            # 4.1. Điểm tiệm tiến độ khó CEFR (ZPD Proximity Score):
            # Càng gần target_level thì điểm càng tiệm cận 1.0
            level_diff = abs(v_level - target_level)
            cefr_score = np.exp(-0.6 * level_diff)

            # 4.2. Điểm tương đồng chủ đề (Theme Graph Affinity):
            theme_score = 1.0 if v_theme in top_user_themes else 0.35

            # 4.3. Điểm tương đồng ngữ nghĩa hình học (Cosine Semantic Score):
            if cosine_sim is not None and learned_indices and v.id in id_to_idx:
                v_idx = id_to_idx[v.id]
                semantic_score = float(np.mean([cosine_sim[v_idx][l_idx] for l_idx in learned_indices]))
            else:
                semantic_score = 0.2

            # 4.4. Điểm tổng hợp trọng số thuật toán (Composite Pedagogical Score)
            # 40% ZPD CEFR + 35% Chủ đề + 25% Ngữ nghĩa
            total_score = (0.40 * cefr_score) + (0.35 * theme_score) + (0.25 * semantic_score)

            candidates.append({
                'vocab_id': int(v.id),
                'word': v.word,
                'cefr_level': v.cefr_level or 'A1',
                'theme': v_theme,
                'score': float(round(total_score, 4)),
                'reason': f"Khớp chủ đề '{v_theme}' & Trình độ tiệm tiến {v.cefr_level or 'A1'}"
            })

        # Sắp xếp theo điểm số thuật toán cao nhất
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:top_n]