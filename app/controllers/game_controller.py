from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from app.models.user_vocabulary import UserVocabulary
from app.models.grammar import Grammar
from app.models.daily_quest import DailyQuest
from datetime import datetime, date, timedelta
import random
from app.ml_models.recommender import VocabRecommender
from app.ml_models.srs_predictor import SmartSRS
from app.models.story_session import StorySession
from app.models.story_topic import StoryTopic

# [ PHASE 3 ] Import Hệ thống Quản lý Thành tựu
from app.utils.achievement_manager import check_and_unlock_achievements

game_bp = Blueprint('game', __name__, url_prefix='/api/game')
recommender_engine = VocabRecommender()
srs_engine = SmartSRS()


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

    # [ PHASE 3 ] Kiểm tra thành tựu Chuỗi đăng nhập (STREAK)
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


# ==========================================
# GACHA ARENA (PHASE 2 & 3 - STAGES / INFINITY)
# ==========================================
@game_bp.route('/gacha/roll', methods=['POST'])
def gacha_roll():
    data = request.get_json() or {}
    mode = data.get('mode', 'stage')  # 'stage' hoặc 'infinity'

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)

    # Lọc từ vựng để test
    if mode == 'stage':
        # Chế độ vượt ải: Lấy từ vựng chưa thuộc
        unlocked_subquery = db.session.query(UserVocabulary.vocab_id).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.is_unlocked == True
        )
        locked_vocab = Vocabulary.query.filter(~Vocabulary.id.in_(unlocked_subquery)).all()
        if not locked_vocab:
            return jsonify(
                {"status": "empty", "message": "[ SYSTEM ] Tuyệt đỉnh! Bạn đã giải cứu toàn bộ kho từ vựng!"}), 200
        target = random.choice(locked_vocab)
    else:
        # Chế độ vô cực: Lấy random toàn bộ từ vựng trong hệ thống
        target = Vocabulary.query.order_by(db.func.rand()).first()

    distractors = Vocabulary.query.filter(Vocabulary.id != target.id).order_by(db.func.rand()).limit(3).all()
    options = [target.meaning] + [d.meaning for d in distractors]
    random.shuffle(options)

    # Tính toán thời gian cho phép (Timer)
    base_time = 5.0
    if mode == 'stage':
        timer = max(2.0, base_time - ((user.arena_stage or 1) * 0.3))
    else:
        timer = random.uniform(2.0, 4.0)

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
    response_time_ms = data.get('response_time_ms', 5000.0)
    mode = data.get('mode', 'stage')
    current_gacha_streak = data.get('current_streak', 0)  # Chuỗi combo gacha độc lập, không đụng tới streak điểm danh

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Phiên làm việc hết hạn!"}), 401

    user = User.query.get(user_id)
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Từ vựng không tồn tại!"}), 404

    is_correct = not is_timeout and (vocab.meaning.strip() == user_answer.strip())

    # Xử lý Logic Học Tập (Lưu lịch sử từ vựng vào SRS)
    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vocab_id).first()
    if not uv:
        uv = UserVocabulary(user_id=user_id, vocab_id=vocab_id, is_unlocked=True)
        db.session.add(uv)
    else:
        uv.is_unlocked = True

    current_fail = uv.fail_count if uv.fail_count is not None else 0
    current_avg = uv.avg_response_time if uv.avg_response_time is not None else 0.0

    if not is_correct:
        uv.fail_count = current_fail + 1
        current_gacha_streak = 0
    else:
        uv.fail_count = current_fail
        current_gacha_streak += 1

    time_sec = response_time_ms / 1000.0
    uv.avg_response_time = time_sec if current_avg == 0.0 else (current_avg + time_sec) / 2

    next_review_dt, _ = srs_engine.predict_next_review(uv.fail_count, uv.avg_response_time, len(vocab.word))
    uv.next_review_time = next_review_dt
    uv.memorization_level = 'DA_THUOC' if is_correct else 'CHUA_THUOC'

    # Xử lý Logic Game Mode (Stage / Infinity)
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

            # [ PHASE 3 ] Kiểm tra thành tựu chuỗi Gacha vô cực
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


# ==========================================
# NHIỆM VỤ HÀNG NGÀY (PHASE 2 - DAILY QUESTS)
# ==========================================
@game_bp.route('/quests/today', methods=['GET'])
def get_daily_quests():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today).all()

    # NẾU CHƯA CÓ QUEST, SINH RA 4 NHIỆM VỤ THAY VÌ 2
    if not quests:
        # Lấy 2 từ chưa mở khóa ngẫu nhiên
        new_vocabs = Vocabulary.query.filter_by(is_unlocked=False).order_by(db.func.rand()).limit(2).all()

        # Lấy 2 từ đã thuộc (để ôn tập)
        review_vocabs = UserVocabulary.query.filter_by(
            user_id=user_id,
            memorization_level='DA_THUOC'
        ).order_by(db.func.rand()).limit(2).all()

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


# ==========================================
# ML EXAM CHUNKS (SRS_PREDICTOR)
# ==========================================
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

        if not is_correct:
            uv.fail_count = current_fail + 1
        else:
            uv.fail_count = current_fail

        time_sec = response_time_ms / 1000.0
        uv.avg_response_time = time_sec if current_avg == 0.0 else (current_avg + time_sec) / 2

        next_dt, _ = srs_engine.predict_next_review(uv.fail_count, uv.avg_response_time, len(vocab.word))
        uv.next_review_time = next_dt
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