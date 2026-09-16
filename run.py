from app import create_app
from waitress import serve

app = create_app()

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

if __name__ == "__main__":
    print("\n" + "="*60, flush=True)
    print("[SYSTEM] Khởi chạy máy chủ Đa luồng Production qua Waitress WSGI (16 Threads)", flush=True)
    print("[SYSTEM] Tương thích cao, chống nghẽn luồng truy vấn đồng thời", flush=True)
    print("[SYSTEM] >>> TRUY CẬP ỨNG DỤNG TẠI: http://127.0.0.1:5000 <<<", flush=True)
    print("="*60 + "\n", flush=True)
    serve(app, host='127.0.0.1', port=5000, threads=16, channel_timeout=60, cleanup_interval=30)