import os
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, render_template

from app import db
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.vision_log import VisionDetectionLog
from app.ml_models.owl_vit_engine import LocalOwlVitEngine
from app.ml_models.vision_taxonomy import OBJECT_PARTS_TAXONOMY, get_part_info
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.scramble_engine import LocalScrambleEngine
from app.ml_models.critique_synthesizer import LocalCritiqueSynthesizer
from app.utils.level_manager import check_and_update_level

vision_bp = Blueprint('vision', __name__)

# Khởi tạo các Core AI (Lazy / Singleton)
owl_vit_engine = LocalOwlVitEngine(lazy=True)
gec_engine = LocalGECEngine(lazy=True)
scramble_engine = LocalScrambleEngine()
critique_synthesizer = LocalCritiqueSynthesizer()


@vision_bp.route('/vision-arena')
def vision_arena_page():
    """Trang Đấu trường Thị giác & Tương tác Cử chỉ Bàn tay Không chạm"""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    return render_template(
        'vision_arena.html',
        current_user=current_user,
        taxonomy=OBJECT_PARTS_TAXONOMY
    )


@vision_bp.route('/api/vision/categories', methods=['GET'])
def get_categories():
    """Lấy danh sách các danh mục vật thể và bộ phận mẫu"""
    return jsonify({
        "status": "success",
        "categories": OBJECT_PARTS_TAXONOMY
    })


@vision_bp.route('/api/vision/scan', methods=['POST'])
def scan_object():
    """
    API Nhận diện vật thể và trích xuất chi tiết bộ phận con từ Camera Frame
    Độc lập 100% với Cloud LLM (Sử dụng Local OWL-ViT)
    """
    try:
        data = request.get_json(silent=True) or {}
        image_data = data.get('image')
        target_category = data.get('target_category') or None
        custom_queries = data.get('custom_queries') or None
        threshold = float(data.get('threshold', 0.14))

        if not image_data:
            return jsonify({
                "status": "error",
                "message": "Không tìm thấy dữ liệu ảnh (image) trong request!"
            }), 400

        # 1. Gọi Local OWL-ViT Engine
        result = owl_vit_engine.detect_parts(
            image_input=image_data,
            target_category=target_category,
            custom_queries=custom_queries,
            score_threshold=threshold,
            max_results=8
        )

        if result.get("status") != "success":
            return jsonify(result), 500

        detected_parts = result.get("detected_parts", [])
        primary_object = result.get("primary_object", "object")

        # 2. Đối chiếu với kho từ vựng của User hiện tại
        user_id = session.get('user_id')
        learned_words = set()
        if user_id:
            user_vocabs = db.session.query(Vocabulary.word).join(
                UserVocabulary, UserVocabulary.vocab_id == Vocabulary.id
            ).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.is_unlocked == True
            ).all()
            learned_words = {v[0].lower() for v in user_vocabs}

        for part in detected_parts:
            part["is_learned"] = (part["word"].lower() in learned_words)

        # 3. Ghi log lịch sử nhận diện
        if user_id and len(detected_parts) > 0:
            try:
                log_entry = VisionDetectionLog(
                    user_id=user_id,
                    detected_object=primary_object,
                    detected_parts=[{
                        "word": p["word"],
                        "confidence": p["confidence"],
                        "cefr": p["cefr"]
                    } for p in detected_parts]
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as log_err:
                db.session.rollback()
                print(f"[!] Lỗi ghi VisionDetectionLog: {log_err}")

        return jsonify({
            "status": "success",
            "primary_object": primary_object,
            "total_detected": len(detected_parts),
            "inference_time_ms": result.get("inference_time_ms", 0),
            "detected_parts": detected_parts
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi hệ thống khi quét ảnh: {str(e)}"
        }), 500


@vision_bp.route('/api/vision/save-vocab', methods=['POST'])
def save_vision_vocab():
    """
    Thu nạp từ vựng thị giác mới vào kho ôn tập cá nhân (Ebbinghaus SRS)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Vui lòng đăng nhập để thu thập từ vựng vào kho cá nhân!"
        }), 401

    data = request.get_json(silent=True) or {}
    word = (data.get('word') or '').strip().lower()
    parent_obj = data.get('parent_object', 'general')

    if not word:
        return jsonify({"status": "error", "message": "Từ vựng không hợp lệ"}), 400

    try:
        # 1. Tìm hoặc tạo bản ghi Vocabulary trong bảng gốc
        vocab = Vocabulary.query.filter_by(word=word).first()
        meta = get_part_info(word, parent_obj)

        if not vocab:
            vocab = Vocabulary(
                word=word,
                meaning=meta.get("meaning", "Từ vựng thị giác"),
                cefr_level=meta.get("cefr", "B1"),
                theme=f"Vision: {parent_obj.capitalize()}"
            )
            db.session.add(vocab)
            db.session.flush()

        # 2. Tìm hoặc tạo liên kết UserVocabulary
        user_vocab = UserVocabulary.query.filter_by(
            user_id=user_id,
            vocab_id=vocab.id
        ).first()

        now = datetime.now()
        if not user_vocab:
            user_vocab = UserVocabulary(
                user_id=user_id,
                vocab_id=vocab.id,
                is_unlocked=True,
                memorization_level='CHUA_THUOC',
                source_type='vision_scan',
                context_note=f"Phát hiện từ vật thể: {parent_obj}",
                fail_count=0,
                avg_response_time=2.0,
                previous_interval=1.0,
                next_review_time=now + timedelta(hours=2) # Chu kỳ SRS ban đầu
            )
            db.session.add(user_vocab)
        else:
            user_vocab.is_unlocked = True
            user_vocab.source_type = 'vision_scan'
            user_vocab.context_note = f"Phát hiện từ vật thể: {parent_obj}"

        # 3. Thưởng nhẹ EXP thu thập từ mới
        user = User.query.get(user_id)
        if user:
            user.exp = (user.exp or 0) + 10
            check_and_update_level(user)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Đã thu thập từ '{word}' vào kho ôn tập SRS thành công (+10 EXP)!",
            "word": word,
            "cefr": vocab.cefr_level,
            "next_review": user_vocab.next_review_time.strftime("%Y-%m-%d %H:%M")
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Lỗi khi lưu từ vựng: {str(e)}"
        }), 500


@vision_bp.route('/api/vision/submit-sentence', methods=['POST'])
def submit_vision_sentence():
    """
    Chấm điểm câu văn ghép được từ các thẻ từ bằng cử chỉ tay
    Tích hợp Scramble Engine, GEC Engine và Critique Synthesizer
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    data = request.get_json(silent=True) or {}
    sentence = (data.get('sentence') or '').strip()
    words_used = data.get('words_used') or []
    primary_object = data.get('primary_object', 'general')

    if not sentence:
        return jsonify({"status": "error", "message": "Câu văn trống!"}), 400

    try:
        # 1. Chẩn đoán ngữ pháp qua Local GEC Engine
        cefr_band = user.cefr_level if (user and user.cefr_level) else "B1"
        target_focus = words_used[0] if words_used else ""
        gec_result = gec_engine.evaluate(
            text=sentence,
            user_level=cefr_band,
            target_word=target_focus
        )

        corrected_sentence = gec_result.get("corrected_text") or sentence
        error_count = gec_result.get("error_count", 0)
        has_error = error_count > 0 or gec_result.get("is_fragment", False)

        # 2. Đánh giá điểm số (quy đổi thang 10 sang thang 100)
        raw_score = gec_result.get("score", 8.0)
        score = int(raw_score * 10)
        if len(words_used) >= 3:
            score = min(100, score + 5) # Thưởng vì ghép được nhiều từ

        # 3. Lời nhận xét sư phạm Master G
        feedback = gec_result.get("master_g_critique") or gec_result.get("feedback") or "Câu văn của bạn được ghép rất hoàn chỉnh!"

        # 4. Thưởng EXP nếu người dùng có tài khoản
        exp_reward = int(score * 0.5)
        level_up = False
        if user:
            user.exp = (user.exp or 0) + exp_reward
            level_up = check_and_update_level(user)
            db.session.commit()

        return jsonify({
            "status": "success",
            "original_sentence": sentence,
            "corrected_sentence": corrected_sentence,
            "has_error": has_error,
            "error_count": error_count,
            "score": score,
            "exp_awarded": exp_reward,
            "level_up": level_up,
            "feedback": feedback,
            "words_used": words_used
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi khi chấm câu: {str(e)}"
        }), 500
