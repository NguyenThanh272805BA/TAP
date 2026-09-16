import os
import json
import random
import re
from typing import Dict, List, Any, Optional

from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.models.user_vocabulary import UserVocabulary
from app.models.user_grammar import UserGrammar
from app.ml_models.gec_engine import LocalGECEngine
from app.ml_models.critique_synthesizer import LocalCritiqueSynthesizer
from app.ml_models.scramble_engine import LocalScrambleEngine
from app import db

# Khởi tạo các Core AI Local dùng chung (Lazy/Singleton)
gec_engine = LocalGECEngine(lazy=True)
critique_synthesizer = LocalCritiqueSynthesizer()
scramble_engine = LocalScrambleEngine()


class LocalExamEngine:
    """
    ĐỘNG CƠ SINH ĐỀ THI & CHẨN ĐOÁN NĂNG LỰC CEFR TỰ ĐỘNG 100% LOCAL (AI-First)
    Độc lập hoàn toàn với Cloud LLM.
    Hỗ trợ sinh đề chuẩn hóa theo từng Band (A1-C2), đề Placement Test, và đề chẩn đoán điểm yếu cá nhân.
    """

    CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    # Ngân hàng mẫu câu ngữ cảnh phong phú theo CEFR để sinh câu hỏi trắc nghiệm
    CONTEXT_TEMPLATES = {
        'A1': [
            ("Every morning, my mother goes to the market to buy fresh [ _____ ].", "vegetables"),
            ("The students are sitting in the [ _____ ] and listening to the teacher.", "classroom"),
            ("Can you help me carry this heavy [ _____ ] to the car?", "box"),
            ("I like to drink a glass of warm [ _____ ] before going to bed.", "milk"),
            ("Look at the sky! The [ _____ ] is shining brightly today.", "sun"),
            ("He rides his [ _____ ] to school every single day.", "bicycle"),
            ("She wears a warm woolen [ _____ ] in the winter.", "coat"),
            ("My little sister loves to play with her cute [ _____ ].", "cat")
        ],
        'A2': [
            ("Because of the heavy rain, our flight was delayed by two [ _____ ].", "hours"),
            ("He checked the bus [ _____ ] to make sure he would not miss the last ride.", "schedule"),
            ("You should keep your passport in a safe [ _____ ] while traveling.", "place"),
            ("She felt very [ _____ ] after working twelve hours continuously.", "exhausted"),
            ("This new restaurant offers delicious food at a reasonable [ _____ ].", "price"),
            ("We decided to spend our summer [ _____ ] near the seaside.", "vacation")
        ],
        'B1': [
            ("The government launched a new campaign to raise public [ _____ ] of clean energy.", "awareness"),
            ("Regular physical exercise has a profound [ _____ ] on mental health.", "effect"),
            ("She demonstrated great [ _____ ] by solving the complex problem in minutes.", "intelligence"),
            ("The company decided to [ _____ ] its production capacity to meet growing demand.", "expand"),
            ("His strong communication skills gave him a significant [ _____ ] in the interview.", "advantage"),
            ("We need to protect the natural [ _____ ] of endangered wildlife species.", "environment")
        ],
        'B2': [
            ("The board of directors reached a unanimous [ _____ ] regarding the merger.", "decision"),
            ("Scientific evidence contradicts the initial [ _____ ] proposed by earlier researchers.", "hypothesis"),
            ("The sudden market collapse was completely [ _____ ] by financial analysts.", "unforeseen"),
            ("Technological advancements have greatly [ _____ ] global cross-border communication.", "facilitated"),
            ("The candidate's extensive international experience made him exceptionally [ _____ ].", "qualified"),
            ("Addressing climate change requires global cooperation and collective [ _____ ].", "responsibility")
        ],
        'C1': [
            ("The politician's speech was filled with ambiguous rhetoric to [ _____ ] public scrutiny.", "evade"),
            ("The researchers adopted an empirical [ _____ ] to test their mathematical model.", "methodology"),
            ("Her groundbreaking findings generated [ _____ ] discussions within the academic community.", "vigorous"),
            ("The intricate mechanism demonstrated unprecedented [ _____ ] and structural resilience.", "sophistication"),
            ("Technological innovation has begun to [ _____ ] obsolete industrial paradigms.", "supersede"),
            ("He possessed an almost intuitive [ _____ ] into complex geopolitical dynamics.", "comprehension")
        ],
        'C2': [
            ("The philosopher articulated an [ _____ ] defense of ethical consequentialism.", "impeccable"),
            ("Such an egregious oversight is completely [ _____ ] in modern cryptographic systems.", "unacceptable"),
            ("The subtle nuances of dialectical reasoning require deep intellectual [ _____ ].", "perspicacity"),
            ("Their revolutionary paradigm was met with vehement [ _____ ] from dogmatic circles.", "repudiation"),
            ("Economic turbulence precipitated widespread [ _____ ] across speculative markets.", "destabilization")
        ]
    }

    # Ngân hàng mẫu câu lỗi sai có chủ đích để sinh câu hỏi Error Spotting
    GRAMMAR_ERROR_BANK = {
        'A1': [
            {
                "incorrect": "She go to school by bus every morning.",
                "error_token": "go",
                "correction": "goes",
                "rule": "Chủ ngữ ngôi thứ 3 số ít 'She' thì Hiện tại đơn cần chia động từ thêm 's/es' (goes).",
                "options": ["go -> goes", "school -> schools", "bus -> buses", "morning -> mornings"]
            },
            {
                "incorrect": "He do not like drinking cold milk.",
                "error_token": "do not",
                "correction": "does not",
                "rule": "Chủ ngữ ngôi thứ 3 số ít 'He' sử dụng trợ động từ phủ định 'does not', không dùng 'do not'.",
                "options": ["do not -> does not", "like -> likes", "drinking -> drink", "cold -> colds"]
            },
            {
                "incorrect": "There is many books on the library table.",
                "error_token": "is",
                "correction": "are",
                "rule": "Danh từ số nhiều 'many books' đi với cấu trúc 'There are', không dùng 'There is'.",
                "options": ["is -> are", "many -> much", "table -> tables", "books -> book"]
            }
        ],
        'A2': [
            {
                "incorrect": "Yesterday, we visit our grandparents in the countryside.",
                "error_token": "visit",
                "correction": "visited",
                "rule": "Dấu hiệu thời gian trong quá khứ 'Yesterday' yêu cầu động từ chia thì Quá khứ đơn (visited).",
                "options": ["visit -> visited", "our -> ours", "countryside -> countrysides", "Yesterday -> Tomorrow"]
            },
            {
                "incorrect": "This laptop is more cheaper than that desktop computer.",
                "error_token": "more cheaper",
                "correction": "cheaper",
                "rule": "'Cheap' là tính từ ngắn nên so sánh hơn chỉ dùng 'cheaper', không dùng thừa 'more'.",
                "options": ["more cheaper -> cheaper", "than -> then", "that -> those", "is -> are"]
            },
            {
                "incorrect": "You must to complete this assignment before Friday.",
                "error_token": "must to complete",
                "correction": "must complete",
                "rule": "Động từ khuyết thiếu 'must' đi trực tiếp với động từ nguyên thể không to (V-inf).",
                "options": ["must to complete -> must complete", "this -> these", "before -> after", "Friday -> Fridays"]
            }
        ],
        'B1': [
            {
                "incorrect": "She has lived here since five years.",
                "error_token": "since",
                "correction": "for",
                "rule": "'Five years' là một khoảng thời gian, bắt buộc dùng giới từ 'for' thay vì 'since'.",
                "options": ["since -> for", "has lived -> lived", "here -> there", "years -> year"]
            },
            {
                "incorrect": "If it will rain tomorrow, the football match will be cancelled.",
                "error_token": "will rain",
                "correction": "rains",
                "rule": "Trong mệnh đề If của câu điều kiện loại 1, động từ chia ở thì Hiện tại đơn (rains), không dùng 'will'.",
                "options": ["will rain -> rains", "the -> a", "will be -> would be", "cancelled -> cancel"]
            },
            {
                "incorrect": "The novel was wrote by Ernest Hemingway in 1952.",
                "error_token": "wrote",
                "correction": "written",
                "rule": "Cấu trúc câu bị động 'was + V3/ed', phân từ 2 của 'write' là 'written'.",
                "options": ["wrote -> written", "The -> A", "by -> with", "in -> at"]
            }
        ],
        'B2': [
            {
                "incorrect": "If I was you, I would consult a medical specialist immediately.",
                "error_token": "was",
                "correction": "were",
                "rule": "Trong câu điều kiện loại 2 giả định, to be dùng chuẩn là 'were' cho tất cả các ngôi.",
                "options": ["was -> were", "would consult -> will consult", "immediately -> immediate", "medical -> medicine"]
            },
            {
                "incorrect": "By the time the ambulance arrived, the patient passed away.",
                "error_token": "passed away",
                "correction": "had passed away",
                "rule": "Hành động xảy ra trước một mốc trong quá khứ ('By the time... arrived') phải chia thì Quá khứ hoàn thành (had passed away).",
                "options": ["passed away -> had passed away", "arrived -> arrives", "the -> a", "patient -> patients"]
            },
            {
                "incorrect": "It is high time we start taking cybersecurity threats seriously.",
                "error_token": "start",
                "correction": "started",
                "rule": "Cấu trúc 'It is high time + S + V(past)' bắt buộc lùi động từ về quá khứ đơn (started).",
                "options": ["start -> started", "taking -> to take", "threats -> threat", "seriously -> serious"]
            }
        ],
        'C1': [
            {
                "incorrect": "Not only he passed the rigorous test, but he also broke the national record.",
                "error_token": "he passed",
                "correction": "did he pass",
                "rule": "Đứng đầu câu bằng cụm phủ định 'Not only' bắt buộc phải dùng đảo ngữ trợ động từ (did he pass).",
                "options": ["he passed -> did he pass", "broke -> broken", "national -> nation", "also -> as well"]
            },
            {
                "incorrect": "Had they listened to the warning, the catastrophe would be avoided.",
                "error_token": "would be avoided",
                "correction": "would have been avoided",
                "rule": "Mệnh đề đảo ngữ điều kiện loại 3 'Had they listened' yêu cầu mệnh đề chính là 'would have been avoided'.",
                "options": ["would be avoided -> would have been avoided", "listened -> listen", "catastrophe -> catastrophic", "warning -> warn"]
            }
        ],
        'C2': [
            {
                "incorrect": "No sooner had the keynote finished when spontaneous applause erupted.",
                "error_token": "when",
                "correction": "than",
                "rule": "Cấu trúc đảo ngữ kép 'No sooner had + S + V3' bắt buộc đi liền với liên từ 'than', không dùng 'when'.",
                "options": ["when -> than", "had the keynote finished -> the keynote had finished", "erupted -> erupts", "applause -> applauses"]
            },
            {
                "incorrect": "It is imperative that every delegate attends the plenary session on time.",
                "error_token": "attends",
                "correction": "attend",
                "rule": "Thể giả định thức (Subjunctive): 'It is imperative that S + V-inf' động từ giữ nguyên mẫu không chia (attend).",
                "options": ["attends -> attend", "every -> all", "on time -> in time", "plenary -> plenarily"]
            }
        ]
    }

    def __init__(self):
        self.oxford_words_by_level = self._load_oxford_by_level()

    def _load_oxford_by_level(self) -> Dict[str, List[str]]:
        """Tải và phân loại 4961 từ Oxford 5000 thành các nhóm CEFR"""
        res = {lvl: [] for lvl in self.CEFR_LEVELS}
        oxford_path = os.path.join(os.path.dirname(__file__), 'oxford_5000.json')
        if os.path.exists(oxford_path):
            try:
                with open(oxford_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for word, lvl in data.items():
                        lvl_upper = lvl.upper() if isinstance(lvl, str) else 'A1'
                        if lvl_upper in res:
                            res[lvl_upper].append(word)
            except Exception as e:
                print(f"[EXAM ENGINE] Lỗi nạp oxford_5000: {e}")
        return res

    def _get_distractors_for_word(self, target_word: str, band: str, count: int = 3) -> List[str]:
        """Tạo các đáp án nhiễu (distractors) cùng band CEFR từ Oxford / Vocabulary"""
        candidates = self.oxford_words_by_level.get(band, [])
        if not candidates or len(candidates) < count:
            candidates = self.oxford_words_by_level.get('A1', []) + self.oxford_words_by_level.get('A2', [])

        # Lọc bỏ từ mục tiêu và các từ quá ngắn / trùng lặp
        filtered = [w for w in candidates if w.lower() != target_word.lower() and len(w) > 2]
        if len(filtered) < count:
            # Fallback từ DB Vocabulary
            db_words = [v.word for v in Vocabulary.query.filter_by(cefr_level=band).limit(20).all()]
            filtered.extend([w for w in db_words if w.lower() != target_word.lower()])

        if len(filtered) >= count:
            return random.sample(filtered, count)
        return ["important", "different", "possible"][:count]

    def generate_mock_exam(self, band: str = 'ALL', num_questions: int = 10, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Sinh đề thi thử chuẩn mực tự động 100% bằng AI Local.
        - band: 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', hoặc 'ALL' (Placement Test)
        - num_questions: Thường là 5 (Quick Mini Test) hoặc 10 (Standard Test)
        """
        band = band.upper()
        if band not in self.CEFR_LEVELS and band != 'ALL':
            band = 'ALL'

        exam_title = f"ĐỀ THI THỬ CHUẨN CEFR BAND {band}" if band != 'ALL' else "ĐỀ THI ĐÁNH GIÁ NĂNG LỰC TOÀN DIỆN (PLACEMENT TEST)"
        time_limit_minutes = max(5, int(num_questions * 1.5))

        questions = []
        q_id = 1

        # Xác định dải phân bổ band cho từng câu hỏi
        if band == 'ALL':
            # Phân bổ tăng dần độ khó: 2 câu A1-A2, 3 câu B1, 3 câu B2, 2 câu C1-C2
            target_bands = ['A1', 'A2', 'B1', 'B1', 'B2', 'B2', 'B2', 'C1', 'C1', 'C2'][:num_questions]
            while len(target_bands) < num_questions:
                target_bands.append('B1')
        else:
            target_bands = [band] * num_questions

        # Tỷ lệ các dạng câu:
        # 40% MCQ Vocab, 30% Error Spotting, 20% Syntax Scramble, 10% Writing
        for i, current_band in enumerate(target_bands):
            # Chọn loại câu hỏi luân phiên
            mod = i % 10
            if mod in [0, 2, 4, 7]:
                q_type = 'mcq_vocab'
            elif mod in [1, 5, 8]:
                q_type = 'error_spotting'
            elif mod in [3, 6]:
                q_type = 'syntax_scramble'
            else:
                q_type = 'writing_challenge'

            if q_type == 'mcq_vocab':
                q_data = self._build_mcq_vocab_question(q_id, current_band)
            elif q_type == 'error_spotting':
                q_data = self._build_error_spotting_question(q_id, current_band)
            elif q_type == 'syntax_scramble':
                q_data = self._build_syntax_scramble_question(q_id, current_band)
            else:
                q_data = self._build_writing_question(q_id, current_band)

            questions.append(q_data)
            q_id += 1

        # Tách cấu trúc đề thi thành 2 bản:
        # 1. client_exam: Ẩn các đáp án đúng và lời giải (gửi ra trình duyệt)
        # 2. answer_key: Lưu đáp án chính xác để đối soát khi nộp bài
        client_questions = []
        answer_key = {}

        for q in questions:
            client_q = {
                "id": q["id"],
                "type": q["type"],
                "band": q["band"],
                "section": q["section"],
                "prompt": q["prompt"],
                "options": q.get("options", []),
                "scrambled_chunks": q.get("scrambled_chunks", []),
                "hint": q.get("hint", "")
            }
            client_questions.append(client_q)

            answer_key[str(q["id"])] = {
                "correct_answer": q.get("correct_answer", ""),
                "correct_index": q.get("correct_index", -1),
                "type": q["type"],
                "band": q["band"],
                "explanation": q.get("explanation", ""),
                "rule": q.get("rule", ""),
                "target_word": q.get("target_word", ""),
                "target_grammar": q.get("target_grammar", "")
            }

        return {
            "status": "success",
            "exam_id": f"exam_{band.lower()}_{int(random.random() * 100000)}",
            "title": exam_title,
            "band": band,
            "total_questions": len(questions),
            "time_limit_minutes": time_limit_minutes,
            "questions": client_questions,
            "answer_key": answer_key  # Có thể lưu trong session Flask
        }

    def _build_mcq_vocab_question(self, q_id: int, band: str) -> Dict:
        """Tạo câu hỏi trắc nghiệm từ vựng theo ngữ cảnh"""
        templates = self.CONTEXT_TEMPLATES.get(band, self.CONTEXT_TEMPLATES['A1'])
        template, target_word = random.choice(templates)

        distractors = self._get_distractors_for_word(target_word, band, 3)
        options = distractors + [target_word]
        random.shuffle(options)
        correct_index = options.index(target_word)

        return {
            "id": q_id,
            "type": "mcq_vocab",
            "band": band,
            "section": "Phần 1: Trắc Nghiệm Từ Vựng Ngữ Cảnh",
            "prompt": f"Chọn từ thích hợp nhất để điền vào chỗ trống:\n\n\"{template}\"",
            "options": options,
            "correct_answer": target_word,
            "correct_index": correct_index,
            "explanation": f"Từ đúng là '{target_word}'. Câu hoàn chỉnh: {template.replace('[ _____ ]', target_word)}",
            "hint": f"Từ vựng thuộc cấp độ CEFR [{band}]."
        }

    def _build_error_spotting_question(self, q_id: int, band: str) -> Dict:
        """Tạo câu hỏi nhận diện & sửa lỗi sai ngữ pháp"""
        error_list = self.GRAMMAR_ERROR_BANK.get(band, self.GRAMMAR_ERROR_BANK['A1'])
        item = random.choice(error_list)

        options = item["options"].copy()
        correct_answer = options[0]  # Tùy chọn đầu tiên trong list là đáp án chuẩn
        random.shuffle(options)
        correct_index = options.index(correct_answer)

        return {
            "id": q_id,
            "type": "error_spotting",
            "band": band,
            "section": "Phần 2: Nhận Diện & Sửa Lỗi Sai Ngữ Pháp",
            "prompt": f"Xác định lỗi sai và chọn phương án sửa chính xác cho câu sau:\n\n\"{item['incorrect']}\"",
            "options": options,
            "correct_answer": correct_answer,
            "correct_index": correct_index,
            "explanation": f"Phương án sửa đúng: {correct_answer}. {item['rule']}",
            "rule": item["rule"],
            "hint": "Hãy chú ý đến quy tắc hòa hợp chủ vị hoặc cách chia thì/trợ động từ."
        }

    def _build_syntax_scramble_question(self, q_id: int, band: str) -> Dict:
        """Tạo câu hỏi sắp xếp / lắp ráp cú pháp câu chuẩn"""
        # Lấy một cấu trúc ngữ pháp tương ứng trong DB
        grammars = Grammar.query.filter_by(cefr_level=band).all()
        if not grammars:
            grammars = Grammar.query.filter_by(cefr_level='A1').all()

        grammar = random.choice(grammars) if grammars else None
        example = grammar.example if grammar and grammar.example else "She plays tennis every Sunday."
        structure = grammar.structure if grammar else "S + V + O"

        # Tách tokens
        clean_sentence = example.replace('.', '').replace('?', '').replace('!', '').strip()
        tokens = clean_sentence.split()
        shuffled = tokens.copy()
        if len(shuffled) > 1:
            random.shuffle(shuffled)

        # Tạo 4 phương án trật tự câu hoàn chỉnh
        correct_sentence = example.strip()
        distractors = [
            " ".join(reversed(tokens)) + ".",
            " ".join(shuffled) + ".",
            " ".join(tokens[1:] + [tokens[0]]) + "."
        ]
        options = [correct_sentence] + [d for d in distractors if d != correct_sentence][:3]
        while len(options) < 4:
            options.append(" ".join(random.sample(tokens, len(tokens))) + ".")
        random.shuffle(options)
        correct_index = options.index(correct_sentence)

        return {
            "id": q_id,
            "type": "syntax_scramble",
            "band": band,
            "section": "Phần 3: Lắp Ráp Cú Pháp & Trật Tự Câu",
            "prompt": f"Hãy sắp xếp các mảnh từ sau thành một câu tiếng Anh hoàn chỉnh đúng ngữ pháp [{structure}]:\n\n[ {' / '.join(shuffled)} ]",
            "scrambled_chunks": shuffled,
            "options": options,
            "correct_answer": correct_sentence,
            "correct_index": correct_index,
            "explanation": f"Câu chuẩn xác là: '{correct_sentence}' (Cấu trúc: {structure}).",
            "target_grammar": structure,
            "hint": f"Cấu trúc ngữ pháp áp dụng: {structure}."
        }

    def _build_writing_question(self, q_id: int, band: str) -> Dict:
        """Tạo câu hỏi thử thách viết câu tự luận chấm bằng AI Master G"""
        grammars = Grammar.query.filter_by(cefr_level=band).all()
        grammar = random.choice(grammars) if grammars else None
        structure = grammar.structure if grammar else "S + V + O"

        # Lấy 1 từ vựng tương ứng
        words = self.oxford_words_by_level.get(band, ["English", "study", "learn"])
        target_word = random.choice(words) if words else "study"

        return {
            "id": q_id,
            "type": "writing_challenge",
            "band": band,
            "section": "Phần 4: Thử Thách Đặt Câu Tự Luận",
            "prompt": f"Hãy viết một câu tiếng Anh hoàn chỉnh có chứa từ '{target_word}' và áp dụng cấu trúc ngữ pháp '{structure}'.",
            "target_word": target_word,
            "target_grammar": structure,
            "explanation": f"Hệ thống Local AI Master G sẽ chấm điểm câu của bạn dựa trên tính trọn vẹn ngữ pháp và sự xuất hiện của từ '{target_word}'.",
            "hint": "Đảm bảo câu có đầy đủ Chủ ngữ và Động từ vị ngữ, tránh nhập cụm từ què cụt."
        }

    def evaluate_mock_exam(self, user_answers: Dict[str, Any], answer_key: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Chấm điểm bài thi thử tự động 100% bằng AI Local.
        Phân tích chi tiết năng lực theo từng kỹ năng và ước tính CEFR Band.
        """
        total_questions = len(answer_key)
        if total_questions == 0:
            return {"error": "Không tìm thấy dữ liệu đề thi đối soát."}

        correct_count = 0
        section_stats = {
            "vocab": {"correct": 0, "total": 0},
            "grammar": {"correct": 0, "total": 0},
            "syntax": {"correct": 0, "total": 0},
            "writing": {"correct": 0, "total": 0, "scores": []}
        }
        question_results = []

        for q_id_str, key_info in answer_key.items():
            q_type = key_info.get("type", "mcq_vocab")
            band = key_info.get("band", "A1")
            user_ans = str(user_answers.get(q_id_str, "")).strip()

            is_correct = False
            awarded_score = 0.0
            ai_comment = ""

            if q_type in ['mcq_vocab', 'error_spotting', 'syntax_scramble']:
                correct_ans = str(key_info.get("correct_answer", "")).strip()
                correct_idx = key_info.get("correct_index", -1)

                # Đối soát theo text đáp án hoặc theo index (A/B/C/D)
                if user_ans.lower() == correct_ans.lower() or (user_ans.isdigit() and int(user_ans) == correct_idx):
                    is_correct = True
                    awarded_score = 1.0
                    correct_count += 1

                if q_type == 'mcq_vocab':
                    section_stats["vocab"]["total"] += 1
                    if is_correct: section_stats["vocab"]["correct"] += 1
                elif q_type == 'error_spotting':
                    section_stats["grammar"]["total"] += 1
                    if is_correct: section_stats["grammar"]["correct"] += 1
                elif q_type == 'syntax_scramble':
                    section_stats["syntax"]["total"] += 1
                    if is_correct: section_stats["syntax"]["correct"] += 1

                ai_comment = "Chính xác!" if is_correct else f"Chưa chính xác. Đáp án đúng: {correct_ans}."

            elif q_type == 'writing_challenge':
                section_stats["writing"]["total"] += 1
                target_word = key_info.get("target_word", "")
                
                if not user_ans:
                    awarded_score = 0.0
                    ai_comment = "Bạn chưa nhập câu trả lời cho câu hỏi này."
                else:
                    # Đánh giá bằng GECEngine cục bộ
                    eval_result = gec_engine.evaluate(user_ans)
                    writing_score = eval_result["score"]  # 0.0 - 10.0
                    
                    # Kiểm tra sự xuất hiện của từ khóa bắt buộc
                    if target_word and not re.search(rf"\b{re.escape(target_word)}\b", user_ans, re.IGNORECASE):
                        writing_score = max(2.0, writing_score - 3.0)
                        ai_comment = f"[Thiếu từ khóa '{target_word}'] "

                    # Sinh nhận xét sư phạm Master G
                    feedback_text = critique_synthesizer.synthesize(
                        user_input=user_ans,
                        gec_result=eval_result,
                        user_level=band
                    )
                    ai_comment += feedback_text
                    
                    # Quy đổi điểm viết sang tỷ lệ câu
                    normalized_score = writing_score / 10.0
                    awarded_score = normalized_score
                    if writing_score >= 6.0:
                        is_correct = True
                        correct_count += 1
                    section_stats["writing"]["scores"].append(writing_score)

            question_results.append({
                "question_id": int(q_id_str),
                "type": q_type,
                "band": band,
                "user_answer": user_ans,
                "correct_answer": key_info.get("correct_answer", ""),
                "is_correct": is_correct,
                "awarded_score": round(awarded_score, 2),
                "explanation": key_info.get("explanation", ""),
                "ai_feedback": ai_comment
            })

        # Tính toán điểm số tổng hợp trên thang 10
        total_points = sum(r["awarded_score"] for r in question_results)
        final_score_10 = round((total_points / total_questions) * 10.0, 1)
        percentage = round((total_points / total_questions) * 100, 1)

        # Tính điểm thành phần subscores
        subscores = {}
        for sec in ["vocab", "grammar", "syntax"]:
            st = section_stats[sec]
            subscores[sec] = round((st["correct"] / st["total"]) * 10.0, 1) if st["total"] > 0 else 10.0

        if section_stats["writing"]["total"] > 0:
            w_scores = section_stats["writing"]["scores"]
            subscores["writing"] = round(sum(w_scores) / len(w_scores), 1) if w_scores else 0.0
        else:
            subscores["writing"] = subscores["grammar"]

        # Ước tính CEFR Band đạt được
        if final_score_10 >= 9.0:
            estimated_band = "C2"
            band_title = "C2 - Độc Cô Cầu Bại (Mastery)"
        elif final_score_10 >= 7.5:
            estimated_band = "C1"
            band_title = "C1 - Cao Cấp (Effective Operational)"
        elif final_score_10 >= 6.0:
            estimated_band = "B2"
            band_title = "B2 - Trung Cao Cấp (Vantage)"
        elif final_score_10 >= 4.5:
            estimated_band = "B1"
            band_title = "B1 - Trung Cấp (Threshold)"
        elif final_score_10 >= 3.0:
            estimated_band = "A2"
            band_title = "A2 - Sơ Cấp (Waystage)"
        else:
            estimated_band = "A1"
            band_title = "A1 - Tân Binh (Breakthrough)"

        # Thưởng xu dựa trên thành tích thi
        coins_reward = 35 if final_score_10 >= 8.0 else (20 if final_score_10 >= 5.0 else 10)

        # Phân tích điểm yếu & Lời khuyên chẩn đoán
        weaknesses = []
        if subscores["vocab"] < 6.0:
            weaknesses.append("Kho từ vựng cần trau dồi thêm ngữ cảnh ứng dụng thực tế.")
        if subscores["grammar"] < 6.0:
            weaknesses.append("Nhận diện các thì và quy tắc hòa hợp chủ vị còn nhầm lẫn.")
        if subscores["syntax"] < 6.0:
            weaknesses.append("Cần rèn luyện thêm trật tự câu và các liên từ đảo ngữ.")
        if subscores["writing"] < 6.0:
            weaknesses.append("Kỹ năng diễn đạt tự luận cần chú ý tính trọn vẹn của vị ngữ.")

        diagnostic_advice = (
            f"Bạn đã đạt {final_score_10}/10 Điểm ({percentage}%). "
            + (" ".join(weaknesses) if weaknesses else "Năng lực ngôn ngữ của bạn rất toàn diện và vững vàng!")
        )

        return {
            "status": "success",
            "final_score": final_score_10,
            "percentage": percentage,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "estimated_band": estimated_band,
            "band_title": band_title,
            "subscores": subscores,
            "coins_reward": coins_reward,
            "diagnostic_advice": diagnostic_advice,
            "question_results": question_results
        }
