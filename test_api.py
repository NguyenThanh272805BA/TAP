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