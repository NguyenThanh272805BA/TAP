# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

# Khởi tạo instance database
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Lấy thông tin từ file .env để ghép thành chuỗi kết nối MySQL
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    # Cấu hình chuỗi URI cho SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Gắn db vào app
    db.init_app(app)
