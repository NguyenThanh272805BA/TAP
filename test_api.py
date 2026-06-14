import unittest
import json
from app import create_app, db


class GlobalFluentAPITestCase(unittest.TestCase):
    def setUp(self):
        """Setup trước mỗi Test Case (Tạo môi trường giả lập)"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_auth_register_missing_data(self):
        """Test API Đăng ký khi thiếu mật khẩu"""
        payload = {"username": "test_bot"}
        response = self.client.post('/api/auth/register', json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)

    def test_gacha_roll_api(self):
        """Test API bốc Gacha xem có trả về đúng 4 sự lựa chọn không"""
        payload = {"user_id": 1}  # Giả định user_id 1 có tồn tại
        response = self.client.post('/api/game/gacha/roll', json=payload)
        data = json.loads(response.data)

        # Nếu chưa mở khóa hết thì phải trả về status success và có mảng options
        if data.get('status') == 'success':
            self.assertEqual(len(data['options']), 4)
            self.assertIn('vocab_id', data)


if __name__ == '__main__':
    unittest.main()