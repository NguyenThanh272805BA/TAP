from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

# Tải các biến môi trường cấu hình bảo mật từ tệp .env
load_dotenv()

# Khởi tạo instance database SQLAlchemy để quản lý ORM
db = SQLAlchemy()


def create_app():
    # Định vị chính xác tuyệt đối từ thư mục gốc của phân vùng app
    base_dir = os.path.abspath(os.path.dirname(__file__))

    # CẤU HÌNH KHỚP 100% CÂY THƯ MỤC: Cả templates và static đều lùi sâu nằm trong views/
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'views', 'templates'),
        static_folder=os.path.join(base_dir, 'views', 'static')
    )

    # Đọc thông tin kết nối từ file .env
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    # Cấu hình chuỗi kết nối MySQL thông qua driver pymysql
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Cấu hình SECRET_KEY mã hóa Session an toàn
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "Monimeo2005?")

    # Gắn kết cấu cấu hình Database vào Flask Application instance (CHỈ GỌI 1 LẦN Ở ĐÂY)
    db.init_app(app)

    # --- HỆ THỐNG ROUTE ĐIỀU HƯỚNG GIAO DIỆN CHÍNH ---

    # 1. Trang giới thiệu sản phẩm cô đọng (Landing Page)
    @app.route('/')
    def home():
        return render_template('index.html')

    # 2. Trang Tổng hành dinh quản lý tập trung mọi chức năng (Dashboard Hub)
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/learn')
    def learn_page():
        return render_template('learn.html')

    @app.route('/test')
    def test_page():
        return render_template('test.html')

    @app.route('/auth')
    def auth_portal():
        return render_template('auth.html')

    # Đã gom cụm route Story lên đây cho đồng bộ tầng Giao diện
    @app.route('/story')
    def story_page():
        return render_template('story.html')

    # --- THÊM ROUTE CHO GIAO DIỆN ADMIN ---
    @app.route('/admin')
    def admin_page():
        return render_template('admin.html')

    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    @app.route('/shop')
    def shop_page():
        return render_template('shop.html')
    # --- ĐĂNG KÝ CÁC BLUEPRINTS ĐIỀU HƯỚNG API BACKEND ---
    from app.controllers.auth_controller import auth_bp
    from app.controllers.game_controller import game_bp
    from app.controllers.ai_controller import ai_bp
    from app.controllers.admin_controller import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    return app