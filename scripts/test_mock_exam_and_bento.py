import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.grammar import Grammar
from app.models.user_grammar import UserGrammar
from app.models.test import TestLog
from app.ml_models.exam_engine import LocalExamEngine

class TestMockExamAndBentoHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Tạo hoặc lấy test user
        cls.user = User.query.filter_by(username='test_exam_user').first()
        if not cls.user:
            cls.user = User(
                username='test_exam_user',
                password_hash='dummy_hash',
                current_band='A1',
                target_band='B2',
                current_level='Tân Binh Ngơ Ngác'
            )
            db.session.add(cls.user)
            db.session.commit()
        cls.user_id = cls.user.id

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test_01_vocabularies_overview_bento(self):
        """Kiểm tra API /api/game/vocabularies/overview trả về danh mục chủ đề chuẩn Bento Grid"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

        res = self.client.get('/api/game/vocabularies/overview')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('topics', data)
        topics = data['topics']
        self.assertGreater(len(topics), 0, "Phải có ít nhất 1 chủ đề từ vựng trong hệ thống.")

        sample = topics[0]
        self.assertIn('theme', sample)
        self.assertIn('total_words', sample)
        self.assertIn('memorized_words', sample)
        self.assertIn('progress_percent', sample)
        self.assertIn('representative_cefr', sample)
        self.assertIn('sample_words', sample)
        print(f"[✓] test_01_vocabularies_overview_bento passed! ({len(topics)} topics loaded).")

    def test_02_personalized_grammar_cefr(self):
        """Kiểm tra API /api/game/grammar/personalized phân nhóm CEFR A1-C2 và gắn nhãn cá nhân"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

        res = self.client.get('/api/game/grammar/personalized')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('user_band', data)
        self.assertIn('mastery_stats', data)
        self.assertIn('grammars_by_band', data)

        bands = data['grammars_by_band']
        for b in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            self.assertIn(b, bands)
            self.assertGreater(len(bands[b]), 0, f"Band {b} phải có ít nhất 1 cấu trúc ngữ pháp.")

        # Kiểm tra nhãn is_recommended cho user band A1
        a1_items = bands['A1']
        self.assertTrue(all(item['is_recommended'] for item in a1_items), "Tất cả ngữ pháp Band A1 phải được gắn nhãn recommended cho user A1.")
        print("[✓] test_02_personalized_grammar_cefr passed! (Tất cả 6 Band CEFR đầy đủ).")

    def test_03_toggle_grammar_mastery(self):
        """Kiểm tra cập nhật trạng thái làm chủ ngữ pháp UserGrammar"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

        g = Grammar.query.first()
        self.assertIsNotNone(g)

        # Toggle sang DANG_LUYEN
        res = self.client.post('/api/game/grammar/toggle_mastery', json={
            'grammar_id': g.id,
            'status': 'DANG_LUYEN'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['mastery_status'], 'DANG_LUYEN')

        # Toggle tiếp sang DA_NAM_VUNG
        res2 = self.client.post('/api/game/grammar/toggle_mastery', json={
            'grammar_id': g.id,
            'status': 'DA_NAM_VUNG'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()['mastery_status'], 'DA_NAM_VUNG')
        print("[✓] test_03_toggle_grammar_mastery passed!")

    def test_04_generate_and_submit_mock_exam(self):
        """Kiểm tra sinh đề thi thử tự động 100% Local và chấm thi toàn diện"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

        # 1. Sinh đề thi thử A1 (5 câu)
        res_gen = self.client.post('/api/game/exam/mock/generate', json={
            'band': 'A1',
            'num_questions': 5
        })
        self.assertEqual(res_gen.status_code, 200)
        exam = res_gen.get_json()
        self.assertEqual(exam['status'], 'success')
        self.assertEqual(len(exam['questions']), 5)
        self.assertNotIn('answer_key', exam, "Không được để lộ answer_key cho client.")

        # 2. Nộp bài thi thử
        answers = {}
        for q in exam['questions']:
            if q['type'] == 'writing_challenge':
                answers[str(q['id'])] = "I love learning English every day."
            elif q['options']:
                answers[str(q['id'])] = q['options'][0]
            else:
                answers[str(q['id'])] = "test"

        initial_coins = self.user.coins or 0
        res_sub = self.client.post('/api/game/exam/mock/submit', json={
            'answers': answers,
            'exam_id': exam['exam_id']
        })
        self.assertEqual(res_sub.status_code, 200)
        report = res_sub.get_json()

        self.assertEqual(report['status'], 'success')
        self.assertIn('final_score', report)
        self.assertIn('estimated_band', report)
        self.assertIn('subscores', report)
        self.assertIn('coins_reward', report)
        self.assertIn('diagnostic_advice', report)
        self.assertGreater(report['coins_reward'], 0)

        # Xác nhận điểm thưởng được cộng vào user
        db.session.refresh(self.user)
        self.assertGreater(self.user.coins, initial_coins)
        print(f"[✓] test_04_generate_and_submit_mock_exam passed! Score: {report['final_score']}, Band: {report['estimated_band']}, Reward: +{report['coins_reward']} xu.")

    def test_05_exam_history(self):
        """Kiểm tra xem lại lịch sử các bài thi thử từ TestLog"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

        res = self.client.get('/api/game/exam/history')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('history', data)
        self.assertGreater(len(data['history']), 0)
        print(f"[✓] test_05_exam_history passed! ({len(data['history'])} logs recorded).")


if __name__ == '__main__':
    unittest.main()
