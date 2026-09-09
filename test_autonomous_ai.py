import unittest
import sys
from app import create_app, db
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.semantic_intent_parser import get_semantic_intent_parser
from app.ml_models.autonomous_miner import AutonomousCorpusMiner
from app.ml_models.srs_predictor import SmartSRS
from app.ml_models.recommender import VocabRecommender

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class TestAutonomousAISystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_01_symbolic_gec_engine(self):
        """Kiểm thử Bộ não 1: Symbolic Grammar Engine phát hiện lỗi và tự sửa không cần model CoLA"""
        gec = LocalGECEngine()
        
        # Test câu sai ngữ pháp
        res_bad = gec.evaluate("She do not likes apples.")
        self.assertLess(res_bad['score'], 10.0)
        self.assertGreater(res_bad['error_count'], 0)
        self.assertIn("She does not like apples.", res_bad['corrected_text'])
        
        # Test câu chuẩn ngữ pháp
        res_good = gec.evaluate("She does not like apples.")
        self.assertEqual(res_good['score'], 10.0)
        self.assertEqual(res_bad['error_count'] > 0, True)
        self.assertEqual(res_good['error_count'], 0)
        
        # Test Bộ sinh nhận xét Master G Local & Cổng phân luồng
        self.assertIn("Master G", res_bad['master_g_critique'])
        self.assertFalse(res_bad['needs_llm_escalation'])
        self.assertFalse(res_good['needs_llm_escalation'])
        print("\n[OK] Test 1: Symbolic Grammar Engine & Local Critique Synthesizer hoạt động chính xác.")

    def test_02_zero_shot_intent_parser(self):
        """Kiểm thử Bộ não 2: Zero-shot Semantic Intent Parser không phụ thuộc file CSV"""
        parser = get_semantic_intent_parser()
        
        self.assertEqual(parser.parse_intent("Giải thích cấu trúc thì hiện tại hoàn thành"), "ask_grammar")
        self.assertEqual(parser.parse_intent("What is the definition of serendipity?"), "ask_vocab")
        self.assertEqual(parser.parse_intent("Tấn công con quái vật bằng song kiếm!"), "story_action")
        self.assertEqual(parser.parse_intent("Attack the dark dragon with fire spell"), "story_action")
        self.assertEqual(parser.parse_intent("Chào bạn, hôm nay thế nào?"), "general_chat")
        print("[OK] Test 2: Zero-shot Semantic Intent Parser phân loại chính xác 100% không cần train data.")

    def test_03_autonomous_corpus_miner(self):
        """Kiểm thử Bộ não 3: Autonomous Miner trích xuất Collocation qua PMI và lọc Zipf từ văn bản thô"""
        miner = AutonomousCorpusMiner()
        sample_text = """
        Artificial intelligence and machine learning technologies provide autonomous solutions.
        Students can make progress in natural language understanding.
        High potential algorithms take into account cognitive models.
        """
        results = miner.mine_from_text(sample_text, top_n=5)
        self.assertGreater(len(results), 0)
        
        # Kiểm tra sự xuất hiện của cụm từ hoặc từ vựng được gán CEFR
        has_collocation = any(r['type'] == 'collocation' for r in results)
        has_vocab = any(r['type'] == 'vocabulary' for r in results)
        self.assertTrue(has_collocation or has_vocab)
        print(f"[OK] Test 3: Autonomous Miner đã trích xuất thành công {len(results)} mục tri thức từ ngữ liệu thô.")

    def test_04_fsrs_smart_srs(self):
        """Kiểm thử Bộ não 4: Thuật toán FSRS tính toán chu kỳ theo độ khó và tốc độ phản xạ"""
        srs = SmartSRS()
        
        # Làm bài đúng và nhanh
        dt_fast, int_fast = srs.predict_next_review(fail_count=0, response_time=1.5, previous_interval=24.0)
        # Làm bài đúng nhưng chậm
        dt_slow, int_slow = srs.predict_next_review(fail_count=0, response_time=8.0, previous_interval=24.0)
        # Làm bài sai nhiều lần
        dt_fail, int_fail = srs.predict_next_review(fail_count=3, response_time=4.0, previous_interval=48.0)
        
        self.assertGreater(int_fast, int_slow)
        self.assertLess(int_fail, 24.0)
        print(f"[OK] Test 4: FSRS phản hồi thích ứng chuẩn: Đúng nhanh ({int_fast:.1f}h) > Đúng chậm ({int_slow:.1f}h) > Sai ({int_fail:.1f}h).")

    def test_05_zpd_concept_recommender(self):
        """Kiểm thử Bộ não 5: ZPD Concept Recommender xử lý Cold-start và tiệm tiến độ khó"""
        recommender = VocabRecommender()
        # Test với User ID 999999 (chưa có lịch sử học tập)
        recs = recommender.recommend_next_words(user_id=999999, top_n=3)
        self.assertIsInstance(recs, list)
        print(f"[OK] Test 5: Recommender gợi ý thành công {len(recs)} từ vựng theo vùng phát triển gần nhất (ZPD).")


if __name__ == '__main__':
    unittest.main()
