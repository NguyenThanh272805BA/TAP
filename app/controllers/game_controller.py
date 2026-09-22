from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app import db
from app.models.user_vocabulary import UserVocabulary
from app.models.grammar import Grammar
from app.models.daily_quest import DailyQuest
from datetime import datetime, date, timedelta
import re
import random
import time
from app.ml_models.recommender import VocabRecommender
from app.ml_models.srs_predictor import SmartSRS
from app.models.story_session import StorySession
from app.models.story_topic import StoryTopic
from app.models.notification import Notification

from app.utils.achievement_manager import check_and_unlock_achievements
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.models.test import TestLog
from app.models.user_grammar import UserGrammar
from app.models.quest import Quest, UserQuestProgress
from app.ml_models.scramble_engine import LocalScrambleEngine
from app.ml_models.exam_engine import LocalExamEngine
from app.utils.grammar_quiz_generator import generate_grammar_collocations, generate_grammar_quiz
from app.utils.vocab_exam_service import generate_50_vocab_exam, evaluate_50_vocab_exam, apply_self_assessment_and_generate_srs_roadmap


game_bp = Blueprint('game', __name__, url_prefix='/api/game')
recommender_engine = VocabRecommender()
srs_engine = SmartSRS()
scramble_engine = LocalScrambleEngine()
exam_engine = LocalExamEngine()
_VOCAB_50_CACHE = {}


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
    vocab_id = data.get('vocab_id') or data.get('id')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401
    if not vocab_id:
        return jsonify({"error": "Thiếu mã từ vựng!"}), 400
    try:
        vocab_id = int(vocab_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Mã từ vựng không hợp lệ!"}), 400

    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({"error": "Từ vựng không tồn tại!"}), 404

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
        "id": target.id,
        "word": target.word,
        "options": options,
        "timer": timer,
        "time_limit": timer,
        "current_stage": user.arena_stage or 1,
        "stage": user.arena_stage or 1
    }), 200


@game_bp.route('/gacha/verify', methods=['POST'])
def gacha_verify():
    data = request.get_json() or {}
    vocab_id = data.get('vocab_id') or data.get('id')
    user_answer = data.get('answer') or data.get('selected', '')
    is_timeout = data.get('timeout', False) or (user_answer == "TIMEOUT_NO_ANSWER")
    mode = data.get('mode', 'stage')
    current_gacha_streak = data.get('current_streak', 0)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Phiên làm việc hết hạn!"}), 401

    if not vocab_id:
        return jsonify({"error": "Thiếu mã nhận diện từ vựng (vocab_id)!"}), 400
    try:
        vocab_id = int(vocab_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Mã từ vựng không hợp lệ!"}), 400

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

    stage_completed = (mode == 'stage' and is_correct and (user.arena_stage or 1) >= 10)

    return jsonify({
        "status": "success",
        "correct": is_correct,
        "is_correct": is_correct,
        "correct_meaning": vocab.meaning,
        "message": game_message,
        "msg": game_message,
        "new_streak": current_gacha_streak,
        "arena_stage": user.arena_stage,
        "stage": user.arena_stage,
        "infinity_score": user.infinity_score,
        "is_game_over": is_game_over,
        "game_over": is_game_over,
        "stage_completed": stage_completed
    }), 200


@game_bp.route('/gacha/leaderboard', methods=['GET'])
def get_leaderboard():
    top_users = User.query.order_by(User.infinity_score.desc()).limit(5).all()
    result = [{
        "username": u.username,
        "score": u.infinity_score or 0,
        "avatar": u.avatar or "default_avatar.png",
        "equipped_frame": getattr(u, 'equipped_frame', 'frame-default') or 'frame-default',
        "equipped_title": getattr(u, 'equipped_title', 'Tân Binh Ngơ Ngác') or 'Tân Binh Ngơ Ngác',
        "current_level": getattr(u, 'current_level', 'Tân Binh A1 (Bronze I)') or 'Tân Binh A1 (Bronze I)'
    } for u in top_users]
    return jsonify({"leaderboard": result}), 200


CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def get_cefr_policy_for_user(user) -> dict:
    """Xác định chính sách dải cấp độ từ vựng phù hợp với trình độ CEFR của người chơi."""
    raw_band = getattr(user, 'current_band', 'A1') or 'A1'
    band = raw_band.upper().strip()
    if band not in CEFR_LEVELS:
        lvl_str = str(getattr(user, 'current_level', '')).lower()
        if 'c2' in lvl_str or 'độc cô' in lvl_str:
            band = 'C2'
        elif 'c1' in lvl_str or 'kiến trúc' in lvl_str:
            band = 'C1'
        elif 'b2' in lvl_str or 'pháp sư' in lvl_str:
            band = 'B2'
        elif 'b1' in lvl_str or 'chiến binh' in lvl_str:
            band = 'B1'
        elif 'a2' in lvl_str or 'thợ săn' in lvl_str:
            band = 'A2'
        else:
            band = 'A1'

    if band == 'A1':
        return {
            'target_band': 'A1',
            'allowed_new': ['A1', 'A2'],
            'allowed_review': ['A1'],
            'max_allowed_tier_index': 1  # Tối đa A2
        }
    elif band == 'A2':
        return {
            'target_band': 'A2',
            'allowed_new': ['A2', 'B1'],
            'allowed_review': ['A1', 'A2'],
            'max_allowed_tier_index': 2  # Tối đa B1
        }
    elif band == 'B1':
        return {
            'target_band': 'B1',
            'allowed_new': ['B1', 'B2'],
            'allowed_review': ['A1', 'A2', 'B1'],
            'max_allowed_tier_index': 3  # Tối đa B2
        }
    elif band == 'B2':
        return {
            'target_band': 'B2',
            'allowed_new': ['B2', 'C1'],
            'allowed_review': ['A2', 'B1', 'B2'],
            'max_allowed_tier_index': 4  # Tối đa C1
        }
    elif band == 'C1':
        return {
            'target_band': 'C1',
            'allowed_new': ['C1', 'C2'],
            'allowed_review': ['B1', 'B2', 'C1'],
            'max_allowed_tier_index': 5  # Tối đa C2
        }
    else:  # C2
        return {
            'target_band': 'C2',
            'allowed_new': ['C2'],
            'allowed_review': ['B2', 'C1', 'C2'],
            'max_allowed_tier_index': 5
        }


@game_bp.route('/quests/today', methods=['GET'])
def get_daily_quests():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Người dùng không tồn tại!"}), 404

    policy = get_cefr_policy_for_user(user)
    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today).all()

    # Cơ chế Self-healing: Nếu phát hiện nhiệm vụ trong ngày chứa từ vựng vượt quá cấp độ cho phép
    # (ví dụ: người chơi A1 bị gán từ C2 như 'Chemical reaction'), tự động dọn dẹp để sinh lại chuẩn.
    if quests:
        needs_regeneration = False
        for q in quests:
            if not q.vocab_id:
                needs_regeneration = True
                break
            v = Vocabulary.query.get(q.vocab_id)
            if not v:
                needs_regeneration = True
                break
            v_cefr = (v.cefr_level or 'A1').upper().strip()
            v_tier_idx = CEFR_LEVELS.index(v_cefr) if v_cefr in CEFR_LEVELS else 0
            if v_tier_idx > policy['max_allowed_tier_index']:
                needs_regeneration = True
                break

        if needs_regeneration:
            for q in quests:
                db.session.delete(q)
            db.session.commit()
            quests = []

    if not quests:
        # 1. Chọn 2 từ vựng MỚI (NEW) phù hợp chính xác cấp độ CEFR của người học
        learned_ids = [uv[0] for uv in db.session.query(UserVocabulary.vocab_id).filter_by(
            user_id=user_id, memorization_level='DA_THUOC'
        ).all()]

        new_candidates = [v[0] for v in db.session.query(Vocabulary.id).filter(
            Vocabulary.cefr_level.in_(policy['allowed_new']),
            ~Vocabulary.id.in_(learned_ids) if learned_ids else True
        ).all()]

        if len(new_candidates) < 2:
            new_candidates = [v[0] for v in db.session.query(Vocabulary.id).filter(
                Vocabulary.cefr_level.in_(policy['allowed_new'])
            ).all()]

        new_vocab_ids = random.sample(new_candidates, min(2, len(new_candidates))) if new_candidates else []
        new_vocabs = Vocabulary.query.filter(Vocabulary.id.in_(new_vocab_ids)).all() if new_vocab_ids else []

        # 2. Chọn 2 từ vựng ÔN TẬP (REVIEW) phù hợp với cấp độ CEFR
        review_candidates = [
            uv[0] for uv in db.session.query(UserVocabulary.vocab_id).join(
                Vocabulary, UserVocabulary.vocab_id == Vocabulary.id
            ).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.memorization_level == 'DA_THUOC',
                Vocabulary.cefr_level.in_(policy['allowed_review'])
            ).all()
        ]

        review_vocab_ids = []
        if len(review_candidates) >= 2:
            review_vocab_ids = random.sample(review_candidates, 2)
        elif len(review_candidates) == 1:
            review_vocab_ids = list(review_candidates)
            supp_pool = [vid for vid in new_candidates if vid not in new_vocab_ids and vid not in review_vocab_ids]
            if supp_pool:
                review_vocab_ids.append(random.choice(supp_pool))
        else:
            supp_pool = [vid for vid in new_candidates if vid not in new_vocab_ids]
            if len(supp_pool) >= 2:
                review_vocab_ids = random.sample(supp_pool, 2)
            elif supp_pool:
                review_vocab_ids = list(supp_pool)

        for nv in new_vocabs:
            db.session.add(DailyQuest(user_id=user_id, vocab_id=nv.id, quest_type='NEW', assigned_date=today))

        for r_id in review_vocab_ids:
            db.session.add(DailyQuest(user_id=user_id, vocab_id=r_id, quest_type='REVIEW', assigned_date=today))

        db.session.commit()
        quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today).all()

    result = []
    for q in quests:
        if not q.vocab_id:
            continue
        v = Vocabulary.query.get(q.vocab_id)
        if v:
            result.append({
                "quest_id": q.id,
                "vocab_id": v.id,
                "word": v.word,
                "meaning": v.meaning,
                "type": q.quest_type,
                "cefr_level": v.cefr_level,
                "is_completed": q.is_completed
            })

    return jsonify({"quests": result}), 200


def check_and_complete_quest(user_id, text_input, score=None, is_valid_sentence=True):
    """
    Kiểm tra và hoàn thành nhiệm vụ hàng ngày:
    - Yêu cầu câu phải đạt điểm tối thiểu >= 5.0
    - Yêu cầu câu không phải là cụm từ rời rạc (fragment)
    - Khớp chính xác từ vựng theo ranh giới từ (word boundary)
    """
    if score is not None and score < 5.0:
        return False, None
    if not is_valid_sentence:
        return False, None

    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=user_id, assigned_date=today, is_completed=False).all()
    cleaned_input = (text_input or '').lower().strip()

    for q in quests:
        if not q.vocab_id:
            continue
        v = Vocabulary.query.get(q.vocab_id)
        if not v or not v.word:
            continue
        v_word = v.word.lower().strip()
        pattern = rf"\b{re.escape(v_word)}\b"
        if re.search(pattern, cleaned_input):
            q.is_completed = True
            user = User.query.get(user_id)
            if user:
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
    vocab_id = data.get('vocab_id') or data.get('id')
    level = data.get('level')
    response_time_ms = data.get('response_time_ms', 2000.0)
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401
    if not vocab_id:
        return jsonify({"error": "Thiếu mã từ vựng!"}), 400
    try:
        vocab_id = int(vocab_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Mã từ vựng không hợp lệ!"}), 400

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
            user_owned_map[uc.cosmetic_id] = {
                "is_equipped": uc.is_equipped,
                "quantity": uc.quantity or 0
            }

    result = []
    for item in items:
        uc_info = user_owned_map.get(item.id, {})
        is_equipped = uc_info.get("is_equipped", False)
        quantity = uc_info.get("quantity", 0)
        is_owned = (item.id in user_owned_map) or (item.price_coins == 0)

        result.append({
            "id": item.id,
            "name": item.name,
            "type": item.type,
            "css_class": item.css_class,
            "description": item.description,
            "price_coins": item.price_coins,
            "item_effect": getattr(item, 'item_effect', None),
            "is_owned": is_owned,
            "is_equipped": is_equipped,
            "quantity": quantity
        })

    return jsonify({"cosmetics": result}), 200


@game_bp.route('/cosmetics/buy', methods=['POST'])
def buy_cosmetic():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')
    if not item_id:
        return jsonify({"error": "Thiếu mã vật phẩm!"}), 400
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Mã vật phẩm không hợp lệ!"}), 400

    item = CosmeticItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Vật phẩm không tồn tại!"}), 404

    user = User.query.get(user_id)

    if user.coins < item.price_coins:
        return jsonify({"error": f"Không đủ Xu! Bạn cần {item.price_coins} Xu (Hiện có: {user.coins} Xu)."}), 400

    # Kiểm tra xem đã sở hữu chưa (đối với vật phẩm không phải tiêu hao)
    existing = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()

    if item.type == 'CONSUMABLE':
        user.coins -= item.price_coins
        if not existing:
            new_owned = UserCosmetic(user_id=user_id, cosmetic_id=item.id, is_equipped=False, quantity=1)
            db.session.add(new_owned)
            current_qty = 1
        else:
            existing.quantity = (existing.quantity or 0) + 1
            current_qty = existing.quantity

        db.session.commit()
        return jsonify({
            "message": f"🎉 Mua thành công '{item.name}'! (Số lượng trong túi: {current_qty})",
            "new_coins": user.coins
        }), 200

    if existing:
        return jsonify({"error": "Bạn đã sở hữu vật phẩm này rồi!"}), 400

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
    if not item_id:
        return jsonify({"error": "Thiếu mã vật phẩm!"}), 400
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Mã vật phẩm không hợp lệ!"}), 400

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

    default_frame = CosmeticItem.query.filter_by(css_class='frame-default').first()
    default_frame_id = default_frame.id if default_frame else 1

    items = []
    seen_ids = set()

    # Luôn có item default với ID chuẩn từ Database
    items.append({
        "id": default_frame_id,
        "name": "Khung Tiêu Chuẩn",
        "type": "AVATAR_FRAME",
        "css_class": "frame-default",
        "description": "Khung kim loại cổ điển cơ bản.",
        "is_equipped": (getattr(user, 'equipped_frame', 'frame-default') == 'frame-default')
    })
    seen_ids.add(default_frame_id)

    for uc in owned_list:
        c = uc.cosmetic
        if c and c.id not in seen_ids:
            seen_ids.add(c.id)
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


# =====================================================================
# [ PHÂN HỆ MỚI: TỔNG QUAN CHỦ ĐỀ, NGỮ PHÁP CEFR & NGÂN HÀNG ĐỀ THI LOCAL AI ]
# =====================================================================

@game_bp.route('/vocabularies/overview', methods=['GET'])
def get_vocabularies_overview():
    """Lấy dữ liệu thống kê tổng quan theo từng Topic của RIÊNG người dùng đang đăng nhập"""
    user_id = session.get('user_id')
    from collections import defaultdict

    if not user_id:
        return jsonify({"topics": [], "is_new_user": True}), 200

    # Chỉ lấy các từ vựng mà tài khoản này đã mở khóa / sở hữu trong UserVocabulary
    user_vocab_records = db.session.query(
        Vocabulary.id, Vocabulary.word, Vocabulary.meaning, Vocabulary.theme,
        Vocabulary.cefr_level, UserVocabulary.memorization_level
    ).join(
        UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
    ).filter(
        UserVocabulary.user_id == user_id
    ).all()

    if not user_vocab_records:
        suggested = [
            {"theme": "GIAO TIẾP HÀNG NGÀY", "level": "A1", "desc": "Các mẫu câu và từ vựng chào hỏi, giới thiệu bản thân."},
            {"theme": "CÔNG NGHỆ & TRÍ TUỆ NHÂN TẠO", "level": "B1", "desc": "Thuật ngữ kỷ nguyên số, máy tính và AI hiện đại."},
            {"theme": "KINH DOANH & KHỞI NGHIỆP", "level": "B2", "desc": "Đàm phán, tài chính doanh nghiệp và quản trị."},
            {"theme": "DU LỊCH & KHÁM PHÁ THẾ GIỚI", "level": "A2", "desc": "Sân bay, đặt phòng khách sạn và ẩm thực địa phương."}
        ]
        return jsonify({"topics": [], "is_new_user": True, "suggested_topics": suggested}), 200

    memorized_set = {r.id for r in user_vocab_records if r.memorization_level == 'DA_THUOC'}

    themes_map = defaultdict(list)
    for r in user_vocab_records:
        t_name = r.theme or "General"
        themes_map[t_name].append(r)

    overview = []
    for t_name, words in themes_map.items():
        total = len(words)
        memorized = sum(1 for w in words if w.id in memorized_set)
        pct = round((memorized / total) * 100, 1) if total > 0 else 0

        cefr_counts = defaultdict(int)
        for w in words:
            cefr_counts[w.cefr_level or 'A1'] += 1
        top_cefr = max(cefr_counts.items(), key=lambda x: x[1])[0] if cefr_counts else 'A1'

        sample_words = [w.word for w in words[:4]]

        overview.append({
            "theme": t_name,
            "total_words": total,
            "memorized_words": memorized,
            "progress_percent": pct,
            "representative_cefr": top_cefr,
            "sample_words": sample_words
        })

    overview.sort(key=lambda x: x["theme"])
    return jsonify({"topics": overview, "is_new_user": False}), 200


@game_bp.route('/grammar/personalized', methods=['GET'])
def get_personalized_grammar():
    """Lấy danh sách ngữ pháp phân cấp CEFR kèm trạng thái làm chủ cá nhân và gợi ý collocations"""
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    user_band = getattr(user, 'current_band', 'A1') if user else 'A1'

    user_grammars_map = {}
    if user_id:
        ugs = UserGrammar.query.filter_by(user_id=user_id).all()
        for ug in ugs:
            user_grammars_map[ug.grammar_id] = ug

    all_grammars = Grammar.query.order_by(Grammar.difficulty_score.asc()).all()
    grouped = {band: [] for band in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']}
    mastery_stats = {band: {"total": 0, "mastered": 0} for band in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']}

    for g in all_grammars:
        band = g.cefr_level if g.cefr_level in grouped else 'A1'
        ug = user_grammars_map.get(g.id)

        status = ug.mastery_status if ug else 'CHUA_HOC'
        practice_count = ug.practice_count if ug else 0
        best_score = ug.best_score if ug else 0.0
        is_recommended = (band == user_band)

        mastery_stats[band]["total"] += 1
        if status == 'DA_NAM_VUNG':
            mastery_stats[band]["mastered"] += 1

        collocations = generate_grammar_collocations(g.structure, g.explanation, g.example)

        grouped[band].append({
            "id": g.id,
            "structure": g.structure,
            "explanation": g.explanation,
            "example": g.example,
            "category": g.category or "General",
            "cefr_level": band,
            "difficulty_score": g.difficulty_score or 1,
            "mastery_status": status,
            "practice_count": practice_count,
            "best_score": best_score,
            "is_recommended": is_recommended,
            "collocations": collocations
        })

    return jsonify({
        "user_band": user_band,
        "mastery_stats": mastery_stats,
        "grammars_by_band": grouped
    }), 200



@game_bp.route('/grammar/toggle_mastery', methods=['POST'])
def toggle_grammar_mastery():
    """Cập nhật trạng thái làm chủ cấu trúc ngữ pháp (CHUA_HOC -> DANG_LUYEN -> DA_NAM_VUNG)"""
    data = request.get_json() or {}
    grammar_id = data.get('grammar_id')
    new_status = data.get('status')

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401
    if not grammar_id:
        return jsonify({"error": "Thiếu grammar_id!"}), 400

    ug = UserGrammar.query.filter_by(user_id=user_id, grammar_id=grammar_id).first()
    if not ug:
        ug = UserGrammar(user_id=user_id, grammar_id=grammar_id, mastery_status=new_status or 'DANG_LUYEN')
        db.session.add(ug)
    else:
        if new_status:
            ug.mastery_status = new_status
        else:
            cycle = {'CHUA_HOC': 'DANG_LUYEN', 'DANG_LUYEN': 'DA_NAM_VUNG', 'DA_NAM_VUNG': 'CHUA_HOC'}
            ug.mastery_status = cycle.get(ug.mastery_status, 'DANG_LUYEN')

    db.session.commit()
    return jsonify({
        "status": "success",
        "grammar_id": grammar_id,
        "mastery_status": ug.mastery_status
    }), 200


@game_bp.route('/exam/mock/generate', methods=['POST'])
def generate_mock_exam():
    """Sinh đề thi thử tự động chuẩn hóa theo Band CEFR hoặc đề toàn diện bằng AI Local 100%"""
    data = request.get_json() or {}
    band = data.get('band', 'ALL')
    num_q = int(data.get('num_questions', 10))
    user_id = session.get('user_id')

    exam_payload = exam_engine.generate_mock_exam(band=band, num_questions=num_q, user_id=user_id)

    # Lưu answer_key vào session để đối soát khi submit
    session['current_exam_id'] = exam_payload['exam_id']
    session['current_exam_answer_key'] = exam_payload['answer_key']

    safe_response = {k: v for k, v in exam_payload.items() if k != 'answer_key'}
    return jsonify(safe_response), 200


@game_bp.route('/exam/mock/submit', methods=['POST'])
def submit_mock_exam():
    """Chấm điểm bài thi thử tự động, tính subscores CEFR, áp dụng cơ chế Leo Rank khắt khe và vật phẩm hồi sinh"""
    data = request.get_json() or {}
    answers = data.get('answers', {})
    use_revive = data.get('use_revive', False)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    answer_key = session.get('current_exam_answer_key')
    if not answer_key:
        answer_key = data.get('answer_key')

    if not answer_key:
        return jsonify({"error": "Không tìm thấy dữ liệu đề thi đối soát hoặc phiên làm bài đã hết hạn."}), 400

    eval_result = exam_engine.evaluate_mock_exam(user_answers=answers, answer_key=answer_key, user_id=user_id)

    user = User.query.get(user_id)
    if user:
        coins = eval_result.get('coins_reward', 10)
        user.coins = (user.coins or 0) + coins

        # CƠ CHẾ LEO RANK KHẮT KHE (STRICT COMPETITIVE RANKING)
        final_score = eval_result.get('final_score', 0.0)
        rp_change = 0
        revive_applied = False

        if final_score < 5.0: # THI TRƯỢT
            if use_revive:
                # Kiểm tra người dùng có Bình Hồi Sinh Thần Tốc không
                revive_item = CosmeticItem.query.filter_by(item_effect='EXAM_REVIVE').first()
                if revive_item:
                    uc = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=revive_item.id).first()
                    if uc and (uc.quantity or 0) > 0:
                        uc.quantity -= 1
                        revive_applied = True
                        rp_change = 0
            if not revive_applied:
                penalty = 35 + ((user.consecutive_fails or 0) * 10) # Trượt liên tiếp bị trừ thêm điểm
                user.academic_rp = max(0, (user.academic_rp or 500) - penalty)
                rp_change = -penalty
                user.consecutive_fails = (user.consecutive_fails or 0) + 1
        elif final_score >= 8.0: # XUẤT SẮC
            bonus = 35
            user.academic_rp = (user.academic_rp or 500) + bonus
            rp_change = bonus
            user.consecutive_fails = 0
        else: # QUA MÔN
            user.academic_rp = (user.academic_rp or 500) + 15
            rp_change = 15
            user.consecutive_fails = 0

        eval_result['rp_change'] = rp_change
        eval_result['revive_applied'] = revive_applied
        eval_result['academic_rp'] = user.academic_rp

        log_feedback = f"[{eval_result['band_title']}] Điểm: {eval_result['final_score']}/10 ({eval_result['percentage']}%). RP: {('+' if rp_change >= 0 else '')}{rp_change}. {eval_result['diagnostic_advice']}"
        test_log = TestLog(
            user_id=user_id,
            score=eval_result['final_score'],
            ai_feedback=log_feedback
        )
        db.session.add(test_log)

        achieved_band = eval_result.get('estimated_band', 'A1')
        band_ranks = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        if band_ranks.get(achieved_band, 1) > band_ranks.get(getattr(user, 'current_band', 'A1'), 1) and eval_result['final_score'] >= 8.0:
            user.current_band = achieved_band
            eval_result['band_upgraded'] = True
            eval_result['new_band'] = achieved_band

        db.session.commit()

    return jsonify(eval_result), 200


@game_bp.route('/exam/history', methods=['GET'])
def get_exam_history():
    """Lấy danh sách 15 bài thi thử gần nhất của người dùng"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    logs = TestLog.query.filter_by(user_id=user_id).order_by(TestLog.created_at.desc()).limit(15).all()
    history = []
    for l in logs:
        history.append({
            "id": l.id,
            "score": l.score,
            "ai_feedback": l.ai_feedback,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else ""
        })
    return jsonify({"history": history}), 200


# =====================================================================
# [ PHÂN HỆ: BÀI THI CẤU TRÚC NGỮ PHÁP RIÊNG BIỆT (GRAMMAR QUIZ) ]
# =====================================================================

@game_bp.route('/grammar/<int:grammar_id>/quiz', methods=['GET'])
def get_grammar_quiz(grammar_id):
    """Sinh 5 câu hỏi trắc nghiệm chuyên biệt theo cấu trúc ngữ pháp"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    g = Grammar.query.get_or_404(grammar_id)
    questions = generate_grammar_quiz(g)

    # Ẩn đáp án đúng gửi về client
    client_questions = []
    answer_keys = {}
    for q in questions:
        answer_keys[str(q["id"])] = q["correct_idx"]
        client_q = dict(q)
        client_q.pop("correct_idx", None)
        client_questions.append(client_q)

    session[f'grammar_quiz_{grammar_id}'] = answer_keys

    return jsonify({
        "status": "success",
        "grammar_id": grammar_id,
        "structure": g.structure,
        "explanation": g.explanation,
        "questions": client_questions
    }), 200


@game_bp.route('/grammar/<int:grammar_id>/quiz/submit', methods=['POST'])
def submit_grammar_quiz(grammar_id):
    """Chấm điểm bài thi cấu trúc ngữ pháp và cập nhật trạng thái làm chủ"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    user_answers = data.get('answers', {})

    answer_keys = session.get(f'grammar_quiz_{grammar_id}')
    if not answer_keys:
        # Nếu session mất, sinh lại chuẩn từ object
        g = Grammar.query.get_or_404(grammar_id)
        original_q = generate_grammar_quiz(g)
        answer_keys = {str(q["id"]): q["correct_idx"] for q in original_q}

    correct_count = 0
    total = len(answer_keys)
    details = []

    opt_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    for q_id, correct_idx in answer_keys.items():
        ans = user_answers.get(q_id)
        if isinstance(ans, str) and ans.strip().upper() in opt_map:
            ans_idx = opt_map[ans.strip().upper()]
        elif ans is not None:
            try:
                ans_idx = int(ans)
            except (ValueError, TypeError):
                ans_idx = None
        else:
            ans_idx = None

        is_correct = (ans_idx is not None and ans_idx == int(correct_idx))
        if is_correct:
            correct_count += 1
        details.append({
            "question_id": q_id,
            "id": q_id,
            "user_answer": ans,
            "correct_answer": ['A', 'B', 'C', 'D'][int(correct_idx)] if int(correct_idx) < 4 else correct_idx,
            "correct_idx": correct_idx,
            "is_correct": is_correct
        })

    pct = round((correct_count / total) * 100, 1) if total > 0 else 0
    user = User.query.get(user_id)
    ug = UserGrammar.query.filter_by(user_id=user_id, grammar_id=grammar_id).first()
    if not ug:
        ug = UserGrammar(user_id=user_id, grammar_id=grammar_id)
        db.session.add(ug)

    ug.practice_count = (ug.practice_count or 0) + 1
    ug.best_score = max(ug.best_score or 0.0, pct)

    new_mastery = ug.mastery_status
    coins_earned = 10
    if pct >= 80:
        new_mastery = 'DA_NAM_VUNG'
        coins_earned = 30
    elif pct >= 50:
        new_mastery = 'DANG_LUYEN'

    ug.mastery_status = new_mastery
    if user:
        user.coins = (user.coins or 0) + coins_earned

    db.session.commit()

    return jsonify({
        "status": "success",
        "grammar_id": grammar_id,
        "score": correct_count,
        "correct_count": correct_count,
        "total": total,
        "percentage": pct,
        "passed": (pct >= 80),
        "xp_earned": 30 if pct >= 80 else 10,
        "mastery_status": new_mastery,
        "coins_earned": coins_earned,
        "details": details
    }), 200


# =====================================================================
# [ PHÂN HỆ: BÀI THI DỊCH 50 TỪ VỰNG & LỘ TRÌNH HỌC SRS CÁ NHÂN HÓA ]
# =====================================================================

@game_bp.route('/vocab/exam/generate', methods=['POST'])
def generate_vocab_50_exam():
    """Sinh bài thi trắc nghiệm 50 từ vựng kèm 4 phương án dịch nghĩa"""
    user_id = session.get('user_id')
    exam = generate_50_vocab_exam(user_id=user_id)
    if "error" in exam:
        return jsonify(exam), 400

    # Lưu bài thi vào bộ nhớ tạm server (tránh vượt giới hạn kích thước cookie 4KB của session)
    _VOCAB_50_CACHE[user_id] = exam["questions"]

    # Ẩn correct_idx khi gửi cho client
    safe_questions = []
    for q in exam["questions"]:
        safe_q = dict(q)
        safe_q.pop("correct_idx", None)
        safe_questions.append(safe_q)

    return jsonify({
        "status": "success",
        "exam_title": exam["exam_title"],
        "total_questions": exam["total_questions"],
        "questions": safe_questions
    }), 200


@game_bp.route('/vocab/exam/submit', methods=['POST'])
def submit_vocab_50_exam():
    """Chấm điểm bài thi 50 từ vựng và trả về danh sách chi tiết phục vụ màn hình Review"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    user_answers = data.get('answers', {})

    full_questions = _VOCAB_50_CACHE.get(user_id) or session.get('vocab_50_exam_full')
    if not full_questions:
        return jsonify({"error": "Phiên làm bài thi 50 từ đã hết hạn. Vui lòng tạo bài thi mới!"}), 400

    eval_result = evaluate_50_vocab_exam(full_questions, user_answers)

    # Thưởng Xu dựa trên điểm số
    user = User.query.get(user_id)
    coins_reward = eval_result["correct_count"] * 2 # Mỗi câu đúng +2 Xu
    if user:
        user.coins = (user.coins or 0) + coins_reward
        db.session.commit()

    eval_result["status"] = "success"
    eval_result["score"] = eval_result["correct_count"]
    eval_result["cefr_estimate"] = eval_result.get("estimated_cefr", "A2")
    eval_result["coins_reward"] = coins_reward
    eval_result["user_coins"] = user.coins if user else 0

    return jsonify(eval_result), 200


@game_bp.route('/vocab/exam/self_assess', methods=['POST'])
def self_assess_vocab_exam():
    """Nhận tích chọn [ĐÃ THUỘC - HƠI THUỘC - CHƯA THUỘC] và sinh Lộ trình SRS cá nhân hóa"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    assessments = data.get('assessments', [])
    if not assessments:
        return jsonify({"error": "Dữ liệu đánh giá rỗng!"}), 400

    roadmap = apply_self_assessment_and_generate_srs_roadmap(user_id, assessments)
    return jsonify({
        "status": "success",
        "message": "Đã lưu thành công đánh giá mức độ ghi nhớ và thiết lập lộ trình ôn tập cá nhân hóa!",
        "roadmap": roadmap
    }), 200


# =====================================================================
# [ PHÂN HỆ: CỬA HÀNG VẬT PHẨM TIÊU HAO & KHO ĐỒ INVENTORY ]
# =====================================================================

@game_bp.route('/consumables/my', methods=['GET'])
def get_my_consumables():
    """Lấy danh sách vật phẩm tiêu hao người dùng đang sở hữu"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    owned = db.session.query(UserCosmetic, CosmeticItem).join(
        CosmeticItem, UserCosmetic.cosmetic_id == CosmeticItem.id
    ).filter(
        UserCosmetic.user_id == user_id,
        CosmeticItem.type == 'CONSUMABLE',
        UserCosmetic.quantity > 0
    ).all()

    items = []
    for uc, ci in owned:
        items.append({
            "id": ci.id,
            "name": ci.name,
            "css_class": ci.css_class,
            "description": ci.description,
            "item_effect": ci.item_effect,
            "quantity": uc.quantity,
            "icon_preview": ci.icon_preview
        })

    return jsonify({"consumables": items}), 200


@game_bp.route('/consumables/buy', methods=['POST'])
def buy_consumable():
    """Mua vật phẩm tiêu hao bằng Xu"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    item = CosmeticItem.query.get(item_id)
    if not item or item.type != 'CONSUMABLE':
        return jsonify({"error": "Vật phẩm không hợp lệ!"}), 404

    user = User.query.get(user_id)
    total_cost = (item.price_coins or 0) * quantity
    if user.coins < total_cost:
        return jsonify({"error": f"Không đủ Xu! Cần {total_cost} Xu nhưng bạn chỉ có {user.coins} Xu."}), 400

    user.coins -= total_cost
    uc = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()
    if not uc:
        uc = UserCosmetic(user_id=user_id, cosmetic_id=item_id, quantity=quantity)
        db.session.add(uc)
    else:
        uc.quantity = (uc.quantity or 0) + quantity

    db.session.commit()
    return jsonify({
        "status": "success",
        "message": f"✨ Đã mua thành công {quantity}x '{item.name}'!",
        "new_coins": user.coins,
        "quantity": uc.quantity
    }), 200


@game_bp.route('/consumables/use', methods=['POST'])
def use_consumable():
    """Kích hoạt sử dụng một vật phẩm tiêu hao trong kho đồ"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    item_id = data.get('item_id')

    item = CosmeticItem.query.get(item_id)
    if not item or item.type != 'CONSUMABLE':
        return jsonify({"error": "Vật phẩm không hợp lệ!"}), 404

    uc = UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=item_id).first()
    if not uc or (uc.quantity or 0) <= 0:
        return jsonify({"error": "Bạn không có vật phẩm này trong kho đồ!"}), 400

    uc.quantity -= 1
    user = User.query.get(user_id)
    effect_msg = ""

    if item.item_effect == 'LUCKY_CHEST':
        import random
        rolled_coins = random.randint(250, 800)
        user.coins = (user.coins or 0) + rolled_coins
        effect_msg = f"🎁 Mở Rương Báu thành công! Bạn nhận được {rolled_coins} Xu thưởng lấp lánh!"
    elif item.item_effect == 'DOUBLE_COINS':
        user.coins = (user.coins or 0) + 150
        effect_msg = "⚡ Đã kích hoạt 2x EXP & Xu Booster (+150 Xu tức thì)!"
    elif item.item_effect == 'STREAK_SHIELD':
        effect_msg = "🛡️ Khiên Bảo Vệ Chuỗi đã được kích hoạt! Bạn được bảo hiểm 1 ngày không rớt streak."
    elif item.item_effect == 'EXAM_REVIVE':
        effect_msg = "💖 Bình Hồi Sinh đã sẵn sàng! Bạn sẽ được cứu mạng không bị trừ điểm Rank nếu rớt bài thi."
    elif item.item_effect == 'TIME_FREEZE':
        effect_msg = "⏳ Đồng Hồ Cát đã được kích hoạt! Tăng thêm 90 giây trong phòng thi kế tiếp."
    else:
        effect_msg = f"✨ Đã sử dụng thành công {item.name}!"

    db.session.commit()
    return jsonify({
        "status": "success",
        "message": effect_msg,
        "remaining_quantity": uc.quantity,
        "coins": user.coins
    }), 200


# =====================================================================
# [ PHÂN HỆ: TRUNG TÂM 500 NHIỆM VỤ CÀY XU (MEGA QUEST HUB) ]
# =====================================================================

@game_bp.route('/quests/all', methods=['GET'])
def get_all_quests():
    """Lấy danh sách 500 nhiệm vụ phân cấp kèm tiến trình cá nhân của người dùng"""
    user_id = session.get('user_id')
    category = request.args.get('category', 'ALL').upper()

    user = User.query.get(user_id) if user_id else None

    # Lấy các chỉ số động của user để kiểm tra tiến trình
    vocab_count = 0
    grammar_count = 0
    if user_id:
        vocab_count = UserVocabulary.query.filter_by(user_id=user_id, memorization_level='DA_THUOC').count()
        grammar_count = UserGrammar.query.filter_by(user_id=user_id, mastery_status='DA_NAM_VUNG').count()

    streak = getattr(user, 'streak_count', 0) or 0
    arena_wins = getattr(user, 'arena_stage', 1) or 1
    coins = getattr(user, 'coins', 0) or 0
    rp = getattr(user, 'academic_rp', 500) or 500

    # Lấy danh sách nhiệm vụ đã lưu tiến trình trong DB
    user_progress_map = {}
    if user_id:
        records = UserQuestProgress.query.filter_by(user_id=user_id).all()
        for r in records:
            user_progress_map[r.quest_id] = r

    query = Quest.query
    if category != 'ALL':
        query = query.filter_by(category=category)

    quests = query.order_by(Quest.order_index.asc()).all()

    output = []
    total_claimable = 0

    for q in quests:
        prog = user_progress_map.get(q.id)
        is_claimed = prog.is_claimed if prog else False

        # Tính toán tiến trình hiện tại dựa trên loại target
        if q.target_type == 'VOCAB_COUNT':
            cur_val = vocab_count
        elif q.target_type == 'GRAMMAR_COUNT':
            cur_val = grammar_count
        elif q.target_type == 'STREAK_DAYS':
            cur_val = streak
        elif q.target_type in ['ARENA_WINS', 'ARENA_STREAK']:
            cur_val = arena_wins
        elif q.target_type in ['EXAM_SCORE', 'RANK_CHALLENGER']:
            cur_val = rp
        elif q.target_type == 'COINS_EARNED':
            cur_val = coins
        else:
            cur_val = prog.current_count if prog else 0

        is_completed = (cur_val >= q.target_count) if not is_claimed else True
        if prog and prog.is_completed:
            is_completed = True

        if is_completed and not is_claimed:
            total_claimable += 1

        pct = min(100, round((cur_val / q.target_count) * 100, 1)) if q.target_count > 0 else 0

        output.append({
            "id": q.id,
            "quest_code": q.quest_code,
            "category": q.category,
            "title": q.title,
            "description": q.description,
            "target_type": q.target_type,
            "target_count": q.target_count,
            "current_count": min(cur_val, q.target_count),
            "progress_percent": pct,
            "reward_coins": q.reward_coins,
            "reward_exp": q.reward_exp,
            "is_completed": is_completed,
            "is_claimed": is_claimed
        })

    return jsonify({
        "status": "success",
        "category": category,
        "total_quests": len(output),
        "total_claimable": total_claimable,
        "quests": output
    }), 200


@game_bp.route('/quests/claim', methods=['POST'])
def claim_quest_reward():
    """Nhận thưởng Xu & EXP cho nhiệm vụ đã hoàn thành"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    quest_id = data.get('quest_id')
    quest = Quest.query.get_or_404(quest_id)

    user = User.query.get(user_id)

    prog = UserQuestProgress.query.filter_by(user_id=user_id, quest_id=quest_id).first()
    if prog and prog.is_claimed:
        return jsonify({"error": "Nhiệm vụ này đã được nhận thưởng rồi!"}), 400

    if not prog:
        prog = UserQuestProgress(user_id=user_id, quest_id=quest_id, is_completed=True, is_claimed=True, claimed_at=datetime.now())
        db.session.add(prog)
    else:
        prog.is_completed = True
        prog.is_claimed = True
        prog.claimed_at = datetime.now()

    reward = quest.reward_coins or 20
    user.coins = (user.coins or 0) + reward

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"🎉 Chúc mừng! Bạn nhận được +{reward} Xu từ nhiệm vụ '{quest.title}'!",
        "reward_coins": reward,
        "new_coins": user.coins,
        "quest_id": quest_id
    }), 200

