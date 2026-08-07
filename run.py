from app import create_app
from waitress import serve

app = create_app()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("[SYSTEM] Khởi chạy máy chủ Production qua Waitress WSGI")
    print("[SYSTEM] An toàn và tương thích 100% trên Python 3.14")
    print("[SYSTEM] >>> TRUY CẬP ỨNG DỤNG TẠI: http://127.0.0.1:5000 <<<")
    print("="*60 + "\n")
    serve(app, host='127.0.0.1', port=5000)