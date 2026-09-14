import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE users MODIFY COLUMN current_level VARCHAR(100) DEFAULT 'Tân Binh Ngơ Ngác'"))
        conn.commit()
        print("[+] Đã mở rộng users.current_level thành VARCHAR(100) thành công!")
