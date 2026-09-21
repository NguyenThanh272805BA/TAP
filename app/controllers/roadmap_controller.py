from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import json
import uuid
import random

from app.models.user import User
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.roadmap import RoadmapMilestone, UserMilestoneProgress
from app.models.cosmetic import CosmeticItem, UserCosmetic
from app.models.notification import Notification
from app.utils.level_manager import check_and_update_level, process_exam_result, compute_user_academic_tier
from app.ml_models.scramble_engine import LocalScrambleEngine
from app import db

roadmap_bp = Blueprint('roadmap', __name__, url_prefix='/api/roadmap')
scramble_engine = LocalScrambleEngine()

CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

GRAMMAR_CLOZE_BANK = {
    "A1": [
        {
            "prompt": "Every morning, my father _____ (drink) green tea before exercising.",
            "options": ["drinks", "is drinking", "drank", "has drunk"],
            "answer": "drinks",
            "explanation": "Chủ ngữ ngôi thứ ba số ít 'my father' và thói quen 'Every morning' dùng thì Hiện tại đơn V(s/es)."
        },
        {
            "prompt": "Water _____ (freeze) into ice when the temperature drops below 0°C.",
            "options": ["freezes", "freezing", "froze", "will freeze"],
            "answer": "freezes",
            "explanation": "Quy luật vật lý, chân lý hiển nhiên dùng thì Hiện tại đơn."
        },
        {
            "prompt": "Listen! The lead vocalist _____ (sing) that melodic ballad right now.",
            "options": ["is singing", "sings", "sang", "has sung"],
            "answer": "is singing",
            "explanation": "Dấu hiệu 'Listen!' và 'right now' thể hiện hành động đang diễn ra tại thời điểm nói -> Hiện tại tiếp diễn."
        },
        {
            "prompt": "The software engineers _____ (develop) a modern interactive feature at this moment.",
            "options": ["are developing", "develop", "developed", "develops"],
            "answer": "are developing",
            "explanation": "Chủ ngữ số nhiều 'engineers' và 'at this moment' dùng Hiện tại tiếp diễn: are + V-ing."
        }
    ],
    "A2": [
        {
            "prompt": "Two years ago, the academy _____ (organize) an international conference in Tokyo.",
            "options": ["organized", "organizes", "has organized", "was organizing"],
            "answer": "organized",
            "explanation": "Thời điểm cụ thể chấm dứt trong quá khứ 'Two years ago' dùng thì Quá khứ đơn V(ed)."
        },
        {
            "prompt": "Yesterday, she _____ (write) a comprehensive report regarding the quarterly metrics.",
            "options": ["wrote", "writes", "has written", "written"],
            "answer": "wrote",
            "explanation": "Động từ bất quy tắc 'write' ở thì Quá khứ đơn là 'wrote'."
        },
        {
            "prompt": "Dr. Miller _____ (reside) in this metropolis since his graduation in 2018.",
            "options": ["has resided", "resided", "is residing", "resides"],
            "answer": "has resided",
            "explanation": "Hành động bắt đầu trong quá khứ và vẫn kéo dài đến hiện tại với mốc 'since 2018' dùng Hiện tại hoàn thành."
        },
        {
            "prompt": "We _____ (already / complete) three crucial milestones of the syllabus.",
            "options": ["have already completed", "already completed", "are already completing", "completed already"],
            "answer": "have already completed",
            "explanation": "Trạng từ 'already' kết hợp với trải nghiệm đạt được dùng Hiện tại hoàn thành: have/has + V3/ed."
        }
    ],
    "B1": [
        {
            "prompt": "If the government _____ (invest) in renewable energy, carbon emissions will decline.",
            "options": ["invests", "will invest", "invested", "would invest"],
            "answer": "invests",
            "explanation": "Mệnh đề 'If' trong câu điều kiện loại 1 chia thì Hiện tại đơn: If + S + V(s/es)."
        },
        {
            "prompt": "Unless you _____ (submit) the application before Friday, the scholarship will be revoked.",
            "options": ["submit", "will submit", "submitted", "are submitting"],
            "answer": "submit",
            "explanation": "'Unless' (= If not) trong câu điều kiện có thật chia ở thì Hiện tại đơn."
        },
        {
            "prompt": "The ancient manuscript _____ (discover) by archaeologists in a secluded cavern.",
            "options": ["was discovered", "discovered", "is discovered", "has discovered"],
            "answer": "was discovered",
            "explanation": "Câu bị động quá khứ đơn: was/were + V3/ed (bản thảo được phát hiện)."
        },
        {
            "prompt": "All strategic proposals _____ (evaluate) strictly by the examination board next week.",
            "options": ["will be evaluated", "evaluated", "are evaluated", "have evaluated"],
            "answer": "will be evaluated",
            "explanation": "Câu bị động tương lai đơn: will be + V3/ed."
        }
    ],
    "B2": [
        {
            "prompt": "If we _____ (possess) sufficient computational capacity, we would simulate the climate model.",
            "options": ["possessed", "possess", "had possessed", "would possess"],
            "answer": "possessed",
            "explanation": "Câu điều kiện loại 2 giả định trái ngược với hiện tại: If + S + V2/ed, S + would + V."
        },
        {
            "prompt": "If the policy _____ (be) implemented fairly, citizens would experience better services.",
            "options": ["were", "is", "will be", "would be"],
            "answer": "were",
            "explanation": "Trong câu điều kiện loại 2 trang trọng, to be chia 'were' cho mọi chủ ngữ."
        },
        {
            "prompt": "Not only _____ the national robotics championship, but they also patented their invention.",
            "options": ["did they win", "they won", "they did win", "won they"],
            "answer": "did they win",
            "explanation": "Đảo ngữ với 'Not only' đứng đầu câu: Not only + Auxiliary (did) + S + V."
        },
        {
            "prompt": "Hardly _____ (the lecture / conclude) when the enthusiastic debate erupted.",
            "options": ["had the lecture concluded", "the lecture had concluded", "did the lecture conclude", "concluded the lecture"],
            "answer": "had the lecture concluded",
            "explanation": "Cấu trúc đảo ngữ phủ định: Hardly had + S + V3/ed + when + S + V2."
        }
    ],
    "C1": [
        {
            "prompt": "_____ they accounted for the volatility of exchange rates, the portfolio would have survived.",
            "options": ["Had", "If had", "Were", "Did"],
            "answer": "Had",
            "explanation": "Đảo ngữ câu điều kiện loại 3 nâng cao: Had + S + V3/ed, S + would have + V3."
        },
        {
            "prompt": "Were the delegates _____ (compromise) on trade barriers, multilateral consensus could emerge.",
            "options": ["to compromise", "compromising", "compromised", "compromise"],
            "answer": "to compromise",
            "explanation": "Đảo ngữ câu điều kiện loại 2 học thuật: Were + S + to-V."
        },
        {
            "prompt": "It was precisely due to empirical evidence _____ the scientific committee ratified the doctrine.",
            "options": ["that", "which", "whom", "where"],
            "answer": "that",
            "explanation": "Cấu trúc câu chẻ nhấn mạnh (Cleft sentence): It is/was + [thành phần nhấn mạnh] + that..."
        },
        {
            "prompt": "It is the relentless pursuit of innovation _____ distinguishes pioneer tech enterprises.",
            "options": ["that", "which", "who", "whom"],
            "answer": "that",
            "explanation": "Câu chẻ học thuật IELTS 8.0+: It is + [S] + that + V."
        }
    ],
    "C2": [
        {
            "prompt": "No sooner had the keynote address commenced _____ critical breakthroughs were proclaimed.",
            "options": ["than", "when", "then", "that"],
            "answer": "than",
            "explanation": "Cấu trúc đảo ngữ thời gian kép cấp độ C2: No sooner had + S + V3 + than + S + V2."
        },
        {
            "prompt": "Scarcely _____ the symposium when global media outlets published breaking headlines.",
            "options": ["had the delegates opened", "the delegates opened", "did the delegates open", "delegates had opened"],
            "answer": "had the delegates opened",
            "explanation": "Cấu trúc đảo ngữ: Scarcely had + S + V3 + when + S + V2."
        },
        {
            "prompt": "Having _____ the labyrinth of legal paradigms, the jurist drafted revolutionary legislation.",
            "options": ["mastered", "mastering", "master", "masters"],
            "answer": "mastered",
            "explanation": "Rút gọn mệnh đề phân từ hoàn thành (Perfect Participle): Having + V3/ed biểu thị hành động đã hoàn tất trước."
        },
        {
            "prompt": "Having _____ comprehensive field trials, the team published peer-reviewed findings.",
            "options": ["concluded", "concluding", "conclude", "concludes"],
            "answer": "concluded",
            "explanation": "Cấu trúc Perfect Participle: Having + V3/ed."
        }
    ]
}


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
        "academic_rp": user.academic_rp if user.academic_rp is not None else 500,
        "consecutive_fails": user.consecutive_fails or 0,
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

    user = User.query.get(user_id)

    # 1. Kiểm tra Cooldown thi lại
    cooldown_remaining = 0
    if user.last_exam_fail_time:
        elapsed = (datetime.now() - user.last_exam_fail_time).total_seconds()
        if elapsed < 45:
            cooldown_remaining = max(0, int(45 - elapsed))

    # 2. Lấy thông tin ngữ pháp
    grammar_info = None
    if milestone.grammar:
        grammar_info = {
            "id": milestone.grammar.id,
            "structure": milestone.grammar.structure,
            "explanation": milestone.grammar.explanation,
            "example": milestone.grammar.example
        }

    # 3. Lấy danh sách từ vựng mục tiêu
    vocab_ids = milestone.get_vocab_ids()
    vocabs = Vocabulary.query.filter(Vocabulary.id.in_(vocab_ids)).all() if vocab_ids else []
    vocab_list = [{
        "id": v.id,
        "word": v.word,
        "meaning": v.meaning,
        "cefr": v.cefr_level,
        "theme": v.theme
    } for v in vocabs]

    # 4. Sinh câu đố ghép chữ và cú pháp mẫu tham khảo cho phần Học tập
    vocab_idx = int(request.args.get('vocab_idx', 0))
    scramble_puzzle = None
    cur_vocab_idx = 0
    if vocabs:
        cur_vocab_idx = vocab_idx % len(vocabs)
        sample_v = vocabs[cur_vocab_idx]
        scramble_puzzle = scramble_engine.generate_word_scramble(vocab_id=sample_v.id)

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
        "user_status": {
            "academic_rp": user.academic_rp if user.academic_rp is not None else 500,
            "current_rank": user.current_level,
            "current_band": getattr(user, 'current_band', 'A1'),
            "consecutive_fails": user.consecutive_fails or 0,
            "cooldown_remaining": cooldown_remaining,
            "coins": user.coins
        },
        "grammar": grammar_info,
        "vocabularies": vocab_list,
        "current_vocab_idx": cur_vocab_idx,
        "total_vocabs": len(vocabs),
        "scramble_challenge": scramble_puzzle,
        "syntax_challenge": syntax_puzzle
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/bypass_cooldown', methods=['POST'])
def bypass_cooldown(milestone_id):
    """Chi trả 20 Xu lệ phí thi để được thi lại ngay lập tức (Bỏ qua 45s Cooldown)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Người dùng không tồn tại!"}), 404

    if user.coins < 20:
        return jsonify({"error": "Bạn không đủ 20 Xu để nộp lệ phí thi lại ngay!"}), 400

    user.coins -= 20
    user.last_exam_fail_time = None
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Đã thanh toán 20 Xu lệ phí thi! Bạn có thể vào phòng thi chặng ngay lập tức.",
        "new_coins": user.coins
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/exam', methods=['GET'])
def generate_milestone_exam(milestone_id):
    """
    SINH ĐỀ THI CHẶNG NGẪU NHIÊN 4 PHẦN THI CHUYÊN SÂU (ANTI-CHEAT / ANTI-EXPLOIT)
    Bảo mật tuyệt đối: KHÔNG gửi đáp án đúng về Client!
    Toàn bộ đáp án chuẩn được lưu trong Server Session gắn với exam_token.
    Mỗi lần làm lại sẽ sinh ra bộ câu hỏi hoàn toàn mới.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    milestone = RoadmapMilestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Không tìm thấy chặng này!"}), 404

    # Kiểm tra Cooldown nếu thi trượt gần đây
    if user.last_exam_fail_time:
        elapsed = (datetime.now() - user.last_exam_fail_time).total_seconds()
        if elapsed < 45:
            remaining = max(1, int(45 - elapsed))
            return jsonify({
                "status": "cooldown",
                "cooldown_remaining": remaining,
                "message": f"Bạn đang trong thời gian tĩnh tâm ôn bài ({remaining}s). Hãy chờ hết giờ hoặc dùng 20 Xu để thi lại ngay!"
            }), 403

    vocab_ids = milestone.get_vocab_ids()
    milestone_vocabs = Vocabulary.query.filter(Vocabulary.id.in_(vocab_ids)).all() if vocab_ids else []
    
    # Nếu chặng có ít hơn 3 từ, lấy thêm từ cùng Band
    if len(milestone_vocabs) < 4:
        band_vocabs = Vocabulary.query.filter_by(cefr_level=milestone.band_level).limit(10).all()
        for bv in band_vocabs:
            if bv.id not in [v.id for v in milestone_vocabs]:
                milestone_vocabs.append(bv)

    if not milestone_vocabs:
        milestone_vocabs = Vocabulary.query.limit(8).all()

    all_vocab_count = Vocabulary.query.count()

    # ----------------------------------------------------
    # PHẦN 1: NHẬN DIỆN TỪ VỰNG (VOCABULARY MCQ - 3 CÂU)
    # ----------------------------------------------------
    mcq_questions = []
    mcq_answer_key = {}
    chosen_mcq_vocabs = random.sample(milestone_vocabs, min(3, len(milestone_vocabs)))

    for idx, v in enumerate(chosen_mcq_vocabs):
        q_id = f"mcq_{idx}"
        # Lấy 3 distractors ngẫu nhiên từ kho từ điển
        distractors = []
        attempts = 0
        while len(distractors) < 3 and attempts < 20:
            rand_off = random.randint(0, max(0, all_vocab_count - 1))
            cand = Vocabulary.query.offset(rand_off).first()
            if cand and cand.id != v.id and cand.meaning != v.meaning and cand.meaning not in distractors:
                distractors.append(cand.meaning)
            attempts += 1
        
        # Fallback distractor nếu kho từ ít
        fallback_meanings = ["khái niệm trừu tượng", "sự phát triển ổn định", "phân tích học thuật", "nghiên cứu thực nghiệm"]
        for fm in fallback_meanings:
            if len(distractors) < 3 and fm != v.meaning and fm not in distractors:
                distractors.append(fm)

        options = [v.meaning] + distractors[:3]
        random.shuffle(options)

        mcq_questions.append({
            "id": q_id,
            "word": v.word,
            "cefr": v.cefr_level or milestone.band_level,
            "options": options
        })
        mcq_answer_key[q_id] = {
            "correct_answer": v.meaning,
            "word": v.word,
            "explanation": f"Từ vựng '{v.word}' ({v.cefr_level or milestone.band_level}) có nghĩa chính xác là: '{v.meaning}'."
        }

    # ----------------------------------------------------
    # PHẦN 2: GỠ BOM KÝ TỰ (WORD SCRAMBLE - 2 CÂU)
    # ----------------------------------------------------
    scramble_questions = []
    scramble_answer_key = {}
    remaining_vocabs = [v for v in milestone_vocabs if v not in chosen_mcq_vocabs]
    if len(remaining_vocabs) < 2:
        remaining_vocabs = milestone_vocabs

    chosen_scramble = random.sample(remaining_vocabs, min(2, len(remaining_vocabs)))
    for idx, v in enumerate(chosen_scramble):
        q_id = f"scramble_{idx}"
        scramble_data = scramble_engine.generate_word_scramble(vocab_id=v.id)
        scramble_questions.append({
            "id": q_id,
            "meaning": v.meaning,
            "cefr": v.cefr_level or milestone.band_level,
            "shuffled_letters": scramble_data["shuffled_letters"],
            "length": len(scramble_data["shuffled_letters"])
        })
        clean_target = "".join([c for c in v.word.strip().upper() if c.isalpha()])
        scramble_answer_key[q_id] = {
            "correct_answer": clean_target,
            "word": v.word,
            "explanation": f"Từ ghép chuẩn xác là '{v.word}' mang nghĩa '{v.meaning}'."
        }

    # ----------------------------------------------------
    # PHẦN 3: LẮP RÁP CÚ PHÁP CÂU (SYNTAX ASSEMBLY - 1 CÂU)
    # ----------------------------------------------------
    syntax_q_id = "syntax_0"
    syntax_data = scramble_engine.generate_syntax_scramble(grammar_id=milestone.grammar_id)
    syntax_question = {
        "id": syntax_q_id,
        "structure": syntax_data["structure"],
        "explanation": syntax_data["explanation"],
        "shuffled_chunks": syntax_data["shuffled_chunks"],
        "chunk_count": len(syntax_data["shuffled_chunks"])
    }
    syntax_answer_key = {
        syntax_q_id: {
            "original_sentence": syntax_data["original_sentence"],
            "explanation": f"Trật tự câu chuẩn ngữ pháp: \"{syntax_data['original_sentence']}\" ({syntax_data['structure']})."
        }
    }

    # ----------------------------------------------------
    # PHẦN 4: VẬN DỤNG NGỮ PHÁP NGỮ CẢNH (CLOZE TEST - 2 CÂU)
    # ----------------------------------------------------
    cloze_questions = []
    cloze_answer_key = {}
    cloze_pool = GRAMMAR_CLOZE_BANK.get(milestone.band_level, GRAMMAR_CLOZE_BANK["B1"])
    chosen_cloze = random.sample(cloze_pool, min(2, len(cloze_pool)))

    for idx, item in enumerate(chosen_cloze):
        q_id = f"cloze_{idx}"
        shuffled_opts = item["options"].copy()
        random.shuffle(shuffled_opts)
        cloze_questions.append({
            "id": q_id,
            "prompt": item["prompt"],
            "options": shuffled_opts
        })
        cloze_answer_key[q_id] = {
            "correct_answer": item["answer"],
            "explanation": item["explanation"],
            "prompt": item["prompt"]
        }

    # Sinh mã phiên thi ngẫu nhiên (Session Exam Token)
    exam_token = str(uuid.uuid4())

    if 'active_exams' not in session:
        session['active_exams'] = {}

    session['active_exams'][str(milestone_id)] = {
        "exam_token": exam_token,
        "milestone_id": milestone_id,
        "created_at": datetime.now().isoformat(),
        "keys": {
            "mcq": mcq_answer_key,
            "scramble": scramble_answer_key,
            "syntax": syntax_answer_key,
            "cloze": cloze_answer_key
        }
    }
    session.modified = True

    return jsonify({
        "status": "success",
        "exam_token": exam_token,
        "milestone_id": milestone.id,
        "milestone_title": milestone.title,
        "band_level": milestone.band_level,
        "time_limit_sec": 420,  # 7 phút đếm ngược
        "sections": {
            "vocab_mcq": mcq_questions,
            "word_scramble": scramble_questions,
            "syntax": syntax_question,
            "grammar_cloze": cloze_questions
        }
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/submit_exam', methods=['POST'])
def submit_milestone_exam(milestone_id):
    """
    CHẤM ĐIỂM BÀI THI CHẶNG KHẮC NGHIỆT (CHỐNG BUG LEO RANK & TIẾT LỘ ĐÁP ÁN ĐẦY ĐỦ)
    1. Kiểm tra đối soát bảo mật với Session Exam Token.
    2. Chấm độc lập 4 phần thi, kiểm tra Quy tắc Điểm Liệt (< 5.0/10 ở bất kỳ phần nào -> TRƯỢT).
    3. Cập nhật Rank RP, giáng hạng nếu RP tụt, khóa cooldown nếu trượt.
    4. Trả về báo cáo phân tích toàn diện kèm giải thích từng câu.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    submitted_token = data.get('exam_token')
    is_abandoned = data.get('is_abandoned', False)
    user_answers = data.get('answers', {})

    active_exams = session.get('active_exams', {})
    exam_session = active_exams.get(str(milestone_id))

    if not exam_session or exam_session.get('exam_token') != submitted_token:
        # Nếu bài thi bỏ cuộc nhưng phiên hết hạn vẫn trừ điểm kỷ luật
        if is_abandoned:
            res = process_exam_result(user_id, milestone_id, 0.0, {
                "vocab_mcq": 0.0, "word_scramble": 0.0, "syntax": 0.0, "grammar_cloze": 0.0
            }, is_abandoned=True)
            return jsonify({"status": "abandoned", "result": res}), 200

        return jsonify({"error": "Phiên làm bài thi không hợp lệ hoặc đã nộp trước đó! Vui lòng làm lại đề mới."}), 400

    keys = exam_session.get('keys', {})
    mcq_keys = keys.get('mcq', {})
    scramble_keys = keys.get('scramble', {})
    syntax_keys = keys.get('syntax', {})
    cloze_keys = keys.get('cloze', {})

    # ----------------------------------------------------
    # CHẤM ĐIỂM TỪNG PHẦN THI
    # ----------------------------------------------------
    detailed_review = []

    # 1. Chấm Phần 1: Vocab MCQ
    user_mcq = user_answers.get('vocab_mcq', {})
    mcq_correct = 0
    for q_id, q_info in mcq_keys.items():
        u_ans = user_mcq.get(q_id, '').strip()
        c_ans = q_info['correct_answer'].strip()
        is_cor = (u_ans.lower() == c_ans.lower())
        if is_cor:
            mcq_correct += 1
        detailed_review.append({
            "section": "1. Nhận Diện Từ Vựng (MCQ)",
            "question": f"Nghĩa chính xác của từ: '{q_info['word']}'",
            "user_answer": u_ans or "(Bỏ trống)",
            "correct_answer": c_ans,
            "is_correct": is_cor,
            "explanation": q_info["explanation"]
        })
    score_mcq = round((mcq_correct / max(1, len(mcq_keys))) * 10.0, 1)

    # 2. Chấm Phần 2: Word Scramble
    user_scramble = user_answers.get('word_scramble', {})
    scramble_correct = 0
    for q_id, q_info in scramble_keys.items():
        u_ans = "".join([c for c in user_scramble.get(q_id, '').strip().upper() if c.isalpha()])
        c_ans = q_info['correct_answer']
        is_cor = (u_ans == c_ans)
        if is_cor:
            scramble_correct += 1
        detailed_review.append({
            "section": "2. Gỡ Bom Ký Tự (Scramble)",
            "question": f"Từ vựng mang nghĩa: '{q_info.get('explanation', '')}'",
            "user_answer": u_ans or "(Bỏ trống)",
            "correct_answer": c_ans,
            "is_correct": is_cor,
            "explanation": q_info["explanation"]
        })
    score_scramble = round((scramble_correct / max(1, len(scramble_keys))) * 10.0, 1)

    # 3. Chấm Phần 3: Syntax Assembly
    user_syntax_chunks = user_answers.get('syntax', {}).get('syntax_0', [])
    syntax_info = syntax_keys.get('syntax_0', {})
    orig_sentence = syntax_info.get('original_sentence', '')
    syntax_res = scramble_engine.verify_syntax_scramble(orig_sentence, user_syntax_chunks)
    score_syntax = float(syntax_res.get('score', 0.0))
    detailed_review.append({
        "section": "3. Lắp Ráp Cú Pháp (Syntax)",
        "question": f"Sắp xếp khối từ thành câu chuẩn ngữ pháp",
        "user_answer": " ".join(user_syntax_chunks) if user_syntax_chunks else "(Bỏ trống)",
        "correct_answer": orig_sentence,
        "is_correct": syntax_res.get('is_correct', False),
        "explanation": syntax_info.get('explanation', '')
    })

    # 4. Chấm Phần 4: Grammar Cloze
    user_cloze = user_answers.get('grammar_cloze', {})
    cloze_correct = 0
    for q_id, q_info in cloze_keys.items():
        u_ans = user_cloze.get(q_id, '').strip()
        c_ans = q_info['correct_answer'].strip()
        is_cor = (u_ans.lower() == c_ans.lower())
        if is_cor:
            cloze_correct += 1
        detailed_review.append({
            "section": "4. Vận Dụng Ngữ Pháp (Cloze)",
            "question": q_info.get('prompt', ''),
            "user_answer": u_ans or "(Bỏ trống)",
            "correct_answer": c_ans,
            "is_correct": is_cor,
            "explanation": q_info["explanation"]
        })
    score_cloze = round((cloze_correct / max(1, len(cloze_keys))) * 10.0, 1)

    # Tổng điểm trung bình của cả 4 phần thi
    total_exam_score = round(
        (score_mcq * 0.25) + (score_scramble * 0.25) + (score_syntax * 0.25) + (score_cloze * 0.25), 1
    )

    section_scores = {
        "vocab_mcq": score_mcq,
        "word_scramble": score_scramble,
        "syntax": score_syntax,
        "grammar_cloze": score_cloze
    }

    # Áp dụng bộ não quản lý Rank học thuật khắc nghiệt
    result = process_exam_result(
        user_id=user_id,
        milestone_id=milestone_id,
        exam_score=total_exam_score,
        section_scores=section_scores,
        is_abandoned=is_abandoned
    )

    # Nếu đỗ: Tự động mở khóa từ vựng vào Smart SRS & gửi thông báo
    milestone = RoadmapMilestone.query.get(milestone_id)
    if result["passed"]:
        vocab_ids = milestone.get_vocab_ids()
        if vocab_ids:
            from app.models.user_vocabulary import UserVocabulary
            from app.ml_models.srs_predictor import SmartSRS
            srs = SmartSRS()
            for vid in vocab_ids:
                uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=vid).first()
                if not uv:
                    next_dt, interval = srs.predict_next_review(0, 2.0, 0.0)
                    uv = UserVocabulary(
                        user_id=user_id, vocab_id=vid, is_unlocked=True,
                        memorization_level='DA_THUOC', fail_count=0, avg_response_time=2.0,
                        previous_interval=interval, next_review_time=next_dt
                    )
                    db.session.add(uv)
                elif not uv.is_unlocked:
                    uv.is_unlocked = True
                    uv.memorization_level = 'DA_THUOC'

        # Gửi thông báo vinh danh
        notif = Notification(
            user_id=user_id,
            title=f"🏆 VƯỢT ẢI THÀNH CÔNG: {milestone.title}",
            message=f"Đạt {total_exam_score:.1f}/10.0! Nhận +{result['rp_change']} RP và +{result['reward_coins']} Xu.",
            type="ACHIEVEMENT"
        )
        db.session.add(notif)
        db.session.commit()

    # Nếu thi trượt: Định vị phần thi có điểm số thấp nhất để kích hoạt Trạm Vi Học Bù Lỗ Hổng
    if not result["passed"]:
        from app.utils.level_manager import SECTION_NAMES
        weakest_section_key = min(section_scores, key=section_scores.get)
        result["weakest_section"] = {
            "key": weakest_section_key,
            "name": SECTION_NAMES.get(weakest_section_key, weakest_section_key),
            "score": section_scores[weakest_section_key]
        }

    # Xóa token phiên thi vừa nộp để chống lạm dụng nộp nhiều lần
    active_exams.pop(str(milestone_id), None)
    session['active_exams'] = active_exams
    session.modified = True

    return jsonify({
        "status": "success",
        "result": result,
        "detailed_review": detailed_review
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/submit', methods=['POST'])
def submit_milestone(milestone_id):
    """Giữ endpoint tương thích ngược"""
    data = request.get_json() or {}
    score = float(data.get('score', 0.0))
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    section_scores = {
        "vocab_mcq": score,
        "word_scramble": score,
        "syntax": score,
        "grammar_cloze": score
    }
    res = process_exam_result(user_id, milestone_id, score, section_scores)
    user = User.query.get(user_id)
    return jsonify({
        "passed": res["passed"],
        "score": score,
        "best_score": res["best_score"],
        "is_completed": res["is_completed"],
        "message": f"🎉 CHÚC MỪNG BẠN ĐÃ QUA ẢI! (+{res['rp_change']} RP)" if res["passed"] else res.get("disqualified_reason", "Chưa đạt điểm qua ải!"),
        "new_coins": user.coins,
        "current_level": user.current_level,
        "current_band": getattr(user, 'current_band', 'A1'),
        "academic_rp": user.academic_rp
    }), 200


# =========================================================================
# PHÂN HỆ: CƠ CHẾ VI HỌC BÙ LỖ HỔNG (ADAPTIVE MICRO-LESSONS & DRILLS)
# =========================================================================

ADAPTIVE_MICRO_LESSONS = {
    ("grammar_cloze", "A1"): {
        "title": "⚡ BÍ KÍP 30S: PHÂN BIỆT HIỆN TẠI ĐƠN & HIỆN TẠI TIẾP DIỄN",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• Hiện tại đơn (V/Vs-es): Diễn tả thói quen, chân lý (dấu hiệu: every day, always, usually).\n• Hiện tại tiếp diễn (am/is/are + V-ing): Diễn tả hành động đang diễn ra tại thời điểm nói (dấu hiệu: now, at present, Look!, Listen!).",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Các động từ chỉ cảm xúc, nhận thức (know, like, want, understand, believe) KHÔNG BAO GIỜ chia ở thì tiếp diễn!",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Listen! The school choir _____ (perform) a traditional anthem in the hall.",
                "options": ["performs", "is performing", "performed", "has performed"],
                "answer": "is performing",
                "explanation": "Dấu hiệu 'Listen!' báo hiệu hành động đang diễn ra ngay lúc nói -> Hiện tại tiếp diễn: is performing."
            },
            {
                "id": "drill_2",
                "prompt": "She _____ (understand) the core principle of physics very well.",
                "options": ["is understanding", "understands", "understand", "are understanding"],
                "answer": "understands",
                "explanation": "'Understand' là động từ tri giác/nhận thức, không dùng thì tiếp diễn -> Dùng Hiện tại đơn: understands."
            },
            {
                "id": "drill_3",
                "prompt": "The sun always _____ (rise) in the east and sets in the west.",
                "options": ["rises", "is rising", "rose", "has risen"],
                "answer": "rises",
                "explanation": "Chân lý hiển nhiên của tự nhiên dùng thì Hiện tại đơn: rises."
            }
        ]
    },
    ("grammar_cloze", "A2"): {
        "title": "⚡ BÍ KÍP 30S: QUÁ KHỨ ĐƠN VS HIỆN TẠI HOÀN THÀNH",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• Quá khứ đơn (V2/ed): Mốc thời gian đã chấm dứt hoàn toàn trong quá khứ (yesterday, in 2019, 3 years ago).\n• Hiện tại hoàn thành (have/has + V3/ed): Hành động bắt đầu trong quá khứ kéo dài đến hiện tại hoặc không nêu rõ thời gian (since, for, already, yet).",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Có 'since + mốc thời gian' (ví dụ: since 2018) thì mệnh đề chính BẮT BUỘC dùng Hiện tại hoàn thành, không dùng Quá khứ đơn.",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Professor Davis _____ (teach) at this university since 2015.",
                "options": ["taught", "has taught", "is teaching", "teaches"],
                "answer": "has taught",
                "explanation": "Có 'since 2015' thể hiện hành động kéo dài đến nay -> Hiện tại hoàn thành: has taught."
            },
            {
                "id": "drill_2",
                "prompt": "Yesterday, the committee _____ (ratify) the new regulations.",
                "options": ["has ratified", "ratified", "ratifies", "was ratifying"],
                "answer": "ratified",
                "explanation": "Có mốc quá khứ rõ ràng 'Yesterday' -> Quá khứ đơn: ratified."
            },
            {
                "id": "drill_3",
                "prompt": "We _____ (already / prepare) all essential materials for the workshop.",
                "options": ["already prepared", "have already prepared", "are already preparing", "prepared already"],
                "answer": "have already prepared",
                "explanation": "'Already' trong câu khẳng định chỉ thành quả đạt được -> Hiện tại hoàn thành: have already prepared."
            }
        ]
    },
    ("grammar_cloze", "B1"): {
        "title": "⚡ BÍ KÍP 30S: CÂU ĐIỀU KIỆN LOẠI 1 & BỊ ĐỘNG HỌC THUẬT",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• Điều kiện loại 1: If + S + V(hiện tại đơn), S + will/can + V (nguyên mẫu).\n• Câu bị động: S + be + V3/ed (Chủ ngữ nhận tác động, xác định thì bằng trợ động từ be).",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Trong mệnh đề 'If' hoặc 'Unless', TUYỆT ĐỐI KHÔNG dùng 'will' (Sai: If it will rain... -> Đúng: If it rains...).",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "If the team _____ (conduct) the survey carefully, the findings will be credible.",
                "options": ["will conduct", "conducts", "conducted", "is conducting"],
                "answer": "conducts",
                "explanation": "Mệnh đề 'If' của điều kiện loại 1 chia thì Hiện tại đơn: conducts."
            },
            {
                "id": "drill_2",
                "prompt": "The ancient artifacts _____ (protect) strictly by the museum curators.",
                "options": ["are protected", "protect", "is protected", "have protected"],
                "answer": "are protected",
                "explanation": "Chủ ngữ số nhiều 'artifacts' bị động hiện tại: are + V3 (protected)."
            },
            {
                "id": "drill_3",
                "prompt": "Unless you _____ (register) before 5 PM, your admission will be canceled.",
                "options": ["will register", "register", "registered", "don't register"],
                "answer": "register",
                "explanation": "Sau 'Unless' (= If not) chia hiện tại đơn khẳng định: register."
            }
        ]
    },
    ("grammar_cloze", "B2"): {
        "title": "⚡ BÍ KÍP 30S: ĐẢO NGỮ 'NOT ONLY' & CÂU ĐIỀU KIỆN LOẠI 2",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• Điều kiện loại 2: If + S + V2/were, S + would + V. (Giả định trái thực tế hiện tại, to be luôn chia WERE).\n• Đảo ngữ Not only: Not only + Trợ động từ (did/do/does) + S + V..., but also...",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Khi đảo ngữ với 'Not only', bắt buộc phải đưa trợ động từ lên trước chủ ngữ và động từ chính trở về nguyên mẫu.",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Not only _____ the research grant, but she also secured corporate sponsorship.",
                "options": ["did she receive", "she received", "received she", "she did receive"],
                "answer": "did she receive",
                "explanation": "Cấu trúc đảo ngữ phủ định: Not only + did + S + V(nguyên mẫu)."
            },
            {
                "id": "drill_2",
                "prompt": "If the laboratory _____ (be) fully automated, researchers would save hours daily.",
                "options": ["was", "were", "is", "would be"],
                "answer": "were",
                "explanation": "Câu điều kiện loại 2 học thuật: to be luôn chia 'were' cho mọi chủ ngữ."
            },
            {
                "id": "drill_3",
                "prompt": "Hardly _____ the conference began when the unexpected power failure occurred.",
                "options": ["had the keynote speech concluded", "the keynote speech had concluded", "did conclude the keynote speech", "concluded the keynote speech"],
                "answer": "had the keynote speech concluded",
                "explanation": "Cấu trúc đảo ngữ thời gian: Hardly had + S + V3 + when + S + V2."
            }
        ]
    },
    ("grammar_cloze", "C1"): {
        "title": "⚡ BÍ KÍP 30S: ĐẢO NGỮ ĐIỀU KIỆN LOẠI 3 & CÂU CHẺ NHẤN MẠNH",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• Đảo ngữ điều kiện 3: Had + S + V3/ed, S + would have + V3.\n• Câu chẻ (Cleft sentence): It is/was + [Thành phần nhấn mạnh] + that + S + V.",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Đảo ngữ loại 3 bỏ hẳn từ 'If', bắt đầu bằng 'Had'. Câu chẻ dùng 'that' phổ quát bất kể thành phần được nhấn mạnh là người hay vật trong văn phong IELTS 8.0+.",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "_____ the analysts anticipated the macroeconomic crisis, they would have restructured the fund.",
                "options": ["Had", "If had", "Were", "Did"],
                "answer": "Had",
                "explanation": "Đảo ngữ câu điều kiện loại 3: Had + S + V3/ed (không dùng If)."
            },
            {
                "id": "drill_2",
                "prompt": "It was precisely through empirical validation _____ the theorem gained worldwide acclaim.",
                "options": ["that", "which", "whom", "where"],
                "answer": "that",
                "explanation": "Câu chẻ nhấn mạnh phương thức: It was + through... + that + Clause."
            },
            {
                "id": "drill_3",
                "prompt": "Were the board _____ (concur) on the merger, unprecedented market synergy could arise.",
                "options": ["to concur", "concurring", "concurred", "concur"],
                "answer": "to concur",
                "explanation": "Đảo ngữ điều kiện loại 2 học thuật: Were + S + to-V."
            }
        ]
    },
    ("grammar_cloze", "C2"): {
        "title": "⚡ BÍ KÍP 30S: CẤU TRÚC ĐẢO NGỮ KÉP & GIẢ ĐỊNH THỨC SUBJUNCTIVE",
        "weak_section_name": "Vận Dụng Ngữ Pháp (Cloze)",
        "core_rule": "• No sooner had + S + V3 + than + S + V2.\n• Thể giả định thức: S + demand / insist / recommend + that + S + (should) + V(bare).",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Sau cấu trúc đề xuất (crucial that, recommend that), động từ luôn giữ nguyên mẫu không chia (bare infinitive), kể cả với chủ ngữ số ít he/she/it.",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "No sooner had the keynote address commenced _____ critical breakthroughs were proclaimed.",
                "options": ["than", "when", "then", "that"],
                "answer": "than",
                "explanation": "Cặp liên từ đảo ngữ chuẩn: No sooner had... than... (Hardly had... when...)."
            },
            {
                "id": "drill_2",
                "prompt": "It is imperative that every candidate _____ (adhere) strictly to the non-disclosure clause.",
                "options": ["adhere", "adheres", "adhered", "is adhering"],
                "answer": "adhere",
                "explanation": "Thể giả định thức (Subjunctive) sau 'imperative that + S + V(bare)'."
            },
            {
                "id": "drill_3",
                "prompt": "Seldom _____ such remarkable unanimity among conflicting geopolitical factions.",
                "options": ["has one observed", "one has observed", "observed one", "one observed"],
                "answer": "has one observed",
                "explanation": "Đảo ngữ với phó từ tần suất phủ định: Seldom + has + S + V3."
            }
        ]
    },
    ("syntax", "A1"): {
        "title": "⚡ BÍ KÍP 30S: TRẬT TỰ CÂU CƠ BẢN SVOCA & TÍNH TỪ OSASCOMP",
        "weak_section_name": "Lắp Ráp Cú Pháp (Syntax)",
        "core_rule": "• Thứ tự chuẩn: Chủ ngữ (S) + Động từ (V) + Tân ngữ (O) + Nơi chốn + Thời gian.\n• Trật tự tính từ: Quan điểm (Opinion) -> Kích thước (Size) -> Tuổi (Age) -> Hình dạng (Shape) -> Màu sắc (Color) -> Nguồn gốc (Origin) -> Chất liệu (Material) -> Mục đích (Purpose) + Noun.",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Không bao giờ đặt trạng từ thời gian vào giữa Động từ và Tân ngữ (Sai: I eat every day apples -> Đúng: I eat apples every day).",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Chọn câu có trật tự từ đúng ngữ pháp nhất:",
                "options": [
                    "She bought a beautiful small antique wooden desk yesterday.",
                    "She bought yesterday a beautiful small antique wooden desk.",
                    "She bought a wooden small beautiful antique desk yesterday.",
                    "Yesterday she bought a antique beautiful small wooden desk."
                ],
                "answer": "She bought a beautiful small antique wooden desk yesterday.",
                "explanation": "Thứ tự tính từ OSASCOMP: beautiful (Opinion) -> small (Size) -> antique (Age) -> wooden (Material) -> desk."
            },
            {
                "id": "drill_2",
                "prompt": "Chọn trật tự cú pháp câu chuẩn:",
                "options": [
                    "Students study quiet in the library every afternoon.",
                    "Students study quietly in the library every afternoon.",
                    "Students study quietly every afternoon in the library.",
                    "Quietly students every afternoon in the library study."
                ],
                "answer": "Students study quietly in the library every afternoon.",
                "explanation": "Quy tắc vị trí: S (Students) + V (study) + Manner (quietly) + Place (in the library) + Time (every afternoon)."
            },
            {
                "id": "drill_3",
                "prompt": "Chọn câu nghi vấn Wh- đúng trật tự:",
                "options": [
                    "Where does your brother work at weekends?",
                    "Where your brother does work at weekends?",
                    "Where works your brother at weekends?",
                    "Where does work your brother at weekends?"
                ],
                "answer": "Where does your brother work at weekends?",
                "explanation": "Công thức câu hỏi Wh-: Wh-word + Auxiliary (does) + S (your brother) + V-bare (work)..."
            }
        ]
    },
    ("syntax", "B1"): {
        "title": "⚡ BÍ KÍP 30S: RÚT GỌN MỆNH ĐỀ QUAN HỆ & CÂU GHÉP LIÊN TỪ",
        "weak_section_name": "Lắp Ráp Cú Pháp (Syntax)",
        "core_rule": "• Rút gọn chủ động: Bỏ đại từ & to be, chuyển V thành V-ing (The man who is talking -> The man talking).\n• Rút gọn bị động: Bỏ đại từ & to be, giữ V3/ed (The book which was written -> The book written).\n• Giới từ đi trước đại từ: preposition + which (vật) / whom (người).",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Tuyệt đối không dùng 'that' ngay sau dấu phẩy hoặc ngay sau giới từ.",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Chọn câu rút gọn mệnh đề quan hệ chuẩn xác:",
                "options": [
                    "The documents sent to the committee yesterday required immediate verification.",
                    "The documents was sent to the committee yesterday required immediate verification.",
                    "The documents sending to the committee yesterday required immediate verification.",
                    "The documents which sent to the committee yesterday required immediate verification."
                ],
                "answer": "The documents sent to the committee yesterday required immediate verification.",
                "explanation": "Rút gọn mệnh đề bị động: 'The documents (which were) sent...' -> sent."
            },
            {
                "id": "drill_2",
                "prompt": "Chọn câu dùng giới từ với đại từ quan hệ chuẩn:",
                "options": [
                    "The project in which we participated achieved unprecedented acclaim.",
                    "The project in that we participated achieved unprecedented acclaim.",
                    "The project which in we participated achieved unprecedented acclaim.",
                    "The project where we participated in it achieved acclaim."
                ],
                "answer": "The project in which we participated achieved unprecedented acclaim.",
                "explanation": "Sau giới từ 'in' chỉ vật dùng 'which', không dùng 'that'."
            },
            {
                "id": "drill_3",
                "prompt": "Chọn câu chủ động có phân từ hoàn chỉnh:",
                "options": [
                    "Arriving at the destination, the team unpacked their equipment.",
                    "Arrived at the destination, the team unpacked their equipment.",
                    "Having arrive at the destination, the team unpacked their equipment.",
                    "Arriving at the destination, equipment was unpacked by the team."
                ],
                "answer": "Arriving at the destination, the team unpacked their equipment.",
                "explanation": "Mệnh đề phân từ hiện tại (Arriving...) đồng chủ ngữ với mệnh đề chính (the team)."
            }
        ]
    },
    ("word_scramble", "default"): {
        "title": "⚡ BÍ KÍP 30S: BỘ XƯƠNG KÝ TỰ & TIỀN TỐ/HẬU TỐ HỌC THUẬT",
        "weak_section_name": "Gỡ Bom Ký Tự (Scramble)",
        "core_rule": "• Bước 1: Nhận diện tiền tố quen thuộc (un-, in-, dis-, re-, pro-, con-).\n• Bước 2: Nhận diện hậu tố xác định từ loại (-tion, -ment, -able, -ive, -ous, -ly).\n• Bước 3: Ghép phần thân từ gốc (root word) ở giữa.",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Các từ hay mắc bẫy nhân đôi phụ âm: accommodate (2c, 2m), embarrassment (2r, 2s), occurrence (2c, 2r).",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Từ vựng nào dưới đây có chính tả chuẩn xác 100%?",
                "options": ["accommodate", "accomodate", "acommodate", "acomodate"],
                "answer": "accommodate",
                "explanation": "Chính tả chuẩn là 'accommodate' với 2 chữ 'c' và 2 chữ 'm'."
            },
            {
                "id": "drill_2",
                "prompt": "Từ vựng nào mang nghĩa 'sự xuất hiện, biến cố' viết đúng chính tả?",
                "options": ["occurrence", "occurance", "ocurrence", "ocurrance"],
                "answer": "occurrence",
                "explanation": "Chính tả chuẩn là 'occurrence' (2 chữ 'c', 2 chữ 'r', đuôi 'ence')."
            },
            {
                "id": "drill_3",
                "prompt": "Sắp xếp các chữ cái sau thành tính từ học thuật: [C, R, U, C, I, A, L]",
                "options": ["CRUCIAL", "CURCIAL", "CIRCUALL", "CRUCILA"],
                "answer": "CRUCIAL",
                "explanation": "Ký tự ghép thành 'CRUCIAL' (Cốt lõi, mang tính quyết định)."
            }
        ]
    },
    ("vocab_mcq", "default"): {
        "title": "⚡ BÍ KÍP 30S: LOẠI TRỪ CẶP TỪ GÂY LÚ & COLLOCATION HỌC THUẬT",
        "weak_section_name": "Nhận Diện Từ Vựng (MCQ)",
        "core_rule": "• Đọc kỹ ngữ cảnh câu để xác định sắc thái nghĩa (tích cực hay tiêu cực).\n• Tìm động từ đi kèm (collocation): 'conduct research' (làm nghiên cứu), 'reach consensus' (đạt đồng thuận).\n• Loại trừ ngay 2 đáp án sai hoàn toàn về ngữ cảnh.",
        "trap_alert": "⚠️ BẪY ĐỀ THI: Phân biệt các cặp từ: 'Economic' (thuộc về nền kinh tế) vs 'Economical' (tiết kiệm); 'Affect' (động từ: tác động) vs 'Effect' (danh từ: kết quả/tác động).",
        "drills": [
            {
                "id": "drill_1",
                "prompt": "Buying goods in bulk is much more _____ (tiết kiệm) for large families.",
                "options": ["economical", "economic", "economics", "economist"],
                "answer": "economical",
                "explanation": "'Economical' có nghĩa là tiết kiệm chi phí; 'Economic' là thuộc về nền kinh tế."
            },
            {
                "id": "drill_2",
                "prompt": "The new environmental policy will directly _____ our manufacturing process.",
                "options": ["affect", "effect", "effective", "efficient"],
                "answer": "affect",
                "explanation": "Chỗ trống cần Động từ: 'affect' (tác động lên); 'effect' là danh từ."
            },
            {
                "id": "drill_3",
                "prompt": "Collocation chuẩn: The committee finally reached a broad _____ regarding the proposal.",
                "options": ["consensus", "conflict", "obstacle", "dilemma"],
                "answer": "consensus",
                "explanation": "Cụm cố định 'reach a consensus' nghĩa là đạt được sự đồng thuận chung."
            }
        ]
    }
}


@roadmap_bp.route('/milestone/<int:milestone_id>/micro_lesson', methods=['GET'])
def get_milestone_micro_lesson(milestone_id):
    """
    TRẠM VI HỌC BÙ LỖ HỔNG (ADAPTIVE MICRO-LESSON)
    Dựa vào phần thi có điểm thấp nhất (lỗ hổng học thuật) để sinh ra gói bài học 30s + 3 câu bài tập giải cứu.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    milestone = RoadmapMilestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Không tìm thấy chặng này!"}), 404

    weak_section = request.args.get('weak_section', 'grammar_cloze')
    band = milestone.band_level or 'A1'

    # Tìm bài vi học phù hợp nhất trong ngân hàng thích ứng
    lesson = ADAPTIVE_MICRO_LESSONS.get((weak_section, band))
    if not lesson:
        lesson = ADAPTIVE_MICRO_LESSONS.get((weak_section, 'default'))
    if not lesson:
        for b in [band, 'B2', 'B1', 'A2', 'A1', 'C1']:
            if (weak_section, b) in ADAPTIVE_MICRO_LESSONS:
                lesson = ADAPTIVE_MICRO_LESSONS[(weak_section, b)]
                break
    if not lesson:
        lesson = ADAPTIVE_MICRO_LESSONS.get(('grammar_cloze', 'A1'))

    drill_token = str(uuid.uuid4())
    answer_keys = {}
    client_drills = []

    for d in lesson["drills"]:
        answer_keys[d["id"]] = {
            "answer": d["answer"],
            "prompt": d["prompt"],
            "explanation": d["explanation"]
        }
        client_drills.append({
            "id": d["id"],
            "prompt": d["prompt"],
            "options": d["options"]
        })

    session['active_drill'] = {
        "drill_token": drill_token,
        "milestone_id": milestone_id,
        "answer_keys": answer_keys
    }
    session.modified = True

    return jsonify({
        "status": "success",
        "drill_token": drill_token,
        "milestone_id": milestone_id,
        "band_level": band,
        "weak_section_key": weak_section,
        "title": lesson["title"],
        "weak_section_name": lesson.get("weak_section_name", weak_section),
        "core_rule": lesson["core_rule"],
        "trap_alert": lesson["trap_alert"],
        "drills": client_drills
    }), 200


@roadmap_bp.route('/milestone/<int:milestone_id>/submit_micro_drill', methods=['POST'])
def submit_micro_drill(milestone_id):
    """
    CHẤM BÀI TẬP BÙ LỖ HỔNG (FAST-FIX RESCUE DRILL)
    - Đúng 3/3 câu: Cứu viện +20 RP, rút thời gian Cooldown xuống 5 giây.
    - Đúng 2/3 câu: Cứu viện +15 RP, rút thời gian Cooldown xuống 5 giây.
    - Đúng 1/3 câu: Cứu viện +10 RP, rút thời gian Cooldown xuống 5 giây.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Người dùng không tồn tại!"}), 404

    data = request.get_json() or {}
    drill_token = data.get('drill_token')
    user_answers = data.get('answers', {})

    active_drill = session.get('active_drill')
    if not active_drill or active_drill.get('drill_token') != drill_token or active_drill.get('milestone_id') != milestone_id:
        return jsonify({"error": "Phiên làm bài tập cứu viện không hợp lệ hoặc đã nộp!"}), 400

    drill_keys = active_drill.get('answer_keys', {})
    correct_count = 0
    review_details = []

    for q_id, q_info in drill_keys.items():
        u_ans = user_answers.get(q_id, '').strip()
        c_ans = q_info['answer'].strip()
        is_cor = (u_ans.lower() == c_ans.lower())
        if is_cor:
            correct_count += 1
        review_details.append({
            "prompt": q_info["prompt"],
            "user_answer": u_ans or "(Bỏ trống)",
            "correct_answer": c_ans,
            "is_correct": is_cor,
            "explanation": q_info["explanation"]
        })

    rescue_rp = 0
    if correct_count == 3:
        rescue_rp = 20
    elif correct_count == 2:
        rescue_rp = 15
    elif correct_count == 1:
        rescue_rp = 10

    if user.academic_rp is None:
        user.academic_rp = 500

    if rescue_rp > 0:
        user.academic_rp += rescue_rp

    # GIẢM COOLDOWN XUỐNG CÒN 5 GIÂY (đặt last_exam_fail_time lùi 40 giây so với hiện tại)
    user.last_exam_fail_time = datetime.now() - timedelta(seconds=40)

    # Tự động cập nhật / phục hồi Level nếu điểm RP cải thiện
    check_and_update_level(user_id)
    db.session.commit()

    # Xóa token phiên drill
    session.pop('active_drill', None)
    session.modified = True

    return jsonify({
        "status": "success",
        "passed": (correct_count >= 1),
        "correct_count": correct_count,
        "total": len(drill_keys),
        "rescue_rp": rescue_rp,
        "new_rp": user.academic_rp,
        "current_rank": user.current_level,
        "cooldown_remaining": 5,
        "message": f"🎉 ĐÃ BÙ LỖ HỔNG THÀNH CÔNG! Bạn nhận được +{rescue_rp} RP cứu viện và thời gian chờ thi lại được rút ngắn xuống chỉ còn 5 giây!",
        "review": review_details
    }), 200

