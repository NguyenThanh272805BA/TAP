from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from app.models.user_vocabulary import UserVocabulary
from app.models.grammar import Grammar
from app.models.daily_quest import DailyQuest
from datetime import datetime, date, timedelta
import random
import time
from app.ml_models.recommender import VocabRecommender
from app.ml_models.srs_predictor import SmartSRS
from app.models.story_session import StorySession
from app.models.story_topic import StoryTopic
from app.models.notification import Notification

from app.utils.achievement_manager import check_and_unlock_achievements
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.ml_models.scramble_engine import LocalScrambleEngine

game_bp = Blueprint('game', __name__, url_prefix='/api/game')
recommender_engine = VocabRecommender()
srs_engine = SmartSRS()
scramble_engine = LocalScrambleEngine()


@game_bp.route('/story/topics', methods=['GET'])
def get_story_topics():
    topics = StoryTopic.query.order_by(StoryTopic.id.desc()).all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "genre": t.genre,
        "cover_image": t.cover_image,
        "system_prompt": t.system_prompt
    } for t in topics]), 200


@game_bp.route('/checkin', methods=['POST'])
def checkin():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập hệ thống!"}), 401

    user = User.query.get(user_id)
    today = date.today()

    if user.last_checkin == today:
        return jsonify({"error": "Bạn đã điểm danh hôm nay rồi! Vui lòng quay lại vào ngày mai."}), 400

    if user.last_checkin and (today - user.last_checkin).days == 1:
        user.streak_count += 1
    else:
        user.streak_count = 1

    user.last_checkin = today

    reward_coins = 10
    bonus_msg = ""
    if user.streak_count % 7 == 0:
        reward_coins += 50
        bonus_msg = " + 50 Xu (Thưởng Chuỗi 7 Ngày)"

    user.coins += reward_coins

    new_achievements = check_and_unlock_achievements(user_id, 'STREAK', user.streak_count)
    if new_achievements:
        for ach in new_achievements:
            bonus_msg += f" \n🏆 Mở khóa thành tựu: {ach['title']} (+{ach['reward']} Xu)"

    unlocked_subquery = db.session.query(UserVocabulary.vocab_id).filter(
        UserVocabulary.user_id == user_id, UserVocabulary.is_unlocked == True
    )
    words_to_unlock = Vocabulary.query.filter(~Vocabulary.id.in_(unlocked_subquery)).limit(2).all()
    unlocked_words_list = []

    for word in words_to_unlock:
        uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=word.id).first()
        if not uv:
            uv = UserVocabulary(user_id=user_id, vocab_id=word.id, is_unlocked=True, memorization_level='CHUA_THUOC')
            db.session.add(uv)
        else:
            uv.is_unlocked = True
        unlocked_words_list.append(word.word)

    db.session.commit()
    return jsonify({
        "message": f"Điểm danh thành công! Bạn nhận được {reward_coins} Xu{bonus_msg}.",
        "current_streak": user.streak_count,
        "new_coins": user.coins,
        "new_words_unlocked": unlocked_words_list
    }), 200


@game_bp.route('/shop/buy', methods=['POST'])
def shop_buy():
    data = request.get_json() or {}
    item_id = data.get('item_id')
    price = data.get('price', 0)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if user.coins < price:
        return jsonify({"error": "Không đủ Xu! Hãy học và điểm danh thêm."}), 400

    user.coins -= price
    db.session.commit()
    return jsonify({"message": f"Mua vật phẩm thành công! (Trừ {price} Xu)", "new_coins": user.coins}), 200


@game_bp.route('/vocabularies', methods=['GET'])
def get_vocabularies():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    results = db.session.query(
        Vocabulary.id, Vocabulary.word, Vocabulary.meaning, Vocabulary.image_url, Vocabulary.theme,
        Vocabulary.cefr_level,
        UserVocabulary.is_unlocked, UserVocabulary.memorization_level, UserVocabulary.next_review_time
    ).join(
        UserVocabulary, (Vocabulary.id == UserVocabulary.vocab_id)
    ).filter(
        UserVocabulary.user_id == user_id
    ).all()

    output = []
    for r in results:
        output.append({
            "id": r.id,
            "word": r.word,
            "meaning": r.meaning,
            "image_url": r.image_url,
            "theme": r.theme,
            "cefr_level": r.cefr_level,
            "is_unlocked": r.is_unlocked if r.is_unlocked is not None else False,
            "is_memorized": True if r.memorization_level == 'DA_THUOC' else False,
            "next_review_time": r.next_review_time.strftime("%Y-%m-%d %H:%M:%S") if r.next_review_time else None
        })
    return jsonify({"vocabularies": output}), 200


@game_bp.route('/recommend', methods=['GET'])
def get_ml_recommendations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    # ML Inference được giữ nguyên
    suggestions = recommender_engine.recommend_next_words(user_id, top_n=5)
    return jsonify({"recommendations": suggestions}), 200


@game_bp.route('/vocab/toggle_memorize', methods=['POST'])
def toggle_memorize():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    vocab = Vocabulary.query.get(vocab_id)
    user = User.query.get(user_id)
    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()

    if not uv:
        uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True, memorization_level='DA_THUOC')
        db.session.add(uv)
        is_memorized_now = True
    else:
        if uv.memorization_level == 'DA_THUOC':
            uv.memorization_level = 'CHUA_THUOC'
            is_memorized_now = False
        else:
            uv.memorization_level = 'DA_THUOC'
            is_memorized_now = True
    db.session.commit()

    current_theme = vocab.theme
    total_words_in_theme = Vocabulary.query.filter_by(theme=current_theme).count()
    memorized_words_in_theme = db.session.query(UserVocabulary).join(Vocabulary).filter(
        UserVocabulary.user_id == user_id, Vocabulary.theme == current_theme,
        UserVocabulary.memorization_level == 'DA_THUOC'
    ).count()

    level_upgraded = False
    if total_words_in_theme > 0 and total_words_in_theme == memorized_words_in_theme:
        if user.current_level == 'Beginner':
            user.current_level = 'Intermediate Explorer'
        elif user.current_level == 'Intermediate Explorer':
            user.current_level = 'Advanced Conqueror'
        level_upgraded = True
        db.session.commit()

    return jsonify({
        "is_memorized": is_memorized_now,
        "theme_progress": f"{memorized_words_in_theme}/{total_words_in_theme}",
        "level_upgraded": level_upgraded,
        "current_level": user.current_level
    }), 200


@game_bp.route('/grammars', methods=['GET'])
def get_grammars():
    return jsonify({"grammars": [
        {"id": g.id, "structure": g.structure, "explanation": g.explanation, "example": g.example,
         "is_slang": g.is_slang} for g in Grammar.query.all()]}), 200


@game_bp.route('/gacha/roll', methods=['POST'])
def gacha_roll():
    data = request.get_json() or {}
    mode = data.get('mode', 'stage')

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    total_vocab = Vocabulary.query.count()

    if total_vocab == 0:
        return jsonify({"error": "Kho từ vựng hệ thống đang trống!"}), 400

    # Lấy Target Word (Loại bỏ ORDER BY RAND)
    if mode == 'stage':
        unlocked_subquery = db.session.query(UserVocabulary.vocab_id).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.is_unlocked == True
        )
        locked_vocab_ids = [v[0] for v in
                            db.session.query(Vocabulary.id).filter(~Vocabulary.id.in_(unlocked_subquery)).all()]

        if not locked_vocab_ids:
            return jsonify(
                {"status": "empty", "message": "[ SYSTEM ] Tuyệt đỉnh! Bạn đã giải cứu toàn bộ kho từ vựng!"}), 200

        target_id = random.choice(locked_vocab_ids)
        target = Vocabulary.query.get(target_id)
    else:
        # Tối ưu Full Table Scan bằng Random Offset
        offset = random.randint(0, total_vocab - 1)
        target = Vocabulary.query.offset(offset).first()

    # Tạo 3 đáp án sai (Distractors) không trùng lặp
    distractors = []
    attempts = 0
    while len(distractors) < 3 and attempts < 15:
        d_off = random.randint(0, total_vocab - 1)
        d = Vocabulary.query.offset(d_off).first()
        if d and d.id != target.id and d.meaning not in [x.meaning for x in distractors]:
            distractors.append(d)
        attempts += 1

    options = [target.meaning] + [d.meaning for d in distractors]
    random.shuffle(options)

    base_time = 5.0
    if mode == 'stage':
        timer = max(3.0, base_time - ((user.arena_stage or 1) * 0.2))
    else:
        timer = random.uniform(5.0, 10.0)

    # BẢO MẬT: Đặt đồng hồ đếm giờ ngay tại Server để chặn Hacker sửa response_time_ms
    session['gacha_start_time'] = time.time()

    return jsonify({
        "status": "success",
        "vocab_id": target.id,
        "word": target.word,
        "options": options,
        "timer": timer,
        "current_stage": user.arena_stage or 1
    }), 200


@game_bp.route('/gacha/verify', methods=['POST'])
def gacha_verify():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    user_answer = data.get('answer', '')
    is_timeout = data.get('timeout', False)
    mode = data.get('mode', 'stage')
    current_gacha_streak = data.get('current_streak', 0)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Phiên làm việc hết hạn!"}), 401

    # BẢO MẬT KÉP: Lấy timestamp thật của server và vô hiệu hóa time ảo từ Client
    start_time = session.pop('gacha_start_time', None)

    if start_time and not is_timeout:
        actual_time_ms = (time.time() - start_time) * 1000
    else:
        actual_time_ms = 5000.0  # Bị timeout hoặc không có timestamp

    # Chống tool auto click (Phản xạ người thường không thể dưới 150ms)
    if actual_time_ms < 150:
        actual_time_ms = 5000.0
        is_timeout = True

    user = User.query.get(user_id)
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Từ vựng không tồn tại!"}), 404

    is_correct = not is_timeout and (vocab.meaning.strip() == user_answer.strip())

    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
    if not uv:
        uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True)
        db.session.add(uv)
    else:
        uv.is_unlocked = True

    current_fail = uv.fail_count if uv.fail_count is not None else 0
    current_avg = uv.avg_response_time if uv.avg_response_time is not None else 0.0
    current_prev_interval = uv.previous_interval if uv.previous_interval is not None else 0.0

    if not is_correct:
        uv.fail_count = current_fail + 1
        current_gacha_streak = 0
    else:
        uv.fail_count = current_fail
        current_gacha_streak += 1

    time_sec = actual_time_ms / 1000.0
    uv.avg_response_time = time_sec if current_avg == 0.0 else (current_avg + time_sec) / 2

    # ML Inference SRS
    next_review_dt, new_interval = srs_engine.predict_next_review(uv.fail_count, uv.avg_response_time,
                                                                  current_prev_interval)
    uv.next_review_time = next_review_dt
    uv.previous_interval = new_interval
    uv.memorization_level = 'DA_THUOC' if is_correct else 'CHUA_THUOC'

    game_message = ""
    is_game_over = False

    if mode == 'stage':
        if is_correct:
            if (user.arena_stage or 1) < 10:
                user.arena_stage = (user.arena_stage or 1) + 1
                game_message = f"[ LEVEL UP ] Tiến vào Ải {user.arena_stage}!"
            else:
                game_message = "[ PHÁ ĐẢO ] Bạn đã vượt qua Ải 10! Huyền thoại!"
                is_game_over = True
        else:
            game_message = "[ DEFEATED ] Bạn đã gục ngã! Trở lại Ải 1."
            user.arena_stage = 1
            is_game_over = True

    elif mode == 'infinity':
        if is_correct:
            game_message = f"[ KABOOM ] Chuỗi Combo: {current_gacha_streak}"
            if current_gacha_streak > (user.infinity_score or 0):
                user.infinity_score = current_gacha_streak

            achieved = check_and_unlock_achievements(user_id, 'GACHA_COMBO', current_gacha_streak)
            if achieved:
                game_message += f" | 🏆 +{len(achieved)} THÀNH TỰU!"
        else:
            game_message = f"[ GAME OVER ] Dừng lại ở điểm: {current_gacha_streak}"
            is_game_over = True

    db.session.commit()

    return jsonify({
        "correct": is_correct,
        "message": game_message,
        "new_streak": current_gacha_streak,
        "arena_stage": user.arena_stage,
        "infinity_score": user.infinity_score,
        "is_game_over": is_game_over
    }), 200


@game_bp.route('/gacha/leaderboard', methods=['GET'])
def get_leaderboard():
    top_users = User.query.order_by(User.infinity_score.desc()).limit(5).all()
    result = [{"username": u.username, "score": u.infinity_score or 0} for u in top_users]
    return jsonify({"leaderboard": result}), 200


@game_bp.route('/quests/today', methods=['GET'])
def get_daily_quests():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today).all()

    if not quests:
        # Tối ưu hóa: Thay thế ORDER BY RAND() bằng Random ID ở Python
        locked_ids = [v[0] for v in db.session.query(Vocabulary.id).filter_by(is_unlocked=False).all()]
        new_vocab_ids = random.sample(locked_ids, min(2, len(locked_ids)))
        new_vocabs = Vocabulary.query.filter(Vocabulary.id.in_(new_vocab_ids)).all() if new_vocab_ids else []

        review_ids = [v[0] for v in db.session.query(UserVocabulary.vocab_id).filter_by(
            user_id=user_id, memorization_level='DA_THUOC'
        ).all()]
        review_vocab_ids = random.sample(review_ids, min(2, len(review_ids)))
        review_vocabs = UserVocabulary.query.filter(UserVocabulary.vocab_id.in_(review_vocab_ids),
                                                    UserVocabulary.user_id == user_id).all() if review_vocab_ids else []

        for nv in new_vocabs:
            db.session.add(DailyQuest(user_id=user_id, vocab_id=nv.id, quest_type='NEW', assigned_date=today))

        for rv in review_vocabs:
            db.session.add(DailyQuest(user_id=user_id, vocab_id=rv.vocab_id, quest_type='REVIEW', assigned_date=today))

        db.session.commit()
        quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today).all()

    result = []
    for q in quests:
        v = Vocabulary.query.get(q.vocab_id)
        if v:
            result.append({
                "quest_id": q.id,
                "vocab_id": v.id,
                "word": v.word,
                "meaning": v.meaning,
                "type": q.quest_type,
                "is_completed": q.is_completed
            })

    return jsonify({"quests": result}), 200


def check_and_complete_quest(user_id, text_input):
    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today, is_completed=False).all()
    for q in quests:
        v = Vocabulary.query.get(q.vocab_id)
        if v and v.word.lower() in text_input.lower():
            q.is_completed = True
            user = User.query.get(user_id)
            user.coins += 20
            db.session.commit()
            return True, v.word
    return False, None


@game_bp.route('/exam/generate', methods=['POST'])
def generate_exam():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    now = datetime.now()
    needs_review = UserVocabulary.query.filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.next_review_time <= now
    ).all()

    review_vocab_ids = [uv.vocab_id for uv in needs_review]
    limit, exam_words = 50, []
    if review_vocab_ids:
        exam_words.extend(Vocabulary.query.filter(Vocabulary.id.in_(review_vocab_ids)).limit(limit).all())

    if len(exam_words) < limit:
        subquery = db.session.query(UserVocabulary.vocab_id).filter_by(user_id=user_id)
        new_vocabs = Vocabulary.query.filter(~Vocabulary.id.in_(subquery)).limit(limit - len(exam_words)).all()
        for nv in new_vocabs:
            db.session.add(UserVocabulary(user_id=user_id, vocab_id=nv.id, is_unlocked=True))
            exam_words.append(nv)
        db.session.commit()

    output = [{"id": w.id, "word": w.word, "meaning": w.meaning} for w in exam_words]
    random.shuffle(output)
    return jsonify({"exam": output, "count": len(output)}), 200


@game_bp.route('/exam/update_status', methods=['POST'])
def update_exam_status():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id')
    level = data.get('level')
    response_time_ms = data.get('response_time_ms', 2000.0)
    user_id = session.get('user_id')

    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
    vocab = Vocabulary.query.get(vocab_id)
    if uv and vocab:
        is_correct = (level == 'DA_THUOC')

        current_fail = uv.fail_count if uv.fail_count is not None else 0
        current_avg = uv.avg_response_time if uv.avg_response_time is not None else 0.0
        current_prev_interval = uv.previous_interval if uv.previous_interval is not None else 0.0

        if not is_correct:
            uv.fail_count = current_fail + 1
        else:
            uv.fail_count = current_fail

        time_sec = response_time_ms / 1000.0
        uv.avg_response_time = time_sec if current_avg == 0.0 else (current_avg + time_sec) / 2

        # ML Inference SRS
        next_dt, new_interval = srs_engine.predict_next_review(uv.fail_count, uv.avg_response_time,
                                                               current_prev_interval)
        uv.next_review_time = next_dt
        uv.previous_interval = new_interval
        uv.memorization_level = level

        db.session.commit()
        return jsonify({"success": True}), 200
    return jsonify({"error": "Lỗi cập nhật"}), 400


@game_bp.route('/story/archive', methods=['GET'])
def get_story_archive():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    sessions = StorySession.query.filter_by(user_id=user_id).order_by(StorySession.created_at.desc()).all()
    result = []
    for s in sessions:
        topic_title = s.topic.title if s.topic else "Không xác định"
        result.append({
            "id": s.id,
            "topic": topic_title,
            "status": s.status,
            "summary_en": s.summary_en,
            "summary_vn": s.summary_vn,
            "date": s.created_at.strftime("%Y-%m-%d")
        })
    return jsonify({"archive": result}), 200


@game_bp.route('/notifications', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(10).all()
    unread_count = sum(1 for n in notifs if not n.is_read)

    data = [{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.strftime("%d/%m %H:%M")
    } for n in notifs]

    return jsonify({"notifications": data, "unread_count": unread_count}), 200


@game_bp.route('/notifications/read', methods=['POST'])
def mark_notifications_read():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True}), 200


# =========================================================================
# PHÂN HỆ MINIGAME: ẢI GHÉP CHỮ & CÚ PHÁP (100% LOCAL-FIRST AI)
# =========================================================================

@game_bp.route('/scramble/generate', methods=['POST'])
def generate_scramble():
    """Tạo ải ghép chữ mới - 100% Local AI (< 5ms)"""
    data = request.get_json(silent=True) or {}
    vocab_id = data.get('vocab_id')
    cefr_filter = data.get('cefr')
    res = scramble_engine.generate_word_scramble(vocab_id=vocab_id, cefr_filter=cefr_filter)
    return jsonify(res), 200


@game_bp.route('/scramble/verify', methods=['POST'])
def verify_scramble():
    """Xác thực câu trả lời ghép chữ và đồng bộ vào Smart SRS"""
    data = request.get_json(silent=True) or {}
    vocab_id = data.get('vocab_id')
    user_answer = data.get('answer', '')
    response_time = float(data.get('response_time', 5.0))
    user_id = session.get('user_id')

    if not vocab_id:
        return jsonify({"error": "Thiếu ID từ vựng!"}), 400

    res = scramble_engine.verify_word_scramble(vocab_id, user_answer, response_time, user_id=user_id)
    return jsonify(res), 200


@game_bp.route('/syntax/generate', methods=['POST'])
def generate_syntax():
    """Tạo ải lắp ráp cú pháp câu - 100% Local AI"""
    data = request.get_json(silent=True) or {}
    grammar_id = data.get('grammar_id')
    res = scramble_engine.generate_syntax_scramble(grammar_id=grammar_id)
    return jsonify(res), 200


@game_bp.route('/syntax/verify', methods=['POST'])
def verify_syntax():
    """Xác thực trật tự cú pháp bằng LanguageTool cục bộ"""
    data = request.get_json(silent=True) or {}
    original = data.get('original_sentence', '')
    user_chunks = data.get('user_chunks', [])
    res = scramble_engine.verify_syntax_scramble(original, user_chunks)
    return jsonify(res), 200


# =========================================================================
# PHÂN HỆ VẬT PHẨM TRANG TRÍ & KHUNG AVATAR (COSMETICS & IDENTITY)
# =========================================================================

def ensure_default_cosmetics():
    """Khởi tạo danh mục 15 Khung Avatar và 3 Danh hiệu chiến binh mặc định"""
    items = [
        # 15 KHUNG AVATAR ĐỘNG BAO QUÁT ÔM TRỌN AVATAR
        {"name": "Khung Tiêu Chuẩn", "type": "AVATAR_FRAME", "css": "frame-default", "price": 0, "desc": "Khung viền kim loại cổ điển tối giản"},
        {"name": "Khung Băng Thanh Neon", "type": "AVATAR_FRAME", "css": "frame-neon-cyan", "price": 100, "desc": "Viền ánh sáng Cyberpunk xanh ngọc kèm tia sét phát xung"},
        {"name": "Khung Hồng Thạch Cyber", "type": "AVATAR_FRAME", "css": "frame-neon-pink", "price": 120, "desc": "Viền hồng Neon ngọt ngào với biểu tượng trái tim phát quang"},
        {"name": "Khung Hỏa Ngục Huyền Thoại", "type": "AVATAR_FRAME", "css": "frame-flame", "price": 200, "desc": "Vòng hào quang rực lửa thiêu đốt mọi câu sai ngữ pháp"},
        {"name": "Khung Hoàng Kim Đế Vương", "type": "AVATAR_FRAME", "css": "frame-gold-dragon", "price": 300, "desc": "Ánh kim long hoàng gia dành riêng cho cao thủ tiếng Anh"},
        {"name": "Khung Ma Trận Số", "type": "AVATAR_FRAME", "css": "frame-glitch-matrix", "price": 180, "desc": "Viền mã nhị phân Hacker xanh lục với linh vật Cyber"},
        {"name": "Khung Cực Quang Huyền Ảo", "type": "AVATAR_FRAME", "css": "frame-aurora", "price": 220, "desc": "Dải cực quang phương Bắc xoay vòng chuyển màu mượt mà"},
        {"name": "Khung Hư Không Vũ Trụ", "type": "AVATAR_FRAME", "css": "frame-void-galaxy", "price": 280, "desc": "Vòng xoáy tím huyền bí của bụi sao vũ trụ bao la"},
        {"name": "Khung Sấm Sét Lôi Thần", "type": "AVATAR_FRAME", "css": "frame-thunder", "price": 240, "desc": "Dòng điện cao thế vàng xanh phóng tia chớp liên tục"},
        {"name": "Khung Cyberpunk 2077 HUD", "type": "AVATAR_FRAME", "css": "frame-cyber-hud", "price": 260, "desc": "Hệ thống ngắm bắn công nghệ tương lai xoay vòng quanh avatar"},
        {"name": "Khung Băng Tuyết Vĩnh Cửu", "type": "AVATAR_FRAME", "css": "frame-frost", "price": 190, "desc": "Lớp băng giá tinh thể Bắc Cực tỏa hơi sương lạnh buốt"},
        {"name": "Khung Hào Quang Thiên Thần", "type": "AVATAR_FRAME", "css": "frame-angel-halo", "price": 350, "desc": "Vòng thánh quang thiên giới bồng bềnh che chở avatar"},
        {"name": "Khung Ác Ma Dạ Xoa", "type": "AVATAR_FRAME", "css": "frame-demon-horns", "price": 360, "desc": "Cặp sừng quỷ đỏ rực đầy uy lực và ma mị"},
        {"name": "Khung Cầu Vồng Quang Phổ", "type": "AVATAR_FRAME", "css": "frame-rainbow-chroma", "price": 400, "desc": "Dải màu RGB Chroma 360 độ xoay tít cực kỳ cuốn hút"},
        {"name": "Khung Độc Cô Cầu Bại", "type": "AVATAR_FRAME", "css": "frame-champion-crown", "price": 500, "desc": "Vương miện kim cương tối thượng khẳng định ngôi vương"},

        # DANH HIỆU CHIẾN BINH
        {"name": "Chiến Binh Cú Pháp", "type": "PLAYER_TITLE", "css": "title-syntax", "price": 80, "desc": "Danh hiệu cho người yêu thích cấu trúc ngữ pháp"},
        {"name": "Đại Đội Trưởng Chính Tả", "type": "PLAYER_TITLE", "css": "title-spelling", "price": 120, "desc": "Danh hiệu cho tay gỡ bom từ vựng siêu cấp"},
        {"name": "Kẻ Hủy Diệt Ngữ Pháp", "type": "PLAYER_TITLE", "css": "title-destroyer", "price": 200, "desc": "Danh xưng huyền thoại của bậc thầy ngôn ngữ"}
    ]

    for it in items:
        c = CosmeticItem.query.filter_by(css_class=it["css"]).first()
        if not c:
            c = CosmeticItem(name=it["name"], type=it["type"], css_class=it["css"], price_coins=it["price"], description=it["desc"])
            db.session.add(c)
    db.session.commit()


@game_bp.route('/cosmetics', methods=['GET'])
def get_cosmetics():
    """Lấy danh mục vật phẩm trong Cửa hàng Trang trí kèm trạng thái sở hữu"""
    user_id = session.get('user_id')
    ensure_default_cosmetics()

    items = CosmeticItem.query.order_by(CosmeticItem.price_coins.asc()).all()
    user_owned_map = {}

    if user_id:
        user_cos = UserCosmetic.query.filter_by(user_id=user_id).all()
        for uc in user_cos:
            user_owned_map[uc.cosmetic_id] = uc.is_equipped

    result = []
    for item in items:
        is_owned = (item.id in user_owned_map) or (item.price_coins == 0)
        is_equipped = user_owned_map.get(item.id, False)

        result.append({
            "id": item.id,
            "name": item.name,
            "type": item.type,
            "css_class": item.css_class,
            "description": item.description,
            "price_coins": item.price_coins,
            "is_owned": is_owned,
            "is_equipped": is_equipped
        })

    return jsonify({"cosmetics": result}), 200


@game_bp.route('/cosmetics/buy', methods=['POST'])
def buy_cosmetic():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')

    item = CosmeticItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Vật phẩm không tồn tại!"}), 404

    user = User.query.get(user_id)

    # Kiểm tra xem đã sở hữu chưa
    existing = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()
    if existing:
        return jsonify({"error": "Bạn đã sở hữu vật phẩm này rồi!"}), 400

    if user.coins < item.price_coins:
        return jsonify({"error": f"Không đủ Xu! Bạn cần {item.price_coins} Xu (Hiện có: {user.coins} Xu)."}), 400

    user.coins -= item.price_coins
    new_owned = UserCosmetic(user_id=user_id, cosmetic_id=item.id, is_equipped=False)
    db.session.add(new_owned)
    db.session.commit()

    return jsonify({
        "message": f"🎉 Mua thành công '{item.name}'! Vật phẩm đã vào kho đồ của bạn.",
        "new_coins": user.coins
    }), 200


@game_bp.route('/cosmetics/equip', methods=['POST'])
def equip_cosmetic():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')

    item = CosmeticItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Vật phẩm không tồn tại!"}), 404

    user = User.query.get(user_id)

    # Đảm bảo người dùng sở hữu vật phẩm này
    if item.price_coins > 0:
        owned = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()
        if not owned:
            return jsonify({"error": "Bạn chưa sở hữu vật phẩm này!"}), 403

    if item.type == 'AVATAR_FRAME':
        user.equipped_frame = item.css_class
    elif item.type == 'PLAYER_TITLE':
        user.equipped_title = item.name

    # Cập nhật cờ is_equipped trong bảng UserCosmetic
    UserCosmetic.query.filter(UserCosmetic.user_id == user_id, UserCosmetic.cosmetic.has(type=item.type)).update({"is_equipped": False}, synchronize_session=False)
    target_uc = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()
    if target_uc:
        target_uc.is_equipped = True

    db.session.commit()

    return jsonify({
        "message": f"✨ Đã trang bị {item.type.replace('_', ' ')}: '{item.name}'!",
        "equipped_frame": user.equipped_frame,
        "equipped_title": user.equipped_title
    }), 200


@game_bp.route('/cosmetics/my_inventory', methods=['GET'])
def get_my_inventory():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    owned_list = UserCosmetic.query.filter_by(user_id=user_id).all()

    items = []
    # Luôn có item default
    items.append({
        "id": 0,
        "name": "Khung Tiêu Chuẩn",
        "type": "AVATAR_FRAME",
        "css_class": "frame-default",
        "is_equipped": (getattr(user, 'equipped_frame', 'frame-default') == 'frame-default')
    })

    for uc in owned_list:
        c = uc.cosmetic
        if c:
            is_active = (user.equipped_frame == c.css_class) if c.type == 'AVATAR_FRAME' else (user.equipped_title == c.name)
            items.append({
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "css_class": c.css_class,
                "description": c.description,
                "is_equipped": is_active
            })

    return jsonify({
        "inventory": items,
        "current_frame": getattr(user, 'equipped_frame', 'frame-default'),
        "current_title": getattr(user, 'equipped_title', 'Tân Binh Ngơ Ngác')
    }), 200