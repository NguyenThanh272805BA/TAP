import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.grammar import Grammar
from app.models.user_grammar import UserGrammar
from sqlalchemy import text

app = create_app()

CEFR_GRAMMAR_DEFINITIONS = [
    # Band A1 - Tân Binh Ngơ Ngác (Điểm 1 - 2)
    {
        "structure": "Subject + Verb + Object (SVO)",
        "explanation": "Cấu trúc câu cơ bản nhất trong tiếng Anh: Chủ ngữ thực hiện hành động lên Tân ngữ.",
        "example": "I study English every day.",
        "cefr_level": "A1",
        "category": "Sentence Structure",
        "difficulty_score": 1
    },
    {
        "structure": "S + V(s/es) + O",
        "explanation": "Thì Hiện tại đơn: Diễn tả thói quen, chân lý hoặc sự thật hiển nhiên.",
        "example": "She plays tennis every Sunday.",
        "cefr_level": "A1",
        "category": "Tenses",
        "difficulty_score": 1
    },
    {
        "structure": "S + is/am/are + V-ing",
        "explanation": "Thì Hiện tại tiếp diễn: Diễn tả một hành động đang diễn ra tại thời điểm nói.",
        "example": "They are studying in the library right now.",
        "cefr_level": "A1",
        "category": "Tenses",
        "difficulty_score": 2
    },
    {
        "structure": "There is / There are + Noun",
        "explanation": "Cấu trúc tồn tại: Chỉ sự hiện diện của một hoặc nhiều vật/người ở một vị trí.",
        "example": "There are many books on the desk.",
        "cefr_level": "A1",
        "category": "Sentence Structure",
        "difficulty_score": 1
    },
    {
        "structure": "S + can / cannot + V-inf",
        "explanation": "Động từ khiếm khuyết cơ bản: Diễn tả khả năng làm việc gì trong hiện tại.",
        "example": "He can speak three languages fluently.",
        "cefr_level": "A1",
        "category": "Modals",
        "difficulty_score": 2
    },

    # Band A2 - Sơ Cấp (Điểm 3 - 4)
    {
        "structure": "S + V(ed)/V2 + O",
        "explanation": "Thì Quá khứ đơn: Diễn tả hành động đã bắt đầu và kết thúc trọn vẹn trong quá khứ.",
        "example": "We visited London last summer.",
        "cefr_level": "A2",
        "category": "Tenses",
        "difficulty_score": 3
    },
    {
        "structure": "S + was/were + V-ing",
        "explanation": "Thì Quá khứ tiếp diễn: Diễn tả hành động đang xảy ra tại một thời điểm xác định trong quá khứ.",
        "example": "I was reading a novel at 8 PM yesterday.",
        "cefr_level": "A2",
        "category": "Tenses",
        "difficulty_score": 3
    },
    {
        "structure": "S + be going to + V-inf",
        "explanation": "Thì Tương lai gần: Diễn đạt kế hoạch hoặc dự đoán có căn cứ ở hiện tại.",
        "example": "Look at those dark clouds; it is going to rain.",
        "cefr_level": "A2",
        "category": "Tenses",
        "difficulty_score": 3
    },
    {
        "structure": "Comparative: S1 + V + adj-er / more adj + than S2",
        "explanation": "So sánh hơn: Dùng để so sánh sự khác biệt giữa hai đối tượng.",
        "example": "This smartphone is more expensive than that one.",
        "cefr_level": "A2",
        "category": "Comparatives",
        "difficulty_score": 3
    },
    {
        "structure": "S + should / must + V-inf",
        "explanation": "Lời khuyên và Nghĩa vụ: Should dùng cho lời khuyên, Must dùng cho sự bắt buộc.",
        "example": "You should drink more water every day.",
        "cefr_level": "A2",
        "category": "Modals",
        "difficulty_score": 4
    },

    # Band B1 - Trung Cấp (Điểm 5 - 6)
    {
        "structure": "S + have/has + V3/ed",
        "explanation": "Thì Hiện tại hoàn thành: Diễn tả trải nghiệm hoặc hành động bắt đầu ở quá khứ còn liên hệ hiện tại.",
        "example": "She has worked for this technology company for five years.",
        "cefr_level": "B1",
        "category": "Tenses",
        "difficulty_score": 5
    },
    {
        "structure": "If + S + V(present), S + will + V-inf",
        "explanation": "Câu điều kiện loại 1: Giả định một khả năng có thật và có thể xảy ra ở hiện tại hoặc tương lai.",
        "example": "If the weather is good tomorrow, we will go hiking.",
        "cefr_level": "B1",
        "category": "Conditionals",
        "difficulty_score": 5
    },
    {
        "structure": "Passive Voice: S + be + V3/ed (+ by Agent)",
        "explanation": "Câu bị động cơ bản: Nhấn mạnh vào đối tượng chịu tác động của hành động thay vì người thực hiện.",
        "example": "The historic bridge was restored by city engineers.",
        "cefr_level": "B1",
        "category": "Passive Voice",
        "difficulty_score": 5
    },
    {
        "structure": "Relative Clauses: Who / Which / That",
        "explanation": "Mệnh đề quan hệ xác định: Bổ nghĩa cho danh từ đứng trước, kết nối hai ý chặt chẽ.",
        "example": "The scientist who discovered the cure received an international award.",
        "cefr_level": "B1",
        "category": "Clauses",
        "difficulty_score": 6
    },
    {
        "structure": "S + used to + V-inf",
        "explanation": "Thói quen trong quá khứ: Diễn tả thói quen hoặc trạng thái đã từng xảy ra nhưng nay không còn nữa.",
        "example": "He used to live in Tokyo before moving to California.",
        "cefr_level": "B1",
        "category": "Habits & States",
        "difficulty_score": 5
    },

    # Band B2 - Trung Cao Cấp (Điểm 7 - 8)
    {
        "structure": "If + S + V(past), S + would + V-inf",
        "explanation": "Câu điều kiện loại 2: Giả định một tình huống không có thật hoặc trái ngược với thực tế ở hiện tại.",
        "example": "If I had a million dollars, I would travel around the world.",
        "cefr_level": "B2",
        "category": "Conditionals",
        "difficulty_score": 7
    },
    {
        "structure": "S + had + V3/ed (Past Perfect)",
        "explanation": "Thì Quá khứ hoàn thành: Diễn tả một hành động xảy ra và hoàn tất trước một thời điểm hoặc hành động khác trong quá khứ.",
        "example": "By the time the police arrived, the burglar had already fled.",
        "cefr_level": "B2",
        "category": "Tenses",
        "difficulty_score": 7
    },
    {
        "structure": "S + wish + S + V(past)",
        "explanation": "Câu điều ước loại 2: Thể hiện mong ước về một điều trái ngược với thực tế ở hiện tại.",
        "example": "I wish I were capable of speaking fluent German.",
        "cefr_level": "B2",
        "category": "Wishes",
        "difficulty_score": 7
    },
    {
        "structure": "Reported Speech: S + said that + S + V(backshift)",
        "explanation": "Câu tường thuật gián tiếp: Tường thuật lại lời nói của người khác với quy tắc lùi thì.",
        "example": "The manager stated that the project would be finalized on time.",
        "cefr_level": "B2",
        "category": "Reported Speech",
        "difficulty_score": 7
    },
    {
        "structure": "It is high time + S + V(past)",
        "explanation": "Cấu trúc nhấn mạnh: Đã đến lúc ai đó khẩn thiết phải hành động.",
        "example": "It is high time we re-evaluated our environmental policies.",
        "cefr_level": "B2",
        "category": "Emphatic Structures",
        "difficulty_score": 8
    },

    # Band C1 - Cao Cấp (Điểm 9)
    {
        "structure": "Not only + Auxiliary + S + V, but also...",
        "explanation": "Đảo ngữ nâng cao: Nhấn mạnh hai đặc tính/sự kiện liên tiếp (Không những... mà còn...).",
        "example": "Not only did she master the curriculum, but she also mentored her peers.",
        "cefr_level": "C1",
        "category": "Inversion",
        "difficulty_score": 9
    },
    {
        "structure": "Had + S + V3, S + would have + V3",
        "explanation": "Đảo ngữ Điều kiện loại 3: Giả định trang trọng về một biến cố trong quá khứ (văn phong học thuật/IELTS 7.5+).",
        "example": "Had the authorities recognized the warning signs, catastrophic failure would have been averted.",
        "cefr_level": "C1",
        "category": "Inversion",
        "difficulty_score": 9
    },
    {
        "structure": "It + is/was + [Focus] + that/who + ...",
        "explanation": "Câu chẻ (Cleft Sentence): Đưa trọng tâm cần nhấn mạnh lên trước mệnh đề liên kết.",
        "example": "It was empirical observation that invalidated the conventional paradigm.",
        "cefr_level": "C1",
        "category": "Cleft Sentences",
        "difficulty_score": 9
    },
    {
        "structure": "Rarely / Seldom / Scarcely + Auxiliary + S + V",
        "explanation": "Đảo ngữ phủ định bán phần: Nhấn mạnh mức độ hiếm hoi mang sắc thái văn chương.",
        "example": "Rarely has human civilization encountered such rapid technological disruption.",
        "cefr_level": "C1",
        "category": "Inversion",
        "difficulty_score": 9
    },

    # Band C2 - Độc Cô Cầu Bại (Điểm 10)
    {
        "structure": "No sooner + had + S + V3 + than + S + V2",
        "explanation": "Đảo ngữ thời gian kép: Diễn tả hai hành động nối tiếp nhau gần như ngay tức khắc trong quá khứ.",
        "example": "No sooner had the symposium concluded than unprecedented collaborations materialized.",
        "cefr_level": "C2",
        "category": "Inversion",
        "difficulty_score": 10
    },
    {
        "structure": "Having + V3/ed, S + V + O",
        "explanation": "Rút gọn mệnh đề phân từ hoàn thành (Perfect Participle): Thể hiện chuỗi hành động nguyên nhân - kết quả tinh tế.",
        "example": "Having assimilated diverse philosophical traditions, the scholar articulated a unified theory.",
        "cefr_level": "C2",
        "category": "Participle Clauses",
        "difficulty_score": 10
    },
    {
        "structure": "It is essential / imperative that + S + (should) + V-inf",
        "explanation": "Thể giả định thức (Subjunctive Mood): Diễn đạt tính cấp thiết, tính bắt buộc trong văn bản pháp quy và hàn lâm.",
        "example": "It is imperative that every participant adhere strictly to safety protocols.",
        "cefr_level": "C2",
        "category": "Subjunctive",
        "difficulty_score": 10
    }
]


def run_migration():
    with app.app_context():
        print("=== BẮT ĐẦU MIGRATION & ENRICHMENT NGỮ PHÁP CEFR VÀ USER_GRAMMARS ===")

        # 1. Thêm cột mới vào bảng grammars
        with db.engine.connect() as conn:
            columns_to_add = [
                ("cefr_level", "VARCHAR(10) DEFAULT 'A1'"),
                ("category", "VARCHAR(50) DEFAULT 'General'"),
                ("difficulty_score", "INT DEFAULT 1")
            ]
            for col, defn in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE grammars ADD COLUMN {col} {defn}"))
                    conn.commit()
                    print(f"[+] Đã thêm cột '{col}' vào bảng grammars.")
                except Exception as e:
                    print(f"[*] Cột '{col}' đã tồn tại: {e}")

        # 2. Tạo bảng user_grammars nếu chưa có
        db.create_all()
        print("[+] db.create_all() hoàn tất (user_grammars đã sẵn sàng).")

        # 3. Cập nhật và bổ sung đầy đủ bộ ngữ pháp theo chuẩn CEFR A1 - C2
        updated_count = 0
        added_count = 0
        for g_def in CEFR_GRAMMAR_DEFINITIONS:
            # Tìm kiếm theo cấu trúc tương đồng hoặc từ khóa
            g = Grammar.query.filter(Grammar.structure.ilike(f"%{g_def['structure'][:15]}%")).first()
            if not g:
                g = Grammar.query.filter_by(structure=g_def["structure"]).first()

            if g:
                g.structure = g_def["structure"]
                g.explanation = g_def["explanation"]
                g.example = g_def["example"]
                g.cefr_level = g_def["cefr_level"]
                g.category = g_def["category"]
                g.difficulty_score = g_def["difficulty_score"]
                updated_count += 1
            else:
                g = Grammar(
                    structure=g_def["structure"],
                    explanation=g_def["explanation"],
                    example=g_def["example"],
                    is_slang=False,
                    cefr_level=g_def["cefr_level"],
                    category=g_def["category"],
                    difficulty_score=g_def["difficulty_score"]
                )
                db.session.add(g)
                added_count += 1

        # Cập nhật các bản ghi còn lại nếu chưa có cefr_level
        all_grammars = Grammar.query.all()
        for g in all_grammars:
            if not g.cefr_level:
                s_lower = g.structure.lower()
                if "no sooner" in s_lower or "having" in s_lower or "imperative" in s_lower:
                    g.cefr_level = 'C2'
                    g.difficulty_score = 10
                elif "not only" in s_lower or "had +" in s_lower or "cleft" in s_lower or "rarely" in s_lower:
                    g.cefr_level = 'C1'
                    g.difficulty_score = 9
                elif "wish" in s_lower or "type 2" in s_lower or "reported" in s_lower or "past perfect" in s_lower:
                    g.cefr_level = 'B2'
                    g.difficulty_score = 7
                elif "have/has" in s_lower or "type 1" in s_lower or "passive" in s_lower or "relative" in s_lower:
                    g.cefr_level = 'B1'
                    g.difficulty_score = 5
                elif "v(ed)" in s_lower or "going to" in s_lower or "was/were" in s_lower or "comparative" in s_lower:
                    g.cefr_level = 'A2'
                    g.difficulty_score = 3
                else:
                    g.cefr_level = 'A1'
                    g.difficulty_score = 1

        db.session.commit()
        print(f"[+] Hoàn tất! Bổ sung mới: {added_count}, Cập nhật: {updated_count}. Tổng số Grammar hiện có: {len(all_grammars)}.")
        
        # Thống kê số lượng Grammar theo CEFR
        for band in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            c = Grammar.query.filter_by(cefr_level=band).count()
            print(f"  - Band {band}: {c} cấu trúc ngữ pháp chuẩn.")


if __name__ == '__main__':
    run_migration()
