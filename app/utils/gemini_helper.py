# app/utils/gemini_helper.py
import os
import sys
import json
import time
import re
from google import genai
from google.genai import errors, types
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load biến môi trường
load_dotenv()


# ==============================================================
# HỆ THỐNG QUẢN LÝ KHÓA ĐA LUỒNG (API KEY ROTATION MANAGER)
# ==============================================================
class GeminiKeyManager:
    def __init__(self):
        self.clients = []
        self.current_index = 0

        # Tự động quét file .env để thu thập toàn bộ các key có tiền tố GEMINI_API_KEY_
        for key_name, key_value in os.environ.items():
            if key_name.startswith("GEMINI_API_KEY") and key_value:
                try:
                    client = genai.Client(api_key=key_value)
                    self.clients.append(client)
                except Exception as e:
                    print(f"[WARNING] Bỏ qua key lỗi {key_name}: {e}")

        # Fallback nếu cấu hình sai, lấy key mặc định cũ
        if not self.clients:
            fallback_key = os.getenv("GEMINI_API_KEY")
            if fallback_key:
                self.clients.append(genai.Client(api_key=fallback_key))
            else:
                print("[FATAL ERROR] KHÔNG TÌM THẤY BẤT KỲ API KEY NÀO TRONG .ENV!")

        self.total_keys = len(self.clients)
        print(f"[SYSTEM] Khởi tạo thành công Mạng lưới AI với {self.total_keys} lõi dự phòng.")

    def get_current_client(self):
        if self.total_keys == 0:
            raise Exception("Hệ thống thiếu nhiên liệu (API Key)!")
        return self.clients[self.current_index]

    def switch_key(self):
        """Kích hoạt cơ chế trượt key khi cạn Quota"""
        if self.total_keys > 1:
            old_index = self.current_index
            self.current_index = (self.current_index + 1) % self.total_keys
            print(
                f"[KEY MANAGER] Lõi {old_index + 1} quá tải/hết Quota. Chuyển mạch sang Lõi {self.current_index + 1}...")
        else:
            print("[KEY MANAGER] Cảnh báo: Hệ thống chỉ có 1 lõi duy nhất. Không thể chuyển mạch!")


# Khởi tạo Singleton Manager
key_manager = GeminiKeyManager()


def call_gemini_with_retry(prompt, system_instruction=None, model='gemini-2.5-flash', enforce_json=False):
    """
    Hàm gọi AI tích hợp thuật toán luân chuyển Key (Đồng bộ).
    Hỗ trợ System Instruction để chống Prompt Injection và Regex bóc tách JSON chống Hallucination.
    """
    max_retries = key_manager.total_keys + 1
    attempt = 0

    while attempt < max_retries:
        client = key_manager.get_current_client()
        try:
            # Thiết lập cấu hình chuyên biệt
            config_params = {}
            if enforce_json:
                config_params['response_mime_type'] = 'application/json'
            if system_instruction:
                config_params['system_instruction'] = system_instruction

            # Gọi API theo chuẩn SDK google-genai
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params) if config_params else None
            )

            raw_text = response.text.strip()

            # [ KHIÊN BẢO VỆ JSON ]: Trích xuất khối JSON cuối cùng, loại bỏ toàn bộ text rác (Hallucination)
            if enforce_json or raw_text.startswith('```json') or '{' in raw_text:
                json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', raw_text)
                if json_match:
                    return json_match.group(0)

            return raw_text.replace('```json', '').replace('```', '').strip()

        except errors.APIError as e:
            if e.code == 429:
                key_manager.switch_key()
                attempt += 1
                time.sleep(0.5)
                continue
            else:
                print(f"[API ERROR] Lỗi hệ thống Google: {e}")
                attempt += 1
                time.sleep(2)

        except Exception as e:
            print(f"[NETWORK ERROR] Lỗi kết nối: {e}")
            attempt += 1
            time.sleep(2)

    raise Exception("Mạng lưới AI sụp đổ hoàn toàn do cạn kiệt tài nguyên!")


def stream_gemini_response(prompt, system_instruction=None, model='gemini-2.5-flash'):
    """
    [ PHASE 2 ]: Generator Streaming trả về từng Chunk dữ liệu thời gian thực (hỗ trợ Key Rotation).
    """
    max_retries = key_manager.total_keys + 1
    attempt = 0

    while attempt < max_retries:
        client = key_manager.get_current_client()
        try:
            config_params = {}
            if system_instruction:
                config_params['system_instruction'] = system_instruction

            response_stream = client.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params) if config_params else None
            )

            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            return

        except errors.APIError as e:
            if e.code == 429:
                key_manager.switch_key()
                attempt += 1
                time.sleep(0.5)
                continue
            else:
                yield f"\n[LỖI MẠNG LƯỚI AI]: {e}"
                return
        except Exception as e:
            yield f"\n[LỖI KẾT NỐI]: {e}"
            return

    yield "\n[SERVER QUÁ TẢI] Cạn kiệt toàn bộ tài nguyên Lõi AI!"


def summarize_context(old_history: str) -> str:
    """
    [ PHASE 2 ]: Tóm tắt bối cảnh cũ để giải phóng Token Context Window (Summary Buffer Memory).
    """
    if not old_history.strip():
        return ""
    prompt = f"Hãy tóm tắt bối cảnh cốt truyện sau đây trong 2-3 câu ngắn gọn nhất để làm nền tảng:\n\n{old_history}"
    system_prompt = "Bạn là trợ lý tóm tắt cốt truyện game Text-RPG gọn gàng, sắc bén."
    try:
        return call_gemini_with_retry(prompt, system_instruction=system_prompt)
    except Exception as e:
        print(f"[SUMMARIZE ERROR] {e}")
        return "Bối cảnh trước đó bị nhiễu do bão từ không gian..."


def evaluate_english_skill(user_input, target_grammar="Không có"):
    """
    Hàm dự phòng đánh giá kỹ năng ngôn ngữ.
    """
    system_prompt = f"""Bạn là 'Master TA', một chuyên gia tiếng Anh cực kỳ cá tính, xéo xắt, hơi 'mỏ hỗn' nhưng thâm tâm rất muốn học trò giỏi. 
    Nhiệm vụ của bạn là chấm điểm câu tiếng Anh/Việt mà người dùng vừa nhập, chỉ ra lỗi sai ngữ pháp, và gợi ý từ lóng (slang) hoặc idiom xịn xò hơn.

    VĂN PHONG BẮT BUỘC: 
    - Bộc trực, hài hước, dùng ngôn từ genZ để giao tiếp với học viên đang học. 
    - Chê thẳng mặt không nể nang nếu sai ngữ pháp cơ bản, có thể chửi nếu cần thiết, nhưng khen nức nở (khen kiểu ngạo nghễ) nếu câu chuẩn. Không nói đạo lý dài dòng.

    YÊU CẦU NGỮ PHÁP (Nếu user dùng đúng cấu trúc này thì cộng điểm, không thì nhắc nhở): {target_grammar}

    ĐỊNH DẠNG ĐẦU RA BẮT BUỘC: 
    Chỉ trả về ĐÚNG 1 chuỗi JSON hợp lệ. Cấu trúc JSON:
    {{
        "score": <số thực từ 0 đến 10>,
        "feedback": "<Lời nhận xét xéo xắt, chỉ ra lỗi sai và cách sửa (nếu có)>",
        "slang_suggestion": "<Gợi ý 1 từ lóng hoặc mẫu câu tự nhiên hơn>"
    }}
    """

    prompt = f"Bài làm của user: '{user_input}'"

    try:
        clean_text = call_gemini_with_retry(prompt, system_instruction=system_prompt, enforce_json=True)
        return clean_text
    except Exception as e:
        fallback_json = {
            "score": 5.0,
            "feedback": f"[ SERVER QUÁ TẢI ] Lò phản ứng AI đã cạn sạch năng lượng. Master G buộc phải đi tản nhiệt. Bạn tạm được 5 điểm an ủi!",
            "slang_suggestion": "Out of juice (Cạn kiệt sinh lực)"
        }
        return json.dumps(fallback_json)