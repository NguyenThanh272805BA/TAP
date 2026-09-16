import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.models.roadmap import RoadmapMilestone, UserMilestoneProgress
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.ml_models.scramble_engine import LocalScrambleEngine
from werkzeug.security import generate_password_hash


class TestNewFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            # Tạo user test nếu chưa có
            user = User.query.filter_by(username='test_learner_hero').first()
            if not user:
                user = User(
                    username='test_learner_hero',
                    password_hash=generate_password_hash('password123'),
                    role='user',
                    coins=1000,
                    target_band='B2',
                    current_band='A1'
                )
                db.session.add(user)
                db.session.commit()
            cls.user_id = user.id

    def setUp(self):
        # Thiết lập session cho test client
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user_id

    def test_01_local_scramble_engine_word(self):
        """Kiểm tra Bộ não Local Scramble Engine (Từ vựng)"""
        with self.app.app_context():
            engine = LocalScrambleEngine()
            puzzle = engine.generate_word_scramble()
            self.assertEqual(puzzle['status'], 'success')
            self.assertTrue('target_word' in puzzle)
            self.assertTrue(len(puzzle['shuffled_letters']) > 0)

            # Test xác thực đúng
            verify_correct = engine.verify_word_scramble(
                puzzle['vocab_id'],
                puzzle['target_word'],
                response_time_sec=2.5,
                user_id=self.user_id
            )
            self.assertTrue(verify_correct['is_correct'])
            self.assertEqual(verify_correct['score'], 10.0)

            # Test xác thực sai
            verify_wrong = engine.verify_word_scramble(
                puzzle['vocab_id'],
                "XYZWRONG",
                response_time_sec=6.0,
                user_id=self.user_id
            )
            self.assertFalse(verify_wrong['is_correct'])
            self.assertEqual(verify_wrong['score'], 0.0)
            print("[✓] test_01_local_scramble_engine_word passed!")

    def test_02_local_scramble_engine_syntax(self):
        """Kiểm tra Bộ não Local Syntax Assembly (Cú pháp câu)"""
        with self.app.app_context():
            engine = LocalScrambleEngine()
            syntax_puzzle = engine.generate_syntax_scramble()
            self.assertEqual(syntax_puzzle['status'], 'success')
            self.assertTrue(len(syntax_puzzle['shuffled_chunks']) > 0)

            # Test ghép đúng thứ tự
            original = syntax_puzzle['original_sentence']
            tokens = original.replace('.', '').replace('?', '').replace('!', '').split()
            verify_res = engine.verify_syntax_scramble(original, tokens)
            self.assertTrue(verify_res['is_correct'])
            print("[✓] test_02_local_scramble_engine_syntax passed!")

    def test_03_roadmap_api(self):
        """Kiểm tra API Lộ trình Target Band & Chặng Milestone"""
        # 1. Lấy roadmap hiện tại
        res = self.client.get('/api/roadmap/current')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('target_band', data)
        self.assertIn('milestones', data)
        self.assertTrue(len(data['milestones']) > 0)

        # 2. Đổi target band
        res_target = self.client.post('/api/roadmap/set_target', json={'target_band': 'C1'})
        self.assertEqual(res_target.status_code, 200)
        self.assertEqual(res_target.get_json()['target_band'], 'C1')

        # 3. Lấy chi tiết milestone 1
        m_id = data['milestones'][0]['id']
        res_m = self.client.get(f'/api/roadmap/milestone/{m_id}')
        self.assertEqual(res_m.status_code, 200)
        m_data = res_m.get_json()
        self.assertIn('milestone', m_data)
        self.assertIn('vocabularies', m_data)

        # 4. Nộp bài vượt ải milestone
        res_submit = self.client.post(f'/api/roadmap/milestone/{m_id}/submit', json={'score': 9.5})
        self.assertEqual(res_submit.status_code, 200)
        sub_data = res_submit.get_json()
        self.assertTrue(sub_data['passed'])
        print("[✓] test_03_roadmap_api passed!")

    def test_04_cosmetics_and_shop_api(self):
        """Kiểm tra API Cửa hàng Trang trí, Mua và Trang bị Khung Avatar"""
        # 1. Lấy danh sách cosmetics
        res = self.client.get('/api/game/cosmetics')
        self.assertEqual(res.status_code, 200)
        cosmetics = res.get_json()['cosmetics']
        self.assertTrue(len(cosmetics) > 0)

        # 2. Tìm một item có bán (price > 0)
        target_item = next((c for c in cosmetics if c['price_coins'] > 0), None)
        self.assertIsNotNone(target_item)

        # 3. Mua item
        res_buy = self.client.post('/api/game/cosmetics/buy', json={'item_id': target_item['id']})
        # Hoặc 200 thành công hoặc 400 nếu đã sở hữu
        self.assertIn(res_buy.status_code, [200, 400])

        # 4. Trang bị item
        res_equip = self.client.post('/api/game/cosmetics/equip', json={'item_id': target_item['id']})
        self.assertEqual(res_equip.status_code, 200)

        # 5. Kiểm tra kho đồ cá nhân
        res_inv = self.client.get('/api/game/cosmetics/my_inventory')
        self.assertEqual(res_inv.status_code, 200)
        inv = res_inv.get_json()
        self.assertTrue(len(inv['inventory']) > 0)
        print("[✓] test_04_cosmetics_and_shop_api passed!")

    def test_05_system_flow_improvements(self):
        """Kiểm tra toàn bộ 5 cải tiến luồng hệ thống mới"""
        with self.app.app_context():
            # 1. Kiểm tra Lộ trình phủ trọn C1 & C2 (Đủ 12 chặng)
            self.client.post('/api/roadmap/set_target', json={'target_band': 'C2'})
            res_c2 = self.client.get('/api/roadmap/current')
            self.assertEqual(res_c2.status_code, 200)
            data_c2 = res_c2.get_json()
            self.assertEqual(data_c2['target_band'], 'C2')
            self.assertEqual(data_c2['total_milestones'], 12)
            c2_bands = {m['band_level'] for m in data_c2['milestones']}
            self.assertEqual(c2_bands, {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'})

            # 2. Kiểm tra Vượt ải tự động mở khóa từ vựng vào Smart SRS
            m_target = data_c2['milestones'][0]
            from app.models.user_vocabulary import UserVocabulary
            vocab_ids = RoadmapMilestone.query.get(m_target['id']).get_vocab_ids()
            
            res_sub = self.client.post(f"/api/roadmap/milestone/{m_target['id']}/submit", json={'score': 10.0})
            self.assertEqual(res_sub.status_code, 200)
            
            # Đảm bảo từ vựng chặng đã được nạp vào UserVocabulary
            for vid in vocab_ids:
                uv = UserVocabulary.query.filter_by(user_id=self.user_id, vocab_id=vid).first()
                self.assertIsNotNone(uv)
                self.assertTrue(uv.is_unlocked)
                self.assertEqual(uv.memorization_level, 'DA_THUOC')

            # 3. Kiểm tra trang bị Khung Tiêu Chuẩn từ kho đồ không bị lỗi ID 0
            res_inv = self.client.get('/api/game/cosmetics/my_inventory')
            inv_items = res_inv.get_json()['inventory']
            default_item = next((it for it in inv_items if it['css_class'] == 'frame-default'), None)
            self.assertIsNotNone(default_item)
            self.assertGreater(default_item['id'], 0) # Không được bằng 0!
            
            # Trang bị lại Khung Tiêu Chuẩn
            res_equip_def = self.client.post('/api/game/cosmetics/equip', json={'item_id': default_item['id']})
            self.assertEqual(res_equip_def.status_code, 200)
            self.assertEqual(res_equip_def.get_json()['equipped_frame'], 'frame-default')

            # 4. Kiểm tra Leaderboard API trả về Avatar + Khung phát sáng + Danh hiệu
            res_lb = self.client.get('/api/game/gacha/leaderboard')
            self.assertEqual(res_lb.status_code, 200)
            lb_list = res_lb.get_json()['leaderboard']
            if lb_list:
                top1 = lb_list[0]
                self.assertIn('avatar', top1)
                self.assertIn('equipped_frame', top1)
                self.assertIn('equipped_title', top1)
                self.assertIn('current_level', top1)

            # 5. Kiểm tra phân trang từ vựng trong câu đố ghép chữ (vocab_idx)
            res_p1 = self.client.get(f"/api/roadmap/milestone/{m_target['id']}?vocab_idx=0")
            res_p2 = self.client.get(f"/api/roadmap/milestone/{m_target['id']}?vocab_idx=1")
            self.assertEqual(res_p1.status_code, 200)
            self.assertEqual(res_p2.status_code, 200)
            p1_data = res_p1.get_json()
            p2_data = res_p2.get_json()
            self.assertIn('current_vocab_idx', p1_data)
            self.assertEqual(p1_data['current_vocab_idx'], 0)
            self.assertEqual(p2_data['current_vocab_idx'], 1)

            print("[✓] test_05_system_flow_improvements passed successfully!")


if __name__ == '__main__':
    unittest.main()
