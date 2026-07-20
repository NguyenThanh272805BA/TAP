import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app import db


class VocabRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def recommend_next_words(self, user_id, top_n=5):
        all_vocabs = Vocabulary.query.all()
        if not all_vocabs:
            return []

        # Nội dung dùng để phân tích: Kết hợp Theme và Nghĩa
        df = pd.DataFrame([{
            'id': v.id,
            'word': v.word,
            'features': f"{v.theme} {v.meaning}"
        } for v in all_vocabs])

        learned_vocabs = db.session.query(UserVocabulary.vocab_id).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.memorization_level == 'DA_THUOC'
        ).all()
        learned_ids = [v[0] for v in learned_vocabs]

        # Xử lý Cold-start (Chưa học từ nào)
        if not learned_ids:
            samples = df.sample(n=min(top_n, len(df)))
            return [{'vocab_id': int(row['id']), 'word': row['word'], 'score': 0.0} for _, row in samples.iterrows()]

        tfidf_matrix = self.vectorizer.fit_transform(df['features'])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

        unlearned_indices = df[~df['id'].isin(learned_ids)].index
        learned_indices = df[df['id'].isin(learned_ids)].index

        recommendations = []
        for idx in unlearned_indices:
            sim_scores = [cosine_sim[idx][l_idx] for l_idx in learned_indices]
            avg_score = sum(sim_scores) / len(sim_scores) if sim_scores else 0
            recommendations.append({
                'vocab_id': int(df.iloc[idx]['id']),
                'word': df.iloc[idx]['word'],
                'score': float(avg_score)
            })

        # Top gợi ý có độ tương đồng cao nhất
        recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:top_n]
        return recommendations