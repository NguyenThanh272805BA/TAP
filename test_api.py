import requests

BASE_URL = "http://127.0.0.1:5000/api/auth"

def test_register():
    print("--- TEST ĐĂNG KÝ ---")
    data = {"username": "thanhnguyen_test", "password": "123"}
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Kết quả: {response.json()}\n")

def test_login():
    print("--- TEST ĐĂNG NHẬP ---")
    data = {"username": "thanhnguyen_test", "password": "123"}
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Kết quả: {response.json()}\n")

if __name__ == "__main__":
    # Nhớ đảm bảo file run.py (Server Flask) đang được chạy ở một Terminal khác nhé!
    test_register()
    test_login()


    # Bổ sung vào cuối file test_api.py cũ:

    def test_game_logic():
        print("--- TEST ĐIỂM DANH & MỞ KHÓA TỪ VỰNG ---")
        # Giả định user_id = 1 là tài khoản chúng ta vừa tạo ở lượt test trước
        data = {"user_id": 1}
        response = requests.post("http://127.0.0.1:5000/api/game/checkin", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Kết quả: {response.json()}\n")


    if __name__ == "__main__":
        # test_register()
        # test_login()
        test_game_logic()  # Chạy hàm test mới này


        def test_ai_evaluate():
            print("\n--- TEST AI CHẤM ĐIỂM (CẨN THẬN BỊ CHỬI) ---")
            data = {
                "user_id": 1,
                "text": "I wish I have a lot of money to buy game."
            }
            response = requests.post("http://127.0.0.1:5000/api/ai/evaluate", json=data)
            print(f"Status Code: {response.status_code}")
            print(f"Kết quả:\n{response.text}")


        if __name__ == "__main__":
            # test_register()
            # test_login()
            # test_game_logic()
            test_ai_evaluate()  # Gọi API AI