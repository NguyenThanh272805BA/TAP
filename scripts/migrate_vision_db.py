import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def migrate():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'global_fluent_db')
    )
    cursor = conn.cursor()
    try:
        # 1. Thêm cột source_type và context_note vào user_vocabularies nếu chưa có
        cursor.execute("SHOW COLUMNS FROM user_vocabularies LIKE 'source_type'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE user_vocabularies 
                ADD COLUMN source_type VARCHAR(50) DEFAULT 'system',
                ADD COLUMN context_note VARCHAR(255) NULL
            """)
            print("[x] Added source_type and context_note to user_vocabularies.")
        else:
            print("[*] user_vocabularies columns already exist.")

        # 2. Tạo bảng vision_detection_logs nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vision_detection_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                detected_object VARCHAR(100) NOT NULL,
                detected_parts JSON NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("[x] Created or verified table vision_detection_logs.")

        conn.commit()
        print(">>> Migration Vision DB successful!")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating DB: {e}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
