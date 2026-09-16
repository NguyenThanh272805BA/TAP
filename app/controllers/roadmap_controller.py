from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json

from app.models.user import User
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.roadmap import RoadmapMilestone, UserMilestoneProgress
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.models.notification import Notification
from app.utils.level_manager import check_and_update_level
from app.utils.achievement_manager import check_and_unlock_achievements
from app.ml_models.scramble_engine import LocalScrambleEngine
from app import db

roadmap_bp = Blueprint('roadmap', __name__, url_prefix='/api/roadmap')
scramble_engine = LocalScrambleEngine()

CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def ensure_default_milestones():
    """Tự động khởi tạo và bổ sung đầy đủ giáo trình các chặng từ A1 đến C2 (Local Database Seed)"""
    # 1. Khởi tạo ngữ pháp chuẩn từ A1 đến C2 nếu chưa có
    sample_grammars = [
        # A1
        {"structure": "S + V(s/es) + O", "explanation": "Thì Hiện tại đơn: Diễn tả thói quen hoặc sự thật hiển nhiên.", "example": "She plays tennis every Sunday."},
        {"structure": "S + is/am/are + V-ing", "explanation": "Thì Hiện tại tiếp diễn: Diễn tả hành động đang xảy ra.", "example": "They are studying in the library."},
        # A2
        {"structure": "S + V(ed)/V2 + O", "explanation": "Thì Quá khứ đơn: Diễn tả hành động đã chấm dứt trong quá khứ.", "example": "We visited London last summer."},
        {"structure": "S + have/has + V3/ed", "explanation": "Thì Hiện tại hoàn thành: Hành động bắt đầu trong quá khứ kéo dài đến hiện tại.", "example": "He has lived here for ten years."},
        # B1
        {"structure": "If + S + V(present), S + will + V", "explanation": "Câu điều kiện Loại 1: Khả năng có thật ở hiện tại/tương lai.", "example": "If it rains tomorrow, we will stay home."},
        {"structure": "S + is/are + V3/ed + by O", "explanation": "Câu bị động (Passive Voice): Nhấn mạnh vào đối tượng chịu tác động.", "example": "The novel was written by a famous author."},
        # B2
        {"structure": "If + S + V(past), S + would + V", "explanation": "Câu điều kiện Loại 2: Giả định trái ngược với thực tế ở hiện tại.", "example": "If I had a million dollars, I would travel the world."},
        {"structure": "Not only + Auxiliary + S + V, but also...", "explanation": "Đảo ngữ nâng cao: Không những... mà còn...", "example": "Not only did he pass the exam, but he also got the highest score."},
        # C1
        {"structure": "Had + S + V3, S + would have + V3", "explanation": "Đảo ngữ Điều kiện Loại 3: Giả định quá khứ trang trọng chuẩn IELTS 7.5+.", "example": "Had we anticipated these risks, we would have succeeded."},
        {"structure": "It + is/was + [focus] + that/who + ...", "explanation": "Câu chẻ nhấn mạnh (Cleft sentence) học thuật cao cấp.", "example": "It was empirical evidence that convinced the international committee."},
        # C2
        {"structure": "No sooner + had + S + V3 + than + S + V2", "explanation": "Đảo ngữ thời gian kép: Vừa mới... thì đã...", "example": "No sooner had the keynote commenced than sudden breakthroughs were announced."},
        {"structure": "Having + V3/ed, S + V + O", "explanation": "Rút gọn mệnh đề phân từ hoàn thành (Perfect Participle) đỉnh cao.", "example": "Having mastered the intricate paradigms, the scholar published groundbreaking research."}
    ]

    grammar_ids = []
    for g_data in sample_grammars:
        g = Grammar.query.filter_by(structure=g_data["structure"]).first()
        if not g:
            g = Grammar(structure=g_data["structure"], explanation=g_data["explanation"], example=g_data["example"], is_slang=False)
            db.session.add(g)
            db.session.flush()
        grammar_ids.append(g.id)

    # 2. Khởi tạo các chặng Milestone cho toàn bộ các Band: A1, A2, B1, B2, C1, C2
    milestones_data = [
        # BAND A1
        {"band": "A1", "order": 1, "title": "Khởi Đầu: Nhập Môn Hiện Tại Đơn", "desc": "Làm quen với cấu trúc câu căn bản và 5 từ vựng thường nhật.", "grammar_idx": 0, "coins": 40},
        {"band": "A1", "order": 2, "title": "Nhịp Sống: Hiện Tại Tiếp Diễn", "desc": "Mô tả các hoạt động đang diễn ra xung quanh bạn.", "grammar_idx": 1, "coins": 50},

        # BAND A2
        {"band": "A2", "order": 1, "title": "Hồi Ức: Kể Lại Chuyện Quá Khứ", "desc": "Nắm vững thì quá khứ đơn và các động từ bất quy tắc phổ biến.", "grammar_idx": 2, "coins": 60},
        {"band": "A2", "order": 2, "title": "Cột Mốc: Trải Nghiệm Hoàn Thành", "desc": "Sử dụng thì hiện tại hoàn thành để diễn tả trải nghiệm sống.", "grammar_idx": 3, "coins": 70},

        # BAND B1
        {"band": "B1", "order": 1, "title": "Dự Đoán: Điều Kiện Có Thực", "desc": "Thành thạo câu điều kiện loại 1 trong thương thuyết và đời sống.", "grammar_idx": 4, "coins": 80},
        {"band": "B1", "order": 2, "title": "Khách Quan: Cú Pháp Bị Động", "desc": "Chuyển đổi câu chủ động sang bị động trong văn cảnh học thuật.", "grammar_idx": 5, "coins": 90},

        # BAND B2
        {"band": "B2", "order": 1, "title": "Giả Định: Điều Kiện Phi Thực Tế", "desc": "Lập luận giả thuyết nâng cao với câu điều kiện loại 2.", "grammar_idx": 6, "coins": 100},
        {"band": "B2", "order": 2, "title": "Đỉnh Cao: Đảo Ngữ Nhấn Mạnh", "desc": "Cú pháp nâng cao giúp bài viết và bài nói đạt điểm C1/B2 xuất sắc.", "grammar_idx": 7, "coins": 120},

        # BAND C1
        {"band": "C1", "order": 1, "title": "Học Thuật: Đảo Ngữ Điều Kiện Loại 3", "desc": "Lập luận giả định quá khứ sắc sảo chuẩn văn phong IELTS 7.5+.", "grammar_idx": 8, "coins": 140},
        {"band": "C1", "order": 2, "title": "Sắc Bén: Câu Chẻ Nhấn Mạnh (Cleft Sentence)", "desc": "Kỹ thuật cô đọng trọng tâm câu văn của các chuyên gia ngôn ngữ.", "grammar_idx": 9, "coins": 160},

        # BAND C2
        {"band": "C2", "order": 1, "title": "Chuyên Sâu: Đảo Ngữ Thời Gian Tối Thượng", "desc": "Bậc thầy liên kết thời gian và nhịp điệu câu văn cấp độ C2.", "grammar_idx": 10, "coins": 180},
        {"band": "C2", "order": 2, "title": "Độc Cô Cầu Bại: Rút Gọn Phân Từ Học Thuật", "desc": "Đỉnh cao cú pháp rút gọn mệnh đề của các nhà nghiên cứu quốc tế.", "grammar_idx": 11, "coins": 200},
    ]

    all_vocabs = Vocabulary.query.limit(60).all()
    vocab_ids = [v.id for v in all_vocabs] if all_vocabs else []

    for idx, m_data in enumerate(milestones_data):
        existing = RoadmapMilestone.query.filter_by(band_level=m_data["band"], step_order=m_data["order"]).first()
        if existing:
            continue

        g_id = grammar_ids[m_data["grammar_idx"]] if m_data["grammar_idx"] < len(grammar_ids) else None
        # Chia nhỏ từ vựng cho từng chặng
        start_v = (idx * 3) % max(1, len(vocab_ids))
        m_vocabs = vocab_ids[start_v:start_v+4] if vocab_ids else []

        m = RoadmapMilestone(
            band_level=m_data["band"],
            step_order=m_data["order"],
            title=m_data["title"],
            description=m_data["desc"],
            grammar_id=g_id,
            target_vocab_ids=json.dumps(m_vocabs),
            pass_score=7.0,
            reward_coins=m_data["coins"]
        )
        db.session.add(m)

    db.session.commit()


@roadmap_bp.route('/current', methods=['GET'])
def get_current_roadmap():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    ensure_default_milestones()

    user = User.query.get(user_id)
    target_band = getattr(user, 'target_band', 'B2') or 'B2'
    current_band = getattr(user, 'current_band', 'A1') or 'A1'

    # Lấy các chặng theo thứ tự Band
    target_idx = CEFR_ORDER.index(target_band) if target_band in CEFR_ORDER else len(CEFR_ORDER) - 1
    allowed_bands = CEFR_ORDER[:target_idx + 1]

    milestones = RoadmapMilestone.query.filter(RoadmapMilestone.band_level.in_(allowed_bands)).order_by(
        RoadmapMilestone.band_level, RoadmapMilestone.step_order
    ).all()

    # Quét tiến độ của người dùng
    user_progress_map = {}
    progresses = UserMilestoneProgress.query.filter_by(user_id=user_id).all()
    for p in progresses:
        user_progress_map[p.milestone_id] = p

    results = []
    previous_completed = True  # Chặng đầu tiên luôn mở
    total_completed = 0

    for m in milestones:
        p = user_progress_map.get(m.id)
        is_done = p.is_completed if p else False
        best_score = p.best_score if p else 0.0

        if is_done:
            total_completed += 1

        is_unlocked = previous_completed or is_done

        # Đếm số từ vựng trong chặng
        v_ids = m.get_vocab_ids()

        results.append({
            "id": m.id,
            "band_level": m.band_level,
            "step_order": m.step_order,
            "title": m.title,
            "description": m.description,
            "is_completed": is_done,
            "is_unlocked": is_unlocked,
            "best_score": best_score,
            "pass_score": m.pass_score,
            "reward_coins": m.reward_coins,
            "vocab_count": len(v_ids),
            "has_grammar": (m.grammar_id is not None)
        })

        previous_completed = is_done

    total_count = len(results)
    progress_pct = round((total_completed / total_count * 100), 1) if total_count > 0 else 0

    return jsonify({
        "current_band": current_band,
        "target_band": target_band,
        "current_level": user.current_level,
        "equipped_frame": getattr(user, 'equipped_frame', 'frame-default'),
        "equipped_title": getattr(user, 'equipped_title', 'Tân Binh Ngơ Ngác'),
        "total_milestones": total_count,
        "completed_milestones": total_completed,
        "progress_pct": progress_pct,
        "milestones": results
    }), 200


@roadmap_bp.route('/set_target', methods=['POST'])
def set_target_band():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    new_target = data.get('target_band', '').strip().upper()

    if new_target not in CEFR_ORDER:
        return jsonify({"error": f"Band không hợp lệ! Vui lòng chọn một trong: {', '.join(CEFR_ORDER)}"}), 400

    user = User.query.get(user_id)
    user.target_band = new_target
    db.session.commit()

    return jsonify({
        "message": f"🎯 Đã cập nhật Mục Tiêu Lộ Trình của bạn thành Band: {new_target}!",
        "target_band": new_target
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>', methods=['GET'])
def get_milestone_details(milestone_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    milestone = RoadmapMilestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Không tìm thấy chặng này!"}), 404

    # 1. Lấy thông tin ngữ pháp
    grammar_info = None
    if milestone.grammar:
        grammar_info = {
            "id": milestone.grammar.id,
            "structure": milestone.grammar.structure,
            "explanation": milestone.grammar.explanation,
            "example": milestone.grammar.example
        }

    # 2. Lấy danh sách từ vựng mục tiêu
    vocab_ids = milestone.get_vocab_ids()
    vocabs = Vocabulary.query.filter(Vocabulary.id.in_(vocab_ids)).all() if vocab_ids else []
    vocab_list = [{
        "id": v.id,
        "word": v.word,
        "meaning": v.meaning,
        "cefr": v.cefr_level,
        "theme": v.theme
    } for v in vocabs]

    # 3. Sinh câu đố ghép chữ cho chặng này (Hỗ trợ đổi từ vựng tiếp theo bằng vocab_idx)
    vocab_idx = int(request.args.get('vocab_idx', 0))
    scramble_puzzle = None
    cur_vocab_idx = 0
    if vocabs:
        cur_vocab_idx = vocab_idx % len(vocabs)
        sample_v = vocabs[cur_vocab_idx]
        scramble_puzzle = scramble_engine.generate_word_scramble(vocab_id=sample_v.id)

    # 4. Sinh 1 câu đố ghép cú pháp mẫu (100% Local AI)
    syntax_puzzle = None
    if milestone.grammar:
        syntax_puzzle = scramble_engine.generate_syntax_scramble(grammar_id=milestone.grammar.id)

    return jsonify({
        "milestone": {
            "id": milestone.id,
            "band_level": milestone.band_level,
            "step_order": milestone.step_order,
            "title": milestone.title,
            "description": milestone.description,
            "pass_score": milestone.pass_score,
            "reward_coins": milestone.reward_coins
        },
        "grammar": grammar_info,
        "vocabularies": vocab_list,
        "current_vocab_idx": cur_vocab_idx,
        "total_vocabs": len(vocabs),
        "scramble_challenge": scramble_puzzle,
        "syntax_challenge": syntax_puzzle
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/submit', methods=['POST'])
def submit_milestone(milestone_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    milestone = RoadmapMilestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Không tìm thấy chặng này!"}), 404

    data = request.get_json() or {}
    score = float(data.get('score', 0.0))

    passed = (score >= milestone.pass_score)

    progress = UserMilestoneProgress.query.filter_by(user_id=user_id, milestone_id=milestone_id).first()
    if not progress:
        progress = UserMilestoneProgress(user_id=user_id, milestone_id=milestone_id, attempts=1)
        db.session.add(progress)
    else:
        progress.attempts = (progress.attempts or 0) + 1

    if score > (progress.best_score or 0.0):
        progress.best_score = score

    user = User.query.get(user_id)
    reward_msg = ""

    if passed:
        # 1. Luôn đồng bộ mở khóa toàn bộ từ vựng chặng vào UserVocabulary & Smart SRS
        vocab_ids = milestone.get_vocab_ids()
        if vocab_ids:
            from app.models.user_vocabulary import UserVocabulary
            from app.ml_models.srs_predictor import SmartSRS
            srs = SmartSRS()
            new_vocabs_count = 0
            for vid in vocab_ids:
                uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vid).first()
                if not uv:
                    next_dt, interval = srs.predict_next_review(0, 2.0, 0.0)
                    uv = UserVocabulary(
                        user_id=user_id, 
                        vocab_id=vid, 
                        is_unlocked=True,
                        memorization_level='DA_THUOC',
                        fail_count=0,
                        avg_response_time=2.0,
                        previous_interval=interval,
                        next_review_time=next_dt
                    )
                    db.session.add(uv)
                    new_vocabs_count += 1
                elif not uv.is_unlocked:
                    uv.is_unlocked = True
                    uv.memorization_level = 'DA_THUOC'
                    new_vocabs_count += 1
            if new_vocabs_count > 0:
                reward_msg += f" + Mở khóa {new_vocabs_count} từ vựng vào Smart SRS"

        # 2. Các phần thưởng chỉ cấp 1 lần đầu tiên khi vượt ải
        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.now()

            # Thưởng xu
            user.coins += milestone.reward_coins
            reward_msg = f" +{milestone.reward_coins} Xu Thưởng" + reward_msg

            # Tặng cosmetic nếu có
            if milestone.reward_cosmetic_id:
                cosmetic = CosmeticItem.query.get(milestone.reward_cosmetic_id)
                if cosmetic and not UserCosmetic.query.filter_by(user_id=user_id, cosmetic_id=cosmetic.id).first():
                    db.session.add(UserCosmetic(user_id=user_id, cosmetic_id=cosmetic.id))
                    reward_msg += f" + Nhận Khung/Danh hiệu: {cosmetic.name}!"

            # Kiểm tra thăng cấp / thăng rank học thuật
            level_up, new_rank = check_and_update_level(user_id)

            # Kiểm tra thành tựu Milestone
            total_completed = UserMilestoneProgress.query.filter_by(user_id=user_id, is_completed=True).count()
            check_and_unlock_achievements(user_id, 'MILESTONE', total_completed)

            # Gửi thông báo
            notif = Notification(
                user_id=user_id,
                title=f"VƯỢT ẢI CHẶNG: {milestone.title}",
                message=f"Chúc mừng bạn đạt {score:.1f} điểm! Đã mở khóa chặng kế tiếp.{reward_msg}",
                type="ACHIEVEMENT"
            )
            db.session.add(notif)

    db.session.commit()

    return jsonify({
        "passed": passed,
        "score": score,
        "best_score": progress.best_score,
        "is_completed": progress.is_completed,
        "message": f"🎉 CHÚC MỪNG BẠN ĐÃ QUA ẢI! {reward_msg}" if passed else "Chưa đạt điểm qua ải (Cần tối thiểu 7.0 điểm). Hãy thử lại nhé!",
        "new_coins": user.coins,
        "current_level": user.current_level,
        "current_band": getattr(user, 'current_band', 'A1')
    }), 200
