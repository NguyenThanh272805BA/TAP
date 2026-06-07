import os
import pymysql
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()


def test_connection():
    try:
        # Lấy thông tin từ file .env
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if connection.open:
            print("Ping thành công! Database 'global_fluent_db' đã kết nối ngon lành.")

            # Thử lấy version của MySQL để chắc chắn
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                db_version = cursor.fetchone()
                print(f" MySQL Version: {db_version[0]}")

    except Exception as e:
        print(f" Toang rồi, lỗi kết nối: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


if __name__ == "__main__":
    test_connection()