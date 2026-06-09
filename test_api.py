from app import create_app, db
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar

app = create_app()


def seed_massive_database():
    with app.app_context():
        print("=== BẮT ĐẦU BƠM KHO DỮ LIỆU TĨNH VÀO GLOBAL FLUENT ===")

        # 1. KHO TỪ VỰNG KHỔNG LỒ (Chia theo Theme)
        vocab_dataset = [
            # --- THEME: ACTION & RPG GAMING ---
            {"word": "Pity", "meaning": "Cơ chế bảo hiểm (chắc chắn ra nhân vật hiếm sau x lần quay).", "theme": "Gacha Systems"},
            {"word": "Banner", "meaning": "Sự kiện quay thưởng giới hạn thời gian cho một nhân vật.", "theme": "Gacha Systems"},
            {"word": "Primogem", "meaning": "Đơn vị tiền tệ quý hiếm dùng để quay gacha.", "theme": "Gacha Systems"},
            {"word": "Stellar Jade", "meaning": "Ngọc ánh sao, một dạng tiền tệ cao cấp đổi vé quay.", "theme": "Gacha Systems"},
            {"word": "Whale", "meaning": "Người chơi nạp số tiền khổng lồ vào game.", "theme": "Gacha Systems"},
            {"word": "Reroll", "meaning": "Tạo lại tài khoản liên tục để lấy nhân vật xịn ở lượt quay đầu.", "theme": "Gacha Systems"},
            {"word": "Grind", "meaning": "Cày cuốc lặp đi lặp lại một phó bản để lấy tài nguyên.", "theme": "Action RPG"},
            {"word": "Ultimate", "meaning": "Chiêu cuối, kỹ năng tối thượng của nhân vật.", "theme": "Action RPG"},
            {"word": "Resonance", "meaning": "Sự cộng hưởng sức mạnh giữa các nguyên tố hoặc đội hình.", "theme": "Action RPG"},
            {"word": "Anomaly", "meaning": "Sự bất thường, trạng thái dị thường gây sát thương lên kẻ địch.", "theme": "Action RPG"},
            {"word": "I-frame", "meaning": "Khung hình bất tử (Invincibility frame) khi thực hiện kỹ năng né tránh.", "theme": "Action RPG"},

            # --- THEME: SOFTWARE & WEB DEVELOPMENT ---
            {"word": "Polymorphism", "meaning": "Tính đa hình (Một khái niệm cốt lõi trong OOP).", "theme": "Java & OOP"},
            {"word": "Encapsulation", "meaning": "Tính đóng gói (Che giấu dữ liệu bên trong class).", "theme": "Java & OOP"},
            {"word": "Inheritance", "meaning": "Tính kế thừa (Class con nhận thuộc tính từ class cha).", "theme": "Java & OOP"},
            {"word": "JDBC", "meaning": "API dùng để kết nối ứng dụng Java với cơ sở dữ liệu.", "theme": "Java & OOP"},
            {"word": "Graphical User Interface (GUI)", "meaning": "Giao diện đồ họa người dùng, thay vì dùng dòng lệnh.", "theme": "Java & OOP"},
            {"word": "Deployment", "meaning": "Quá trình đưa website/app lên server thực tế.", "theme": "Database & Hosting"},
            {"word": "Workspace", "meaning": "Không gian làm việc hoặc môi trường chứa các project đang code.", "theme": "Database & Hosting"},
            {"word": "Query", "meaning": "Câu lệnh truy vấn để lấy dữ liệu từ Database (VD: SELECT).", "theme": "Database & Hosting"},
            {"word": "Schema", "meaning": "Cấu trúc, mô hình tổ chức của một cơ sở dữ liệu.", "theme": "Database & Hosting"},
            {"word": "Domain", "meaning": "Tên miền của website trên Internet.", "theme": "Database & Hosting"},

            # --- THEME: INTERNET SLANG & GEN Z ---
            {"word": "Flex", "meaning": "Khoe khoang một cách tự hào.", "theme": "Internet Slang"},
            {"word": "Red flag", "meaning": "Dấu hiệu cảnh báo nguy hiểm trong một mối quan hệ/công việc.", "theme": "Internet Slang"},
            {"word": "Ghosting", "meaning": "Bơ tin nhắn, biến mất không một lời từ biệt.", "theme": "Internet Slang"},
            {"word": "Salty", "meaning": "Cay cú, tức tối vì một chuyện gì đó.", "theme": "Internet Slang"},
            {"word": "Touch grass", "meaning": "Khuyên ai đó bớt chơi game/lướt mạng lại và ra ngoài hít thở đi.", "theme": "Internet Slang"},
            {"word": "Sus", "meaning": "Đáng ngờ (viết tắt của Suspicious).", "theme": "Internet Slang"},
            {"word": "GOAT", "meaning": "Vĩ đại nhất mọi thời đại (Greatest Of All Time).", "theme": "Internet Slang"},
            {"word": "No cap", "meaning": "Thật đấy, không đùa đâu (Tương đương 'for real').", "theme": "Internet Slang"}
        ]

        # 2. KHO NGỮ PHÁP & CẤU TRÚC (Bổ sung để sửa lỗi NameError)
        grammar_dataset = [
            {
                "structure": "To be worth the grind",
                "explanation": "Đáng công sức cày cuốc, bỏ thời gian làm việc gì đó lặp đi lặp lại.",
                "example": "Getting this legendary weapon is hard, but it's totally worth the grind."
            },
            {
                "structure": "To flex on someone",
                "explanation": "Khoe mẽ, thể hiện cái gì đó vượt trội trước mặt người khác.",
                "example": "He bought a high-tier skin just to flex on his friends."
            },
            {
                "structure": "To deploy [something] to [environment]",
                "explanation": "Triển khai/đưa sản phẩm phần mềm lên một môi trường hệ thống cụ thể.",
                "example": "The dev team is preparing to deploy the new features to production tonight."
            },
            {
                "structure": "To give off a [adjective] vibe",
                "explanation": "Toả ra, tạo cho người khác một cảm giác hoặc năng lượng cụ thể.",
                "example": "This new game update gives off a very nostalgic vibe."
            },
            {
                "structure": "To end up + V-ing",
                "explanation": "Rốt cuộc thì, kết cục là (làm một việc gì đó nằm ngoài kế hoạch ban đầu).",
                "example": "I didn't plan to spend money, but I ended up whaling on the character banner."
            }
        ]

        # Đẩy từ vựng vào DB (Kiểm tra tránh trùng lặp)
        vocab_added = 0
        for item in vocab_dataset:
            if not Vocabulary.query.filter_by(word=item['word']).first():
                new_v = Vocabulary(
                    word=item['word'],
                    meaning=item['meaning'],
                    theme=item['theme'],
                    image_url="default.png",
                    is_unlocked=True  # Mở khóa sẵn một nửa để test
                )
                db.session.add(new_v)
                vocab_added += 1

        # Đẩy ngữ pháp vào DB (Giờ đã có dữ liệu để chạy ổn định)
        grammar_added = 0
        for item in grammar_dataset:
            if not Grammar.query.filter_by(structure=item['structure']).first():
                new_g = Grammar(
                    structure=item['structure'],
                    explanation=item['explanation'],
                    example=item['example'],
                    is_slang=False
                )
                db.session.add(new_g)
                grammar_added += 1

        db.session.commit()
        print(f"[+] Báo cáo: Đã tiêm {vocab_added} từ vựng và {grammar_added} cấu trúc ngữ pháp vào lõi.")
        print("=== HOÀN TẤT CHIẾN DỊCH ===")


if __name__ == "__main__":
    seed_massive_database()