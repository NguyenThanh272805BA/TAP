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
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }

    # Cấu hình SECRET_KEY mã hóa Session an toàn
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "Monimeo2005?")

    # Gắn kết cấu cấu hình Database vào Flask Application instance (CHỈ GỌI 1 LẦN Ở ĐÂY)
    db.init_app(app)

    @app.context_processor
    def inject_current_user():
        from flask import session
        from app.models.user import User
        user_id = session.get('user_id')
        current_user = User.query.get(user_id) if user_id else None
        return dict(current_user=current_user)

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

    # 3. Trung tâm Khảo thí CEFR (Lobby & Các phân hệ tách biệt)
    @app.route('/test')
    def test_page():
        return render_template('test.html')

    @app.route('/test/placement')
    def test_placement_page():
        return render_template('test_placement.html')

    @app.route('/test/bands')
    def test_bands_page():
        return render_template('test_bands.html')

    @app.route('/test/history')
    def test_history_page():
        return render_template('test_history.html')

    # 4. Phòng thi độc lập (Dedicated Exam Chamber)
    @app.route('/test/room')
    def exam_room_page():
        return render_template('exam_room.html')

    # 5. Đấu Trường Phản Xạ AI & Gacha (Tách biệt hoàn toàn khỏi Khảo thí)
    @app.route('/arena')
    def arena_page():
        return render_template('arena.html')

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

    @app.route('/roadmap')
    def roadmap_page():
        return render_template('roadmap.html')

    # 10. Bảng Xếp Hạng Thành Tích Toàn Diện (Đa Chiều)
    @app.route('/leaderboard')
    def leaderboard_page():
        return render_template('leaderboard.html')

    # 11. Trung Tâm 500 Nhiệm Vụ Cày Xu
    @app.route('/quests')
    def quests_page():
        return render_template('quests.html')


    # --- ĐĂNG KÝ CÁC BLUEPRINTS ĐIỀU HƯỚNG API BACKEND ---
    from app.controllers.auth_controller import auth_bp
    from app.controllers.game_controller import game_bp
    from app.controllers.ai_controller import ai_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.roadmap_controller import roadmap_bp
    from app.controllers.leaderboard_controller import leaderboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(leaderboard_bp)

    return app