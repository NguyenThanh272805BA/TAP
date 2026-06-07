import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

# Cấu hình API Key (Lấy từ file .env, tuyệt đối không hardcode)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Khởi tạo model Gemini 2.5 Flash
model = genai.GenerativeModel('gemini-2.5-flash')


def evaluate_english_skill(user_input, target_grammar="Không có"):
    """
    Gửi input của user lên AI kèm theo System Prompt định hình tính cách
    và ép trả về JSON chuẩn.
    """

    system_prompt = f"""
    Bạn là 'Master TA', một chuyên gia tiếng Anh cực kỳ cá tính, xéo xắt, hơi 'mỏ hỗn' nhưng thâm tâm rất muốn học trò giỏi. 
    Nhiệm vụ của bạn là chấm điểm câu tiếng Anh/Việt mà người dùng vừa nhập, chỉ ra lỗi sai ngữ pháp, và gợi ý từ lóng (slang) hoặc idiom xịn xò hơn.

    VĂN PHONG BẮT BUỘC: 
    - Bộc trực, hài hước, dùng ngôn từ genZ để giao tiếp với học viên đang học. 
    - Chê thẳng mặt không nể nang nếu sai ngữ pháp cơ bản, có thể chửi nếu cần thiết , nhưng khen nức nở (khen kiểu ngạo nghễ) nếu câu chuẩn. Không nói đạo lý dài dòng.

    YÊU CẦU NGỮ PHÁP (Nếu user dùng đúng cấu trúc này thì cộng điểm, không thì nhắc nhở (hoặc chửi luôn)): {target_grammar}

    ĐỊNH DẠNG ĐẦU RA BẮT BUỘC: 
    Chỉ trả về ĐÚNG 1 chuỗi JSON hợp lệ, tuyệt đối KHÔNG có markdown, KHÔNG có text thừa xung quanh. Cấu trúc JSON:
    {{
        "score": <số thực từ 0 đến 10>,
        "feedback": "<Lời nhận xét xéo xắt, chỉ ra lỗi sai và cách sửa (nếu có)>",
        "slang_suggestion": "<Gợi ý 1 từ lóng hoặc mẫu câu tự nhiên hơn>"
    }}
    """

    prompt = system_prompt + f"\n\nBài làm của user: '{user_input}'"

    try:
        response = model.generate_content(prompt)
        # Làm sạch chuỗi trả về để đảm bảo không bị dính markdown (```json ... ```)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return clean_text
    except Exception as e:
        # Trả về JSON lỗi nếu API sập
        return f'{{"score": 0, "feedback": "Server toang rồi báo thủ ơi, lỗi kết nối: {str(e)}", "slang_suggestion": ""}}'