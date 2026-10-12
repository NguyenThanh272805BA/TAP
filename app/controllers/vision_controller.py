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
from app.ml_models.vision_taxonomy import (
    OBJECT_PARTS_TAXONOMY,
    get_part_info,
    DOMAINS,
    get_domain_stats,
    get_taxonomy_forest,
    get_micro_queries,
    lookup_forest_word,
    get_facial_expressions
)
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
        taxonomy=OBJECT_PARTS_TAXONOMY,
        domains=DOMAINS,
        domain_stats=get_domain_stats()
    )


@vision_bp.route('/api/vision/categories', methods=['GET'])
def get_categories():
    """Lấy danh sách các danh mục vật thể và các miền thực thể toàn cảnh"""
    return jsonify({
        "status": "success",
        "domains": DOMAINS,
        "domain_stats": get_domain_stats(),
        "categories": OBJECT_PARTS_TAXONOMY
    })


@vision_bp.route('/api/vision/taxonomy-forest', methods=['GET'])
def get_taxonomy_forest_info():
    """Lấy siêu dữ liệu Rừng phân cấp 5.830 từ vựng và các thực thể vĩ mô cốt lõi"""
    forest = get_taxonomy_forest()
    trees = forest.get("macro_trees", {})
    tree_summaries = {}
    for k, v in trees.items():
        tree_summaries[k] = {
            "name": v.get("name"),
            "vn_name": v.get("vn_name"),
            "domain": v.get("domain"),
            "cefr": v.get("cefr"),
            "micro_parts_count": len(v.get("micro_anatomy", [])),
            "expressions_count": len(v.get("expressions_behaviors", []))
        }

    return jsonify({
        "status": "success",
        "total_vocab_count": forest.get("total_vocab_count", 5830),
        "macro_trees": tree_summaries,
        "expression_engine": forest.get("expression_engine", {}),
        "stats": forest.get("stats", {})
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
        threshold = float(data.get('threshold', 0.12))
        max_results = int(data.get('max_results', 10))
        max_results = max(3, min(20, max_results))
        granularity = str(data.get('granularity', 'all')).lower()
        domain = str(data.get('domain', 'all')).lower()
        reticle_roi = data.get('reticle_roi')

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
            max_results=max_results,
            granularity=granularity,
            domain=domain,
            reticle_roi=reticle_roi
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
            "domain": result.get("domain", domain),
            "domain_breakdown": result.get("domain_breakdown", {}),
            "scene_info": result.get("scene_info", {}),
            "context_caption": result.get("context_caption", {}),
            "inference_time_ms": result.get("inference_time_ms", 0),
            "detected_parts": detected_parts
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi hệ thống khi quét ảnh: {str(e)}"
        }), 500


@vision_bp.route('/api/vision/micro-focus', methods=['POST'])
def micro_focus_scan():
    """
    API Soi Chi Tiết Vi Mô & Cây Phân Cấp Thực Thể (Focal Reticle Micro-Zoom)
    Phục vụ Mục 13.2, 13.3, 13.4, 13.5
    """
    try:
        data = request.get_json(silent=True) or {}
        image_data = data.get('image')
        reticle_roi = data.get('reticle_roi')
        parent_category = data.get('parent_category')
        mode = data.get('mode', 'all')
        threshold = float(data.get('threshold', 0.08))
        max_results = int(data.get('max_results', 6))

        if not image_data:
            return jsonify({
                "status": "error",
                "message": "Không tìm thấy dữ liệu ảnh (image) trong request!"
            }), 400

        result = owl_vit_engine.detect_micro_focus(
            image_input=image_data,
            reticle_roi=reticle_roi,
            parent_category=parent_category,
            mode=mode,
            score_threshold=threshold,
            max_results=max_results
        )

        # Đối chiếu với từ vựng đã học của user
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

        for md in result.get("micro_detections", []):
            md["is_learned"] = (md["word"].lower() in learned_words)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi xử lý vi mô: {str(e)}"
        }), 500


@vision_bp.route('/api/vision/upload-media', methods=['POST'])
def upload_media_and_scan():
    """
    API Tải lên ảnh tĩnh hoặc video clip (Giới hạn tối đa 25MB)
    Tự động trích xuất khung hình và nhận diện từ vựng theo hình ảnh động hoặc tĩnh.
    Hỗ trợ chia cấp độ nhận biết (granularity) và giới hạn số lượng vật thể (3-20).
    """
    try:
        if 'media' not in request.files and 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "Vui lòng chọn tệp ảnh hoặc video để tải lên!"
            }), 400

        file = request.files.get('media') or request.files.get('file')
        if not file or file.filename == '':
            return jsonify({
                "status": "error",
                "message": "Tệp rỗng hoặc chưa được chọn!"
            }), 400

        # Kiểm tra dung lượng tệp (Giới hạn tối đa 25MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_allowed_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_allowed_size:
            size_mb = round(file_size / (1024 * 1024), 2)
            return jsonify({
                "status": "error",
                "message": f"Dung lượng tệp ({size_mb} MB) vượt quá giới hạn tối đa cho phép (25 MB)!"
            }), 400

        filename = file.filename.lower()
        target_category = request.form.get('target_category') or None
        granularity = str(request.form.get('granularity', 'all')).lower()
        domain = str(request.form.get('domain', 'all')).lower()
        max_results = int(request.form.get('max_results', 10))
        max_results = max(3, min(20, max_results))
        threshold = float(request.form.get('threshold', 0.12))

        is_video = any(filename.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']) or (
            bool(file.mimetype and file.mimetype.startswith('video/'))
        )

        import cv2
        import base64
        import io
        from PIL import Image

        extracted_pil_image = None
        preview_base64 = None

        if is_video:
            # Lưu tạm video vào scratch file để OpenCV trích xuất frame
            temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"temp_{int(time.time()*1000)}_{os.path.basename(filename)}")
            file.save(temp_path)

            try:
                cap = cv2.VideoCapture(temp_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25
                # Chọn frame tại giây thứ 1 (hoặc giữa video nếu ngắn)
                target_frame_no = min(int(fps * 1.0), max(0, total_frames // 2))
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_no)
                success, frame = cap.read()
                if not success:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, frame = cap.read()
                cap.release()

                if not success or frame is None:
                    return jsonify({
                        "status": "error",
                        "message": "Không thể trích xuất khung hình từ video!"
                    }), 400

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                extracted_pil_image = Image.fromarray(frame_rgb)

                # Tạo preview base64
                buffered = io.BytesIO()
                extracted_pil_image.save(buffered, format="JPEG", quality=85)
                preview_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode('utf-8')

            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        else:
            # Là ảnh tĩnh
            image_bytes = file.read()
            extracted_pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buffered = io.BytesIO()
            extracted_pil_image.save(buffered, format="JPEG", quality=85)
            preview_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Thực hiện nhận diện với OWL-ViT
        result = owl_vit_engine.detect_parts(
            image_input=extracted_pil_image,
            target_category=target_category,
            score_threshold=threshold,
            max_results=max_results,
            granularity=granularity,
            domain=domain
        )

        if result.get("status") != "success":
            return jsonify(result), 500

        detected_parts = result.get("detected_parts", [])
        primary_object = result.get("primary_object", "object")

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

        return jsonify({
            "status": "success",
            "media_type": "video" if is_video else "image",
            "primary_object": primary_object,
            "total_detected": len(detected_parts),
            "domain": result.get("domain", domain),
            "domain_breakdown": result.get("domain_breakdown", {}),
            "scene_info": result.get("scene_info", {}),
            "context_caption": result.get("context_caption", {}),
            "inference_time_ms": result.get("inference_time_ms", 0),
            "preview_image": preview_base64,
            "detected_parts": detected_parts
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi xử lý tệp tải lên: {str(e)}"
        }), 500


@vision_bp.route('/api/vision/save-vocab', methods=['POST'])
def save_vision_vocab():
    """
    Thu nạp từ vựng thị giác mới vào kho ôn tập cá nhân (Ebbinghaus SRS)
    """
    user_id = session.get('user_id')
    if not user_id:
        guest_user = User.query.first()
        if guest_user:
            user_id = guest_user.id
        else:
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

        # 3. Thưởng nhẹ RP & Xu thu thập từ mới
        user = User.query.get(user_id)
        if user:
            user.academic_rp = (user.academic_rp or 0) + 10
            user.coins = (user.coins or 0) + 5
            check_and_update_level(user.id)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Đã thu thập từ '{word}' vào kho ôn tập SRS thành công (+10 RP, +5 Xu)!",
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
    user = User.query.get(user_id) if user_id else User.query.first()

    data = request.get_json(silent=True) or {}
    sentence = (data.get('sentence') or '').strip()
    words_used = data.get('words_used') or []
    primary_object = data.get('primary_object', 'general')

    if not sentence:
        return jsonify({"status": "error", "message": "Câu văn trống!"}), 400

    try:
        # 1. Chẩn đoán ngữ pháp qua Local GEC Engine
        cefr_band = getattr(user, 'current_band', 'B1') if user else "B1"
        if not cefr_band:
            cefr_band = "B1"
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

        # 4. Thưởng Rank Points & Xu nếu người dùng có tài khoản
        rp_reward = max(5, int(score * 0.2))
        coins_reward = max(2, int(score * 0.1))
        level_up = False
        if user:
            user.academic_rp = (user.academic_rp or 0) + rp_reward
            user.coins = (user.coins or 0) + coins_reward
            level_up, _ = check_and_update_level(user.id)
            db.session.commit()

        return jsonify({
            "status": "success",
            "original_sentence": sentence,
            "corrected_sentence": corrected_sentence,
            "has_error": has_error,
            "error_count": error_count,
            "score": score,
            "exp_awarded": rp_reward,
            "rp_awarded": rp_reward,
            "coins_awarded": coins_reward,
            "level_up": level_up,
            "feedback": feedback,
            "words_used": words_used
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi khi chấm câu: {str(e)}"
        }), 500
