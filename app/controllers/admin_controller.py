import os
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, session, request, current_app
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.story_topic import StoryTopic
from app.models.grammar import Grammar
from app.models.test import TestLog
from app.models.user_vocabulary import UserVocabulary
from app.models.user_grammar import UserGrammar
from app.models.user_achievement import UserAchievement
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.models.roadmap import UserMilestoneProgress
from app.models.story_session import StorySession
from app.models.daily_quest import DailyQuest
from app.models.quest import Quest, UserQuestProgress
from app.models.notification import Notification
from app import db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Cấu hình thư mục upload ảnh bìa (Sẽ tự động tạo nếu chưa tồn tại)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# MIDDLEWARE: Bảo vệ API, chỉ cho phép Admin truy cập
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({"error": "[ SECURITY BREACH ] Bạn không có quyền truy cập khu vực này!"}), 403

        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    users_count = User.query.count()
    vocab_count = Vocabulary.query.count()
    grammar_count = Grammar.query.count()
    tests_count = TestLog.query.count()
    topics_count = StoryTopic.query.count()
    cosmetics_count = CosmeticItem.query.count()
    quests_count = Quest.query.count()

    return jsonify({
        "users": users_count,
        "vocab": vocab_count,
        "grammar": grammar_count,
        "tests": tests_count,
        "topics": topics_count,
        "cosmetics": cosmetics_count,
        "quests": quests_count
    }), 200


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "level": u.current_level,
        "role": u.role,
        "coins": u.coins,
        "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A"
    } for u in users]), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        return jsonify({"error": "Lỗi: Không thể tự xóa tài khoản của chính mình!"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn player {user.username} khỏi máy chủ!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ CHỦ ĐỀ TEXT-RPG
# ==========================================
@admin_bp.route('/topics', methods=['GET'])
@admin_required
def get_topics():
    topics = StoryTopic.query.all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "genre": t.genre,
        "cover_image": t.cover_image,
        "system_prompt": t.system_prompt,
        "play_mode": getattr(t, 'play_mode', 'both')
    } for t in topics]), 200


@admin_bp.route('/topics', methods=['POST'])
@admin_required
def create_topic():
    title = request.form.get('title')
    genre = request.form.get('genre')
    system_prompt = request.form.get('system_prompt')
    play_mode = request.form.get('play_mode', 'both') # Phase 3: Đọc play_mode

    if not title or not system_prompt:
        return jsonify({"error": "Thiếu thông tin bắt buộc!"}), 400

    filename = 'default_cover.jpg'
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers')

            os.makedirs(upload_path, exist_ok=True)

            # Lưu file
            file.save(os.path.join(upload_path, filename))

    # Phase 3: Gắn thêm trường play_mode
    new_topic = StoryTopic(title=title, genre=genre, cover_image=filename, system_prompt=system_prompt, play_mode=play_mode)
    db.session.add(new_topic)
    db.session.commit()
    return jsonify({"message": "Đã ghi nhận Chủ đề Truyện mới vào Hệ thống Lõi!"}), 201


@admin_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@admin_required
def delete_topic(topic_id):
    topic = StoryTopic.query.get(topic_id)
    if not topic:
        return jsonify({"error": "Không tìm thấy chủ đề này!"}), 404
    if topic.cover_image and topic.cover_image != 'default_cover.jpg':
        base_dir = os.path.abspath(os.path.dirname(__file__))
        cover_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers', topic.cover_image)
        if os.path.exists(cover_path):
            try:
                os.remove(cover_path)
            except:
                pass

    # Xóa các StorySession thuộc topic này trước khi xóa topic
    StorySession.query.filter_by(topic_id=topic_id).delete()

    db.session.delete(topic)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn chủ đề '{topic.title}' khỏi hệ thống!"}), 200


@admin_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@admin_required
def update_topic(topic_id):
    topic = StoryTopic.query.get(topic_id)
    if not topic:
        return jsonify({"error": "Không tìm thấy chủ đề này!"}), 404

    title = request.form.get('title')
    genre = request.form.get('genre')
    system_prompt = request.form.get('system_prompt')
    play_mode = request.form.get('play_mode')

    if title:
        topic.title = title.strip()
    if genre:
        topic.genre = genre.strip()
    if system_prompt:
        topic.system_prompt = system_prompt.strip()
    if play_mode:
        topic.play_mode = play_mode.strip()

    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_dir, '..', 'views', 'static', 'uploads', 'covers')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            topic.cover_image = filename

    db.session.commit()
    return jsonify({"message": f"Đã cập nhật chủ đề truyện '{topic.title}' thành công!"}), 200


@admin_bp.route('/story-sessions', methods=['GET'])
@admin_required
def get_story_sessions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    status = request.args.get('status', '').strip()

    query = StorySession.query
    if status and status != 'ALL':
        query = query.filter_by(status=status)

    total = query.count()
    sessions = query.order_by(StorySession.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
        "sessions": [{
            "id": s.id,
            "user_id": s.user_id,
            "username": s.user.username if s.user else 'Unknown',
            "topic_id": s.topic_id,
            "topic_title": s.topic.title if s.topic else 'Deleted Topic',
            "status": s.status,
            "summary_en": (s.summary_en[:120] + '...') if s.summary_en and len(s.summary_en) > 120 else (s.summary_en or ''),
            "summary_vn": (s.summary_vn[:120] + '...') if s.summary_vn and len(s.summary_vn) > 120 else (s.summary_vn or ''),
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "N/A"
        } for s in sessions]
    }), 200


@admin_bp.route('/story-sessions/<int:session_id>', methods=['DELETE'])
@admin_required
def delete_story_session(session_id):
    session_item = StorySession.query.get(session_id)
    if not session_item:
        return jsonify({"error": "Không tìm thấy phiên truyện này!"}), 404

    db.session.delete(session_item)
    db.session.commit()
    return jsonify({"message": f"Đã xóa phiên truyện #{session_id} thành công!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ TỪ VỰNG (VOCABULARY)
# ==========================================
@admin_bp.route('/vocabulary', methods=['GET'])
@admin_required
def get_vocabularies():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search = request.args.get('search', '', type=str).strip()
    level = request.args.get('level', '', type=str).strip().upper()

    query = Vocabulary.query
    if search:
        query = query.filter(
            (Vocabulary.word.ilike(f'%{search}%')) |
            (Vocabulary.meaning.ilike(f'%{search}%')) |
            (Vocabulary.theme.ilike(f'%{search}%'))
        )
    if level and level != 'ALL':
        query = query.filter(Vocabulary.cefr_level == level)

    total = query.count()
    items = query.order_by(Vocabulary.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
        "vocabularies": [{
            "id": v.id,
            "word": v.word,
            "meaning": v.meaning,
            "theme": v.theme or 'General',
            "cefr_level": v.cefr_level or 'A1',
            "is_unlocked": bool(v.is_unlocked),
            "is_memorized": bool(v.is_memorized)
        } for v in items]
    }), 200


@admin_bp.route('/vocabulary', methods=['POST'])
@admin_required
def create_vocabulary():
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    meaning = data.get('meaning', '').strip()
    theme = data.get('theme', 'General').strip() or 'General'
    cefr_level = data.get('cefr_level', 'A1').strip().upper() or 'A1'

    if not word or not meaning:
        return jsonify({"error": "Vui lòng nhập đầy đủ từ vựng và nghĩa!"}), 400

    existing = Vocabulary.query.filter_by(word=word).first()
    if existing:
        return jsonify({"error": f"Từ '{word}' đã tồn tại trong từ điển!"}), 400

    new_vocab = Vocabulary(word=word, meaning=meaning, theme=theme, cefr_level=cefr_level)
    db.session.add(new_vocab)
    db.session.commit()
    return jsonify({"message": f"Đã thêm thành công từ vựng '{word}'!", "id": new_vocab.id}), 201


@admin_bp.route('/vocabulary/<int:vocab_id>', methods=['DELETE'])
@admin_required
def delete_vocabulary(vocab_id):
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Không tìm thấy từ vựng này!"}), 404

    # Xóa liên kết trong UserVocabulary và DailyQuest nếu có
    UserVocabulary.query.filter_by(vocab_id=vocab_id).delete()
    DailyQuest.query.filter_by(vocab_id=vocab_id).delete()
    db.session.delete(vocab)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn từ vựng '{vocab.word}' khỏi từ điển!"}), 200


@admin_bp.route('/vocabulary/<int:vocab_id>', methods=['PUT'])
@admin_required
def update_vocabulary(vocab_id):
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Không tìm thấy từ vựng này!"}), 404

    data = request.get_json() or {}
    if 'word' in data and data['word'].strip():
        vocab.word = data['word'].strip()
    if 'meaning' in data and data['meaning'].strip():
        vocab.meaning = data['meaning'].strip()
    if 'theme' in data and data['theme'].strip():
        vocab.theme = data['theme'].strip()
    if 'cefr_level' in data and data['cefr_level'].strip():
        vocab.cefr_level = data['cefr_level'].strip().upper()

    db.session.commit()
    return jsonify({"message": f"Đã cập nhật từ vựng '{vocab.word}' thành công!"}), 200


# ==========================================
# CÁC ROUTE TIẾN ĐỘ VÀ RESET DỮ LIỆU
# ==========================================
@admin_bp.route('/users/<int:user_id>/reset', methods=['POST'])
@admin_required
def reset_user_progress(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    try:
        UserVocabulary.query.filter_by(user_id=user_id).delete()
        UserGrammar.query.filter_by(user_id=user_id).delete()
        UserAchievement.query.filter_by(user_id=user_id).delete()
        UserCosmetic.query.filter_by(user_id=user_id).delete()
        UserMilestoneProgress.query.filter_by(user_id=user_id).delete()
        TestLog.query.filter_by(user_id=user_id).delete()
        DailyQuest.query.filter_by(user_id=user_id).delete()
        Notification.query.filter_by(user_id=user_id).delete()
        StorySession.query.filter_by(user_id=user_id).delete()

        user.coins = 0
        user.streak_count = 0
        user.current_level = 'Tân Binh Ngơ Ngác'
        user.current_band = 'A1'
        user.arena_stage = 1
        user.infinity_score = 0
        user.last_checkin = None
        user.last_quest_date = None
        user.equipped_frame = 'frame-default'
        user.equipped_title = 'Tân Binh Ngơ Ngác'

        db.session.commit()
        return jsonify({"message": f"Đã reset toàn bộ tiến độ của @{user.username} về mặc định!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi khi reset tiến độ: {str(e)}"}), 500


@admin_bp.route('/reset-data', methods=['DELETE'])
@admin_required
def reset_all_data():
    data = request.get_json() or {}
    confirm_code = data.get('confirm_code', '').strip()

    if confirm_code != "XAC_NHAN_XOA_TOAN_BO":
        return jsonify({"error": "Mã xác nhận không chính xác! Vui lòng nhập đúng 'XAC_NHAN_XOA_TOAN_BO'."}), 400

    try:
        deleted = {}
        deleted["StorySession"] = StorySession.query.delete()
        deleted["UserVocabulary"] = UserVocabulary.query.delete()
        deleted["UserGrammar"] = UserGrammar.query.delete()
        deleted["UserAchievement"] = UserAchievement.query.delete()
        deleted["UserCosmetic"] = UserCosmetic.query.delete()
        deleted["UserMilestoneProgress"] = UserMilestoneProgress.query.delete()
        deleted["TestLog"] = TestLog.query.delete()
        deleted["DailyQuest"] = DailyQuest.query.delete()
        deleted["Notification"] = Notification.query.delete()

        # Xóa tất cả user không phải admin
        non_admins = User.query.filter(User.role != 'admin').all()
        deleted["User (non-admin)"] = len(non_admins)
        for u in non_admins:
            db.session.delete(u)

        db.session.commit()
        admins = User.query.filter_by(role='admin').all()
        return jsonify({
            "message": "Dọn dẹp dữ liệu hoàn tất! Toàn bộ tiến độ và tài khoản người dùng thường đã bị xóa.",
            "deleted_stats": deleted,
            "admins_retained": [a.username for a in admins]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi khi dọn dẹp hệ thống: {str(e)}"}), 500


# ==========================================
# CÁC ROUTE QUẢN LÝ VẬT PHẨM & SHOP (COSMETICS)
# ==========================================
@admin_bp.route('/shop/items', methods=['GET'])
@admin_required
def get_shop_items():
    item_type = request.args.get('type', '').strip().upper()
    search = request.args.get('search', '').strip()

    query = CosmeticItem.query
    if item_type and item_type != 'ALL':
        query = query.filter_by(type=item_type)
    if search:
        query = query.filter(
            (CosmeticItem.name.ilike(f'%{search}%')) |
            (CosmeticItem.description.ilike(f'%{search}%')) |
            (CosmeticItem.css_class.ilike(f'%{search}%'))
        )

    items = query.order_by(CosmeticItem.price_coins.asc(), CosmeticItem.id.asc()).all()
    return jsonify([{
        "id": it.id,
        "name": it.name,
        "type": it.type,
        "css_class": it.css_class,
        "description": it.description or '',
        "price_coins": it.price_coins,
        "icon_preview": it.icon_preview or 'default_item.png',
        "item_effect": it.item_effect,
        "owners_count": len(it.owners) if hasattr(it, 'owners') else 0
    } for it in items]), 200


@admin_bp.route('/shop/items', methods=['POST'])
@admin_required
def create_shop_item():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    item_type = (data.get('type') or 'AVATAR_FRAME').strip().upper()
    css_class = (data.get('css_class') or '').strip()
    price_coins = int(data.get('price_coins') or 0)
    description = (data.get('description') or '').strip()
    icon_preview = (data.get('icon_preview') or 'default_item.png').strip() or 'default_item.png'
    item_effect = (data.get('item_effect') or '').strip() or None

    if not name or not css_class:
        return jsonify({"error": "Vui lòng nhập đầy đủ Tên vật phẩm và CSS class!"}), 400

    existing = CosmeticItem.query.filter_by(css_class=css_class).first()
    if existing:
        return jsonify({"error": f"Vật phẩm có mã CSS '{css_class}' đã tồn tại!"}), 400

    new_item = CosmeticItem(
        name=name,
        type=item_type,
        css_class=css_class,
        price_coins=price_coins,
        description=description,
        icon_preview=icon_preview,
        item_effect=item_effect
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": f"Đã tạo thành công vật phẩm '{name}'!", "id": new_item.id}), 201


@admin_bp.route('/shop/items/<int:item_id>', methods=['PUT'])
@admin_required
def update_shop_item(item_id):
    item = CosmeticItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Không tìm thấy vật phẩm này!"}), 404

    data = request.get_json() or {}
    if 'name' in data and data['name']:
        item.name = str(data['name']).strip()
    if 'type' in data and data['type']:
        item.type = str(data['type']).strip().upper()
    if 'css_class' in data and data['css_class']:
        item.css_class = str(data['css_class']).strip()
    if 'price_coins' in data and data['price_coins'] is not None:
        item.price_coins = int(data['price_coins'])
    if 'description' in data:
        item.description = (data['description'] or '').strip()
    if 'icon_preview' in data:
        item.icon_preview = (data['icon_preview'] or 'default_item.png').strip() or 'default_item.png'
    if 'item_effect' in data:
        item.item_effect = (data['item_effect'] or '').strip() or None

    db.session.commit()
    return jsonify({"message": f"Đã cập nhật vật phẩm '{item.name}' thành công!"}), 200


@admin_bp.route('/shop/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_shop_item(item_id):
    item = CosmeticItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Không tìm thấy vật phẩm!"}), 404

    UserCosmetic.query.filter_by(cosmetic_id=item_id).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn vật phẩm '{item.name}' khỏi Cửa hàng!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ DANH MỤC & NGỮ PHÁP (GRAMMAR)
# ==========================================
@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    vocab_themes = db.session.query(
        Vocabulary.theme, db.func.count(Vocabulary.id)
    ).group_by(Vocabulary.theme).all()

    grammar_cats = db.session.query(
        Grammar.category, db.func.count(Grammar.id)
    ).group_by(Grammar.category).all()

    return jsonify({
        "vocabulary_themes": [{"name": t[0] or 'General', "count": t[1]} for t in vocab_themes],
        "grammar_categories": [{"name": c[0] or 'General', "count": c[1]} for c in grammar_cats]
    }), 200


@admin_bp.route('/categories/rename', methods=['POST'])
@admin_required
def rename_category():
    data = request.get_json() or {}
    source_type = data.get('source_type', 'both')
    old_name = data.get('old_name', '').strip()
    new_name = data.get('new_name', '').strip()

    if not old_name or not new_name:
        return jsonify({"error": "Vui lòng nhập tên danh mục cũ và tên danh mục mới!"}), 400

    vocab_updated = 0
    grammar_updated = 0

    if source_type in ['vocab', 'both']:
        vocab_updated = Vocabulary.query.filter_by(theme=old_name).update({Vocabulary.theme: new_name})
    if source_type in ['grammar', 'both']:
        grammar_updated = Grammar.query.filter_by(category=old_name).update({Grammar.category: new_name})

    db.session.commit()
    return jsonify({
        "message": f"Đã đổi tên danh mục từ '{old_name}' sang '{new_name}'!",
        "vocab_updated": vocab_updated,
        "grammar_updated": grammar_updated
    }), 200


@admin_bp.route('/grammars', methods=['GET'])
@admin_required
def get_grammars():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search = request.args.get('search', '', type=str).strip()
    level = request.args.get('level', '', type=str).strip().upper()
    category = request.args.get('category', '', type=str).strip()

    query = Grammar.query
    if search:
        query = query.filter(
            (Grammar.structure.ilike(f'%{search}%')) |
            (Grammar.explanation.ilike(f'%{search}%')) |
            (Grammar.example.ilike(f'%{search}%'))
        )
    if level and level != 'ALL':
        query = query.filter(Grammar.cefr_level == level)
    if category and category != 'ALL':
        query = query.filter(Grammar.category == category)

    total = query.count()
    items = query.order_by(Grammar.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
        "grammars": [{
            "id": g.id,
            "structure": g.structure,
            "explanation": g.explanation,
            "example": g.example or '',
            "cefr_level": g.cefr_level or 'A1',
            "category": g.category or 'General',
            "difficulty_score": g.difficulty_score or 1,
            "is_slang": bool(g.is_slang)
        } for g in items]
    }), 200


@admin_bp.route('/grammars', methods=['POST'])
@admin_required
def create_grammar():
    data = request.get_json() or {}
    structure = data.get('structure', '').strip()
    explanation = data.get('explanation', '').strip()
    example = data.get('example', '').strip()
    cefr_level = data.get('cefr_level', 'A1').strip().upper() or 'A1'
    category = data.get('category', 'General').strip() or 'General'
    difficulty_score = int(data.get('difficulty_score', 1))
    is_slang = bool(data.get('is_slang', False))

    if not structure or not explanation:
        return jsonify({"error": "Vui lòng nhập cấu trúc ngữ pháp và phần giải thích!"}), 400

    existing = Grammar.query.filter_by(structure=structure).first()
    if existing:
        return jsonify({"error": f"Cấu trúc '{structure}' đã tồn tại trong thư viện ngữ pháp!"}), 400

    new_g = Grammar(
        structure=structure,
        explanation=explanation,
        example=example,
        cefr_level=cefr_level,
        category=category,
        difficulty_score=difficulty_score,
        is_slang=is_slang
    )
    db.session.add(new_g)
    db.session.commit()
    return jsonify({"message": f"Đã thêm thành công cấu trúc ngữ pháp '{structure}'!", "id": new_g.id}), 201


@admin_bp.route('/grammars/<int:grammar_id>', methods=['PUT'])
@admin_required
def update_grammar(grammar_id):
    g = Grammar.query.get(grammar_id)
    if not g:
        return jsonify({"error": "Không tìm thấy cấu trúc ngữ pháp này!"}), 404

    data = request.get_json() or {}
    if 'structure' in data and data['structure'].strip():
        g.structure = data['structure'].strip()
    if 'explanation' in data and data['explanation'].strip():
        g.explanation = data['explanation'].strip()
    if 'example' in data:
        g.example = data['example'].strip()
    if 'cefr_level' in data and data['cefr_level'].strip():
        g.cefr_level = data['cefr_level'].strip().upper()
    if 'category' in data and data['category'].strip():
        g.category = data['category'].strip()
    if 'difficulty_score' in data:
        g.difficulty_score = int(data['difficulty_score'])
    if 'is_slang' in data:
        g.is_slang = bool(data['is_slang'])

    db.session.commit()
    return jsonify({"message": f"Đã cập nhật thành công cấu trúc ngữ pháp '{g.structure}'!"}), 200


@admin_bp.route('/grammars/<int:grammar_id>', methods=['DELETE'])
@admin_required
def delete_grammar(grammar_id):
    g = Grammar.query.get(grammar_id)
    if not g:
        return jsonify({"error": "Không tìm thấy cấu trúc ngữ pháp này!"}), 404

    UserGrammar.query.filter_by(grammar_id=grammar_id).delete()
    db.session.delete(g)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn cấu trúc ngữ pháp '{g.structure}'!"}), 200


# ==========================================
# CÁC ROUTE QUẢN LÝ NHIỆM VỤ (QUESTS & CÀY XU)
# ==========================================
@admin_bp.route('/quests', methods=['GET'])
@admin_required
def get_quests():
    category = request.args.get('category', '').strip().upper()
    search = request.args.get('search', '').strip()

    query = Quest.query
    if category and category != 'ALL':
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            (Quest.title.ilike(f'%{search}%')) |
            (Quest.description.ilike(f'%{search}%')) |
            (Quest.quest_code.ilike(f'%{search}%'))
        )

    quests = query.order_by(Quest.category.asc(), Quest.order_index.asc()).all()
    return jsonify([{
        "id": q.id,
        "quest_code": q.quest_code,
        "category": q.category,
        "title": q.title,
        "description": q.description,
        "target_type": q.target_type,
        "target_count": q.target_count,
        "reward_coins": q.reward_coins,
        "reward_exp": q.reward_exp,
        "badge_icon": q.badge_icon,
        "order_index": q.order_index
    } for q in quests]), 200


@admin_bp.route('/quests', methods=['POST'])
@admin_required
def create_quest():
    data = request.get_json() or {}
    quest_code = data.get('quest_code', '').strip()
    category = data.get('category', 'NEWBIE').strip().upper()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    target_type = data.get('target_type', 'VOCAB_COUNT').strip().upper()
    target_count = int(data.get('target_count', 1))
    reward_coins = int(data.get('reward_coins', 20))
    reward_exp = int(data.get('reward_exp', 50))
    badge_icon = data.get('badge_icon', 'quest').strip() or 'quest'
    order_index = int(data.get('order_index', 1))

    if not quest_code or not title or not description:
        return jsonify({"error": "Vui lòng nhập đầy đủ Mã nhiệm vụ, Tiêu đề và Mô tả!"}), 400

    existing = Quest.query.filter_by(quest_code=quest_code).first()
    if existing:
        return jsonify({"error": f"Nhiệm vụ với mã '{quest_code}' đã tồn tại!"}), 400

    new_q = Quest(
        quest_code=quest_code,
        category=category,
        title=title,
        description=description,
        target_type=target_type,
        target_count=target_count,
        reward_coins=reward_coins,
        reward_exp=reward_exp,
        badge_icon=badge_icon,
        order_index=order_index
    )
    db.session.add(new_q)
    db.session.commit()
    return jsonify({"message": f"Đã tạo thành công nhiệm vụ '{title}'!", "id": new_q.id}), 201


@admin_bp.route('/quests/<int:quest_id>', methods=['PUT'])
@admin_required
def update_quest(quest_id):
    q = Quest.query.get(quest_id)
    if not q:
        return jsonify({"error": "Không tìm thấy nhiệm vụ này!"}), 404

    data = request.get_json() or {}
    if 'quest_code' in data and data['quest_code'].strip():
        q.quest_code = data['quest_code'].strip()
    if 'category' in data and data['category'].strip():
        q.category = data['category'].strip().upper()
    if 'title' in data and data['title'].strip():
        q.title = data['title'].strip()
    if 'description' in data and data['description'].strip():
        q.description = data['description'].strip()
    if 'target_type' in data and data['target_type'].strip():
        q.target_type = data['target_type'].strip().upper()
    if 'target_count' in data:
        q.target_count = int(data['target_count'])
    if 'reward_coins' in data:
        q.reward_coins = int(data['reward_coins'])
    if 'reward_exp' in data:
        q.reward_exp = int(data['reward_exp'])
    if 'badge_icon' in data:
        q.badge_icon = data['badge_icon'].strip()
    if 'order_index' in data:
        q.order_index = int(data['order_index'])

    db.session.commit()
    return jsonify({"message": f"Đã cập nhật nhiệm vụ '{q.title}' thành công!"}), 200


@admin_bp.route('/quests/<int:quest_id>', methods=['DELETE'])
@admin_required
def delete_quest(quest_id):
    q = Quest.query.get(quest_id)
    if not q:
        return jsonify({"error": "Không tìm thấy nhiệm vụ này!"}), 404

    UserQuestProgress.query.filter_by(quest_id=quest_id).delete()
    db.session.delete(q)
    db.session.commit()
    return jsonify({"message": f"Đã xóa vĩnh viễn nhiệm vụ '{q.title}'!"}), 200