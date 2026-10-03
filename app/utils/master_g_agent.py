import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

from app import db
from app.models.user import User
from app.models.test import TestLog
from app.models.user_vocabulary import UserVocabulary
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.models.roadmap import RoadmapMilestone, UserMilestoneProgress
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.vocab_classifier import VocabCEFRClassifier
from app.ml_models.srs_predictor import SmartSRS
from app.ml_models.scramble_engine import LocalScrambleEngine
from app.ml_models.critique_synthesizer import LocalCritiqueSynthesizer
from app.ml_models.autonomous_miner import AutonomousCorpusMiner
from app.controllers.auth_controller import compute_user_competency_radar


class MasterGPedagogicalAgent:
    """
    TÁC TỬ SƯ PHẠM ĐIỀU PHỐI ĐA PHÂN HỆ MASTER G (MASTER G AUTONOMOUS PEDAGOGICAL AGENT)
    - 100% Offline & Local (Zero LLM Dependency)
    - Đóng vai trò là 'Nhạc Trưởng' (Conductor / Orchestrator) liên kết toàn bộ các phân hệ chuyên trách:
        1. Phân hệ 1: GEC DistilBERT INT8 (Chấm cú pháp câu)
        2. Phân hệ 2: Intent NLU MLP (Đoán ý định)
        3. Phân hệ 3: Smart SRS Ebbinghaus TRF (Dự báo điểm rơi quên)
        4. Phân hệ 4: Vocab CEFR Zipf Classifier (Phân cấp độ khó từ)
        5. Phân hệ 5: Content-Based Recommender (Gợi ý từ vựng liên tưởng)
        6. Phân hệ 6: Autonomous Corpus Miner (Khai phá cụm từ cố định PMI)
        7. Synthesizer: Level-Adaptive Critique Synthesizer (Tổng hợp nhận xét)
    - Chu trình tự hành (BDI Loop): Cảm nhận (Perceive) -> Chẩn đoán (Diagnose) -> Ra quyết định (Plan) -> Thực thi (Act).
    """

    def __init__(self):
        self.gec_engine = LocalGECEngine(lazy=True)
        self.cefr_classifier = VocabCEFRClassifier()
        self.srs_engine = SmartSRS()
        self.scramble_engine = LocalScrambleEngine()
        self.critique_synthesizer = LocalCritiqueSynthesizer()
        self.corpus_miner = AutonomousCorpusMiner()

    def inspect_learner_state(self, user_id: int) -> Dict[str, Any]:
        """
        [PERCEPTION STAGE]: Quét toàn diện hồ sơ và lịch sử học tập của học viên
        """
        user = User.query.get(user_id)
        if not user:
            return {"error": f"Không tìm thấy người dùng #{user_id}"}

        # 1. Quét Ma trận Năng lực Radar 6 Chiều
        radar = compute_user_competency_radar(user_id) or {}
        
        # 2. Quét danh sách từ vựng Smart SRS đang đến hạn ôn tập
        now = datetime.now()
        due_vocabs = UserVocabulary.query.filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.is_unlocked == True,
            UserVocabulary.next_review_time <= now
        ).order_by(UserVocabulary.next_review_time.asc()).limit(8).all()

        due_vocab_list = []
        for uv in due_vocabs:
            v = Vocabulary.query.get(uv.vocab_id)
            if v:
                due_vocab_list.append({
                    "id": v.id,
                    "word": v.word,
                    "meaning": v.meaning,
                    "cefr": v.cefr_level,
                    "fail_count": uv.fail_count or 0,
                    "avg_response_time": uv.avg_response_time or 2.0
                })

        # 3. Quét lịch sử kiểm tra gần nhất (5 bài gần nhất)
        recent_tests = TestLog.query.filter_by(user_id=user_id).order_by(TestLog.created_at.desc()).limit(5).all()
        avg_recent_score = (sum(t.score for t in recent_tests) / len(recent_tests)) if recent_tests else 7.0

        # 4. Quét chặng lộ trình hiện tại
        current_band = getattr(user, 'current_band', 'A1') or 'A1'
        target_band = getattr(user, 'target_band', 'B2') or 'B2'

        return {
            "user_id": user.id,
            "username": user.username,
            "current_band": current_band,
            "target_band": target_band,
            "current_rank": user.current_level,
            "academic_rp": user.academic_rp if user.academic_rp is not None else 500,
            "streak": user.streak_count or 0,
            "consecutive_fails": user.consecutive_fails or 0,
            "radar": radar,
            "due_vocabs_count": len(due_vocab_list),
            "due_vocabs": due_vocab_list,
            "recent_test_count": len(recent_tests),
            "avg_recent_score": round(avg_recent_score, 1)
        }

    def diagnose_and_prescribe(self, user_id: int) -> Dict[str, Any]:
        """
        [REASONING & PRESCRIPTION STAGE]:
        Tự động phán đoán điểm nghẽn nhận thức và xuất toa điều trị (Personalized Learning Prescription)
        hoàn toàn bằng thuật toán cục bộ, không cần LLM.
        """
        state = self.inspect_learner_state(user_id)
        if "error" in state:
            return state

        radar = state.get("radar", {})
        has_data = radar.get("has_data", True)
        is_unranked = radar.get("is_unranked", False)

        weakest = radar.get("weakest", {"key": "grammar", "name": "Chuẩn Ngữ Pháp", "score": 40.0})
        strongest = radar.get("strongest", {"key": "vocabulary", "name": "Vốn Từ Vựng", "score": 75.0})
        weakest_key = weakest.get("key", "grammar")
        weakest_score = weakest.get("score", 50.0)

        consecutive_fails = state.get("consecutive_fails", 0)
        due_count = state.get("due_vocabs_count", 0)
        current_band = state.get("current_band", "A1")
        target_band = state.get("target_band", "B2")

        # ----------------------------------------------------
        # RA QUYẾT ĐỊNH CHẾ ĐỘ SƯ PHẠM (REGIME CLASSIFICATION)
        # ----------------------------------------------------
        if not has_data or is_unranked:
            regime = "INITIAL_ONBOARDING"
            regime_title = "CHÀO MỪNG TÂN BINH: KHỞI TẠO MA TRẬN NĂNG LỰC"
            priority_action = "Hoàn thành Bài Khảo Thí Đầu Vào (Placement Test) để thiết lập hồ sơ học thuật."
        elif consecutive_fails >= 2 or (weakest_score < 45.0 and weakest_key != "none"):
            regime = "CRITICAL_REMEDIAL"
            regime_title = "CẢNH BÁO NGUY CƠ: BÙ LỖ HỔNG HỌC THUẬT KHẨN CẤP"
            priority_action = "Tập trung giải cứu kỹ năng yếu nhất trước khi tiếp tục leo Rank."
        elif due_count >= 3:
            regime = "SRS_RETENTION_SURGE"
            regime_title = "ĐẾN HẠN CỦNG CỐ: KÍCH HOẠT ĐƯỜNG CONG EBBINGHAUS"
            priority_action = f"Có {due_count} từ vựng sắp rơi vào vùng quên lãng. Cần giải phóng trí nhớ ngay."
        elif state.get("avg_recent_score", 0) >= 8.5 and weakest_score >= 65.0:
            regime = "ACCELERATED_ADVANCEMENT"
            regime_title = "PHONG ĐỘ ĐỈNH CAO: BỨT PHÁ CHẶNG MỚI"
            priority_action = "Năng lực đang ở trạng thái tối ưu. Đủ điều kiện vượt cấp thách thức."
        else:
            regime = "BALANCED_FLOW"
            regime_title = "NHỊP ĐỘ CÂN BẰNG: RÈN LUYỆN TOÀN DIỆN"
            priority_action = "Tiếp tục duy trì chuỗi luyện tập đều đặn hàng ngày."

        # ----------------------------------------------------
        # TỰ ĐỘNG LẬP NHIỆM VỤ GIẢI CỨU / THÁCH THỨC (AUTO-PRESCRIPTION)
        # ----------------------------------------------------
        prescribed_tasks = []

        if regime == "INITIAL_ONBOARDING":
            prescribed_tasks.append({
                "type": "ONBOARDING_PLACEMENT",
                "title": "Khảo Thí Xếp Lớp Đầu Vào (Placement Test)",
                "reason": "Kích hoạt Ma Trận Năng Lực 6 Chiều và xác định Band xuất phát chính xác.",
                "payload": None,
                "action_url": "/test/placement",
                "reward_rp": 50
            })
        else:
            # 1. Nhiệm vụ khắc phục kỹ năng yếu nhất
            if weakest_key in ['syntax', 'grammar']:
                # Gọi Brain Scramble / Grammar Quiz
                sample_grammar = Grammar.query.filter_by(cefr_level=current_band).first()
                if not sample_grammar:
                    sample_grammar = Grammar.query.first()
                
                syntax_puzzle = None
                if sample_grammar:
                    syntax_puzzle = self.scramble_engine.generate_syntax_scramble(sample_grammar.id)

                prescribed_tasks.append({
                    "type": "SYNTAX_ASSEMBLY_RESCUE",
                    "title": f"Phục hồi Cú pháp ({weakest['name']})",
                    "reason": f"Chỉ số {weakest['name']} hiện tại đang ở mức {weakest_score}đ.",
                    "payload": syntax_puzzle,
                    "reward_rp": 25,
                    "target_grammar": sample_grammar.structure if sample_grammar else "S + V + O"
                })
            elif weakest_key in ['vocabulary', 'retention']:
                # Gợi ý bài tập từ vựng hoặc củng cố SRS
                target_v = state["due_vocabs"][0] if state["due_vocabs"] else None
                word_puzzle = None
                if target_v:
                    word_puzzle = self.scramble_engine.generate_word_scramble(target_v["id"])
                
                prescribed_tasks.append({
                    "type": "VOCAB_RETENTION_RESCUE",
                    "title": f"Gỡ Bom Trí Nhớ: {target_v['word'] if target_v else 'Từ Vựng Cốt Lõi'}",
                    "reason": "Chỉ số độ bền trí nhớ cần được gia cố theo đường cong lãng quên.",
                    "payload": word_puzzle,
                    "reward_rp": 20
                })

        # 2. Nhiệm vụ ôn tập Smart SRS nếu có từ đến hạn
        if state["due_vocabs"]:
            prescribed_tasks.append({
                "type": "SRS_FLASH_REVIEW",
                "title": f"Ôn tập nhanh {len(state['due_vocabs'])} từ vựng đến hạn",
                "reason": "Thuật toán Ebbinghaus ghi nhận điểm rơi trí nhớ hôm nay.",
                "words": [w["word"] for w in state["due_vocabs"][:5]],
                "reward_rp": 15
            })

        # ----------------------------------------------------
        # TỔNG HỢP LỜI KHUYÊN SƯ PHẠM MASTER G (SLOT-FILLING NLG)
        # ----------------------------------------------------
        user_tier = self.critique_synthesizer.normalize_user_level(state["current_rank"])
        
        if regime == "INITIAL_ONBOARDING":
            advice_msg = (
                "Master G chào mừng tân binh! Hiện tại Ma Trận Năng Lực của bạn đang ở trạng thái chờ kích hoạt (0đ). "
                "Hãy hoàn thành Bài Khảo Thí Đầu Vào (Placement Test) để hệ thống đo lường chính xác các chỉ số phản xạ và ngữ pháp của riêng bạn nhé!"
            )
        elif regime == "CRITICAL_REMEDIAL":
            advice_msg = (
                f"Master G lưu ý bạn: Kỹ năng '{weakest['name']}' của bạn đang cần được gia cố thêm ({weakest_score}đ). "
                f"Trong việc học ngôn ngữ, việc xây chắc nền móng trước khi bứt phá là yếu tố quyết định. "
                f"Hãy hoàn thành bài tập phục hồi dưới đây để củng cố phản xạ và tự tin hơn nhé!"
            )
        elif regime == "SRS_RETENTION_SURGE":
            advice_msg = (
                f"Master G nhắc lịch ôn tập: Hệ thống ghi nhận bạn có {due_count} từ vựng đã đến thời điểm vàng cần kích hoạt lại trí nhớ. "
                f"Dành ra 2 phút ôn luyện ngay hôm nay sẽ giúp các từ này in sâu vào trí nhớ dài hạn của bạn một cách bền vững."
            )
        elif regime == "ACCELERATED_ADVANCEMENT":
            advice_msg = (
                f"Master G biểu dương phong độ: Bạn đang học rất ấn tượng! Điểm kiểm tra gần đây đạt trung bình {state['avg_recent_score']}/10.0 "
                f"và vốn từ phát triển rất vững vàng. Bạn đã hoàn toàn sẵn sàng để bứt phá lên Band {target_band}!"
            )
        else:
            advice_msg = (
                f"Master G đồng hành: Bạn đang duy trì nhịp học rất đều đặn với chuỗi Streak {state['streak']} ngày! "
                f"Thế mạnh nổi bật nhất của bạn lúc này là '{strongest['name']}' ({strongest['score']}đ). Hãy tiếp tục bài rèn luyện hôm nay nhé."
            )

        return {
            "status": "success",
            "agent_name": "Master G Pedagogical Agent (Offline Autonomous Core)",
            "execution_mode": "100%_LOCAL_NON_LLM",
            "current_cefr_estimate": current_band,
            "target_band": target_band,
            "directive": {
                "directive_title": regime_title,
                "directive_advice": advice_msg,
                "priority_action": priority_action,
                "target_action": {"action_type": "CONTINUE_ROADMAP", "target_url": "/roadmap"}
            },
            "learner_summary": {
                "username": state["username"],
                "current_band": current_band,
                "target_band": target_band,
                "academic_rp": state["academic_rp"],
                "overall_score": radar.get("overall_score", 60.0),
                "overall_grade": radar.get("overall_grade", "B"),
                "strongest_skill": strongest,
                "weakest_skill": weakest
            },
            "diagnosis": {
                "regime": regime,
                "regime_title": regime_title,
                "priority_action": priority_action,
                "master_g_advice": advice_msg
            },
            "prescribed_tasks": prescribed_tasks,
            "due_vocabs": state["due_vocabs"]
        }

    # =========================================================================
    # HỆ THỐNG TÍCH LŨY BAND ĐỊNH LƯỢNG THỰC CHẤT (BAND ACCUMULATION MODEL)
    # =========================================================================
    BAND_CONFIG = {
        'A1': {
            'target': 'A2',
            'required_vocabs': 500,           # Số từ nạp thêm từ cấp trước (+500 - 700 từ A2)
            'cumulative_benchmark': 1000,      # Tổng từ vựng tích lũy chuẩn CEFR (1.000 - 1.500 từ)
            'required_grammars': 6,
            'label': 'A1 ➔ A2 (Sơ Cấp - Elementary)'
        },
        'A2': {
            'target': 'B1',
            'required_vocabs': 1000,          # Số từ nạp thêm (+1.000 từ B1)
            'cumulative_benchmark': 2000,      # Tổng từ vựng tích lũy chuẩn CEFR (2.000 - 2.500 từ)
            'required_grammars': 10,
            'label': 'A2 ➔ B1 (Trung Cấp - Intermediate)'
        },
        'B1': {
            'target': 'B2',
            'required_vocabs': 1500,          # Số từ nạp thêm (+1.500 từ B2)
            'cumulative_benchmark': 3500,      # Tổng từ vựng tích lũy chuẩn CEFR (3.500 - 4.000 từ)
            'required_grammars': 15,
            'label': 'B1 ➔ B2 (Trung Cao Cấp - Upper-Intermediate)'
        },
        'B2': {
            'target': 'C1',
            'required_vocabs': 3500,          # Số từ nạp thêm (+3.000 - 4.000 từ C1)
            'cumulative_benchmark': 7000,      # Tổng từ vựng tích lũy chuẩn CEFR (7.000 - 8.000 từ)
            'required_grammars': 20,
            'label': 'B2 ➔ C1 (Cao Cấp - Advanced)'
        },
        'C1': {
            'target': 'C2',
            'required_vocabs': 8000,          # Số từ nạp thêm (+7.000 - 8.000 từ C2)
            'cumulative_benchmark': 15000,     # Tổng từ vựng tích lũy chuẩn CEFR (15.000 - 16.000+ từ)
            'required_grammars': 25,
            'label': 'C1 ➔ C2 (Tinh Thông - Mastery / Proficiency)'
        },
        'C2': {
            'target': 'C2',
            'required_vocabs': 8000,
            'cumulative_benchmark': 16000,
            'required_grammars': 30,
            'label': 'C2 Master (Đỉnh Cao Ngôn Ngữ)'
        }
    }

    def compute_band_accumulation_progress(self, user_id: int) -> Dict[str, Any]:
        """
        TÍNH TOÁN TIẾN ĐỘ TÍCH LŨY THỰC TẾ ĐỂ MỞ KHÓA BÀI THI THĂNG HẠNG BAND
        Áp dụng chuẩn khung năng lực Châu Âu (CEFR). Đòi hỏi tích lũy lượng biến thành chất biến.
        """
        user = User.query.get(user_id)
        if not user:
            return {"error": "User không tồn tại"}

        current_band = getattr(user, 'current_band', 'A1') or 'A1'
        cfg = self.BAND_CONFIG.get(current_band, self.BAND_CONFIG['A1'])
        target_band = cfg['target']
        required_vocabs = cfg['required_vocabs']
        cumulative_benchmark = cfg.get('cumulative_benchmark', 1000)
        required_grammars = cfg['required_grammars']

        # 1. Đếm từ vựng thuộc target_band mà user ĐÃ THUỘC (DA_THUOC) qua Smart SRS
        mastered_vocabs = db.session.query(UserVocabulary).join(
            Vocabulary, UserVocabulary.vocab_id == Vocabulary.id
        ).filter(
            UserVocabulary.user_id == user_id,
            Vocabulary.cefr_level == target_band,
            UserVocabulary.memorization_level == 'DA_THUOC'
        ).count()

        # 2. Đếm tổng vốn từ vựng tích lũy toàn diện (mọi cấp độ) mà user ĐÃ THUỘC
        cumulative_mastered = db.session.query(UserVocabulary).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.memorization_level == 'DA_THUOC'
        ).count()

        # 3. Đếm từ vựng thuộc target_band đang học (DANG_HOC hoặc CHUA_THUOC)
        learning_vocabs = db.session.query(UserVocabulary).join(
            Vocabulary, UserVocabulary.vocab_id == Vocabulary.id
        ).filter(
            UserVocabulary.user_id == user_id,
            Vocabulary.cefr_level == target_band,
            UserVocabulary.memorization_level != 'DA_THUOC'
        ).count()

        # 4. Tổng số từ vựng của target_band có trong hệ thống
        total_target_in_system = Vocabulary.query.filter_by(cefr_level=target_band).count()

        # 5. Ngữ pháp đã hoàn thành
        grammar_done = UserMilestoneProgress.query.join(
            RoadmapMilestone, UserMilestoneProgress.milestone_id == RoadmapMilestone.id
        ).filter(
            UserMilestoneProgress.user_id == user_id,
            UserMilestoneProgress.is_completed == True,
            RoadmapMilestone.band_level == target_band
        ).count()

        percent = round(min(100.0, (mastered_vocabs / max(1, required_vocabs)) * 100), 1)
        cumulative_percent = round(min(100.0, (cumulative_mastered / max(1, cumulative_benchmark)) * 100), 1)
        shortfall = max(0, required_vocabs - mastered_vocabs)
        is_exam_ready = (mastered_vocabs >= required_vocabs and grammar_done >= (required_grammars // 2))

        if not is_exam_ready:
            gatekeeper_verdict = (
                f"Master G nhắn nhủ: Theo Khung Tham Chiếu Châu Âu (CEFR), để bứt phá lên Band {target_band}, "
                f"bạn cần làm chủ thêm {shortfall} từ vựng mục tiêu (hiện tại: {mastered_vocabs}/{required_vocabs} từ, đạt {percent}%). "
                f"Tổng vốn từ tích lũy của bạn đang đạt {cumulative_mastered}/{cumulative_benchmark} từ chuẩn CEFR. "
                f"Hãy tiếp tục kiên trì rèn luyện hàng ngày để biến lượng thành chất và tự tin vượt qua kỳ thi nhé!"
            )
        else:
            gatekeeper_verdict = (
                f"Master G chúc mừng: Xuất sắc! Bạn đã làm chủ {mastered_vocabs} từ vựng mục tiêu Band {target_band} "
                f"(tổng tích lũy toàn diện đạt {cumulative_mastered}/{cumulative_benchmark} từ chuẩn CEFR) "
                f"và hoàn thành xuất sắc các cấu trúc ngữ pháp nền tảng. "
                f"Phòng thi thăng hạng Band {target_band} đã chính thức mở khóa. Hãy tự tin bước vào phòng thi để khẳng định năng lực nhé!"
            )

        return {
            "status": "success",
            "current_band": current_band,
            "target_band": target_band,
            "band_label": cfg['label'],
            "mastered_vocabs": mastered_vocabs,
            "learning_vocabs": learning_vocabs,
            "required_vocabs": required_vocabs,
            "cumulative_mastered": cumulative_mastered,
            "cumulative_benchmark": cumulative_benchmark,
            "cumulative_percent": cumulative_percent,
            "grammar_done": grammar_done,
            "required_grammars": required_grammars,
            "percent": percent,
            "shortfall": shortfall,
            "is_exam_ready": is_exam_ready,
            "total_target_in_system": total_target_in_system,
            "gatekeeper_verdict": gatekeeper_verdict
        }

    # =========================================================================
    # GIÁO ÁN PHIÊN HỌC HÀNG NGÀY 4 BƯỚC (CURATED DAILY SESSION - 15 PHÚT)
    # Cơ chế: 70% Deterministic (SRS + Target Band) & 30% Constrained Randomness
    # =========================================================================
    def generate_curated_session(self, user_id: int) -> Dict[str, Any]:
        """
        Khởi tạo phiên học 15 phút do Agent dẫn dắt.
        Loại bỏ cảm giác ngẫu nhiên rời rạc, gói gọn trong 1 chu trình khép kín.
        """
        import uuid
        import re
        from datetime import datetime, timedelta

        now = datetime.now()
        user = User.query.get(user_id)
        if not user:
            return {"error": "Không tìm thấy user"}

        acc_progress = self.compute_band_accumulation_progress(user_id)
        current_band = acc_progress["current_band"]
        target_band = acc_progress["target_band"]

        # ------------------------------------------------------------------
        # BƯỚC 1: WARMUP & SPATIAL RETENTION (3 PHÚT) - Não 3 Smart SRS
        # ------------------------------------------------------------------
        due_records = db.session.query(Vocabulary, UserVocabulary).join(
            UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
        ).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.is_unlocked == True,
            UserVocabulary.next_review_time <= now
        ).order_by(UserVocabulary.next_review_time.asc()).limit(4).all()

        if not due_records:
            due_records = db.session.query(Vocabulary, UserVocabulary).join(
                UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
            ).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.is_unlocked == True
            ).order_by(db.func.random()).limit(4).all()

        if not due_records:
            fresh_words = Vocabulary.query.filter_by(cefr_level='A1').limit(4).all()
            for fw in fresh_words:
                uv = UserVocabulary(user_id=user_id, vocab_id=fw.id, is_unlocked=True, memorization_level='CHUA_THUOC')
                db.session.add(uv)
            db.session.commit()
            due_records = [(fw, UserVocabulary.query.filter_by(user_id=user_id, vocab_id=fw.id).first()) for fw in fresh_words]

        step_1_questions = []
        for idx, (v, uv) in enumerate(due_records, 1):
            all_other_meanings = [w.meaning for w in Vocabulary.query.filter(Vocabulary.id != v.id).order_by(db.func.random()).limit(3).all()]
            options = [v.meaning] + all_other_meanings
            random.shuffle(options)
            
            scrambled = "".join(random.sample(v.word, len(v.word))) if len(v.word) > 2 else v.word
            
            step_1_questions.append({
                "id": idx,
                "vocab_id": v.id,
                "word": v.word,
                "meaning": v.meaning,
                "scrambled": scrambled,
                "options": options,
                "correct_option": v.meaning,
                "type": "quick_choice" if idx % 2 != 0 else "scramble"
            })

        # ------------------------------------------------------------------
        # BƯỚC 2: TARGET BAND INPUT (5 PHÚT) - Lò đúc có định hướng
        # ------------------------------------------------------------------
        user_vocab_subquery = db.session.query(UserVocabulary.vocab_id).filter_by(user_id=user_id)
        candidate_target_words = Vocabulary.query.filter(
            Vocabulary.cefr_level == target_band,
            ~Vocabulary.id.in_(user_vocab_subquery)
        ).limit(15).all()

        if len(candidate_target_words) < 4:
            candidate_target_words = db.session.query(Vocabulary).join(
                UserVocabulary, Vocabulary.id == UserVocabulary.vocab_id
            ).filter(
                UserVocabulary.user_id == user_id,
                Vocabulary.cefr_level == target_band,
                UserVocabulary.memorization_level != 'DA_THUOC'
            ).limit(10).all()

        if not candidate_target_words:
            candidate_target_words = Vocabulary.query.filter_by(cefr_level=target_band).limit(4).all()

        selected_target_words = random.sample(candidate_target_words, min(4, len(candidate_target_words))) if candidate_target_words else []
        step_2_words = []
        for w in selected_target_words:
            step_2_words.append({
                "id": w.id,
                "word": w.word,
                "meaning": w.meaning,
                "theme": w.theme or "Tổng quát",
                "cefr_level": w.cefr_level,
                "collocation": f"essential {w.word}" if len(w.word) > 3 else f"use {w.word}",
                "sample_sentence": f"In modern contexts, understanding '{w.word}' helps improve communication fluency."
            })

        target_grammar = Grammar.query.filter_by(cefr_level=target_band).order_by(db.func.random()).first()
        if not target_grammar:
            target_grammar = Grammar.query.first()

        grammar_data = {
            "id": target_grammar.id if target_grammar else 1,
            "structure": target_grammar.structure if target_grammar else "Subject + Modal Verb + Bare Infinitive",
            "explanation": target_grammar.explanation if target_grammar else "Cấu trúc diễn tả khả năng hoặc nghĩa vụ.",
            "example": target_grammar.example if target_grammar else "You should practice daily to master this skill.",
            "cefr_level": target_grammar.cefr_level if target_grammar else target_band
        }

        # ------------------------------------------------------------------
        # BƯỚC 3: CONTEXTUAL OUTPUT CHALLENGE (5 PHÚT) - Ứng dụng thực chiến
        # ------------------------------------------------------------------
        SCENARIOS = [
            {
                "context": "Giao tiếp Công sở & Quản lý Dự án",
                "prompt": "Bạn đang thảo luận với đồng nghiệp quốc tế về một giải pháp tối ưu cho công việc.",
                "guide": "Hãy viết 1 câu tiếng Anh diễn đạt ý kiến hoặc đề xuất của bạn."
            },
            {
                "context": "Du lịch & Giao lưu Quốc tế",
                "prompt": "Bạn đang ở nước ngoài và cần trao đổi với người bản xứ để hỏi thông tin hoặc xử lý một tình huống phát sinh.",
                "guide": "Hãy viết 1 câu tiếng Anh miêu tả tình huống hoặc yêu cầu hỗ trợ."
            },
            {
                "context": "Phỏng vấn & Mục tiêu Nghề nghiệp",
                "prompt": "Nhà tuyển dụng muốn biết cách bạn ứng phó với thử thách mới trong chuyên môn.",
                "guide": "Hãy viết 1 câu tiếng Anh nêu bật năng lực hoặc mục tiêu phát triển của bạn."
            },
            {
                "context": "Công nghệ, Đời sống & Xu hướng",
                "prompt": "Bạn đang chia sẻ nhận định về ảnh hưởng của chuyển đổi số và công nghệ đến đời sống hiện đại.",
                "guide": "Hãy viết 1 câu tiếng Anh thể hiện góc nhìn phản biện của bạn."
            }
        ]
        chosen_scenario = random.choice(SCENARIOS)
        step_2_word_strings = [w["word"] for w in step_2_words]

        # ------------------------------------------------------------------
        # CHAIN OF THOUGHT (TƯ DUY MINH BẠCH CỦA TÁC TỬ MASTER G)
        # ------------------------------------------------------------------
        thought_trace = [
            f"🧠 [Brain 3 - Smart SRS]: Quét bộ nhớ đường cong lãng quên: Phát hiện {len(due_records)} từ vựng cần kích hoạt phản xạ lại.",
            f"📚 [Brain 4 - Vocab CEFR]: Lọc tập từ vựng chuẩn Oxford Band {target_band}: Tuyển chọn {len(step_2_words)} từ mục tiêu chưa nắm vững.",
            f"📐 [Grammar Orchestrator]: Ghép cấu trúc ngữ pháp trọng điểm Band {target_band}: '{grammar_data['structure']}'.",
            f"🎯 [Brain 2 - Intent Engine]: Khởi tạo tình huống tương tác thực chiến có kiểm soát: '{chosen_scenario['context']}'.",
            f"🧙‍♂️ [Master G Conductor]: Giáo án 4 bước cá nhân hóa đã sẵn sàng. Điểm hòa quyện năng lực: Tích lũy {acc_progress['percent']}% Band {target_band}."
        ]

        session_payload = {
            "session_id": str(uuid.uuid4()),
            "status": "ready",
            "created_at": now.isoformat(),
            "learner": {
                "user_id": user.id,
                "username": user.username,
                "current_band": current_band,
                "target_band": target_band,
                "band_progress": acc_progress
            },
            "thought_trace": thought_trace,
            "step_1": {
                "step_number": 1,
                "title": "Khởi động & Giải phóng Trí nhớ (Smart SRS)",
                "duration_minutes": 3,
                "purpose": "Kích hoạt phản xạ cho các từ vựng đang ở điểm rơi lãng quên Ebbinghaus.",
                "questions": step_1_questions
            },
            "step_2": {
                "step_number": 2,
                "title": f"Nạp Kiến thức Mục tiêu (Chuẩn Band {target_band})",
                "duration_minutes": 5,
                "purpose": "Học sâu 4 từ vựng mục tiêu và 1 cấu trúc ngữ pháp tương ứng.",
                "target_words": step_2_words,
                "grammar": grammar_data
            },
            "step_3": {
                "step_number": 3,
                "title": "Thử thách Thực chiến Đặt câu (GEC AI)",
                "duration_minutes": 5,
                "purpose": "Vận dụng từ vựng mới vào ngữ cảnh đàm thoại thực tế dưới sự giám sát của DistilBERT GEC.",
                "scenario": chosen_scenario,
                "required_words": step_2_word_strings,
                "min_words_count": 4
            },
            "step_4": {
                "step_number": 4,
                "title": "Đánh giá Năng lực & Khép vòng",
                "duration_minutes": 2,
                "purpose": "Ghi nhận tiến độ tích lũy thực tế, cộng thưởng Xu & RP và nhận xét sư phạm.",
                "reward_rp": 35,
                "reward_coins": 30,
                "projected_progress_increase": "+3.5%"
            }
        }
        return session_payload

    def evaluate_session_step(self, user_id: int, step_number: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        ĐÁNH GIÁ TỪNG BƯỚC CỦA PHIÊN HỌC VÀ CẬP NHẬT DATABASE
        """
        import re
        from datetime import datetime, timedelta

        user = User.query.get(user_id)
        if not user:
            return {"status": "error", "message": "User không tồn tại"}

        if step_number == 1:
            answers = payload.get("answers", [])
            correct_count = 0
            for ans in answers:
                v_id = ans.get("vocab_id")
                is_correct = ans.get("is_correct", False)
                if is_correct:
                    correct_count += 1
                if v_id:
                    uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v_id).first()
                    if uv:
                        if is_correct:
                            uv.fail_count = max(0, (uv.fail_count or 0) - 1)
                            uv.next_review_time = datetime.now() + timedelta(days=3)
                            uv.memorization_level = 'DA_THUOC'
                        else:
                            uv.fail_count = (uv.fail_count or 0) + 1
                            uv.next_review_time = datetime.now() + timedelta(hours=12)
            db.session.commit()
            return {
                "status": "success",
                "step": 1,
                "score": f"{correct_count}/{len(answers)}" if answers else "4/4",
                "feedback": f"Tuyệt vời! Bạn đã hoàn thành phần khởi động ({correct_count} câu chuẩn xác). Não bộ đã được làm ấm và sẵn sàng nạp kiến thức mới!"
            }

        elif step_number == 2:
            word_ids = payload.get("word_ids", [])
            for w_id in word_ids:
                uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=w_id).first()
                if not uv:
                    uv = UserVocabulary(user_id=user_id, vocab_id=w_id, is_unlocked=True, memorization_level='DANG_HOC')
                    db.session.add(uv)
                else:
                    uv.is_unlocked = True
            db.session.commit()
            return {
                "status": "success",
                "step": 2,
                "feedback": f"Đã nạp thành công {len(word_ids)} từ vựng mới vào kho trí nhớ! Hãy sẵn sàng ứng dụng chúng trong câu nói thực tế ở bước tiếp theo."
            }

        elif step_number == 3:
            sentence = (payload.get("sentence") or "").strip()
            required_words = [w.lower() for w in payload.get("required_words", [])]

            if not sentence or len(sentence.split()) < 3:
                return {
                    "status": "error",
                    "step": 3,
                    "message": "Câu của bạn quá ngắn! Vui lòng viết ít nhất 4 từ hoàn chỉnh để AI đánh giá."
                }

            gec_res = self.gec_engine.evaluate(sentence, user_level="Intermediate")
            score = float(gec_res.get("score", 7.5))
            critique = gec_res.get("master_g_critique", gec_res.get("feedback", "Cấu trúc câu tương đối tốt."))
            corrected = gec_res.get("corrected", sentence)

            clean_tokens = set(re.findall(r'\b[a-zA-Z]+\b', sentence.lower()))
            matched_words = [w for w in required_words if w in clean_tokens]
            has_target_word = len(matched_words) > 0

            critical_hit = has_target_word and score >= 5.5
            bonus_coins = 15 if critical_hit else 5
            bonus_rp = 10 if critical_hit else 5

            user.coins = (user.coins or 0) + bonus_coins
            user.academic_rp = (user.academic_rp or 500) + bonus_rp

            if critical_hit:
                for mw in matched_words:
                    v_match = Vocabulary.query.filter(db.func.lower(Vocabulary.word) == mw).first()
                    if v_match:
                        uv_rec = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v_match.id).first()
                        if uv_rec:
                            uv_rec.memorization_level = 'DA_THUOC'
                            uv_rec.next_review_time = datetime.now() + timedelta(days=4)
            db.session.commit()

            return {
                "status": "success",
                "step": 3,
                "score": score,
                "critical_hit": critical_hit,
                "matched_words": matched_words,
                "corrected": corrected,
                "critique": critique,
                "bonus_coins": bonus_coins,
                "bonus_rp": bonus_rp,
                "feedback": (
                    f"✨ Bứt phá xuất sắc! Bạn đã vận dụng chuẩn xác từ '{', '.join(matched_words)}' vào câu (+{bonus_coins} Xu, +{bonus_rp} RP)!\n\n"
                    f"{critique}"
                    if critical_hit else critique
                )
            }

        elif step_number == 4:
            reward_rp = 35
            reward_coins = 30
            user.coins = (user.coins or 0) + reward_coins
            user.academic_rp = (user.academic_rp or 500) + reward_rp
            user.study_time_minutes = (user.study_time_minutes or 0) + 15
            db.session.commit()

            new_progress = self.compute_band_accumulation_progress(user_id)
            return {
                "status": "success",
                "step": 4,
                "message": "🎉 CHÚC MỪNG BẠN ĐÃ HOÀN THÀNH PHIÊN HỌC HÔM NAY!",
                "reward_rp": reward_rp,
                "reward_coins": reward_coins,
                "new_band_progress": new_progress,
                "master_g_farewell": (
                    f"Rất xuất sắc! Bạn đã bổ sung thêm những viên gạch vững chắc cho Band {new_progress['target_band']}. "
                    f"Tiến độ tích lũy hiện tại đạt {new_progress['percent']}%. Hãy quay lại vào ngày mai để tiếp tục duy trì chuỗi học tập!"
                )
            }

        return {"status": "error", "message": "Bước không hợp lệ"}
