import speech_recognition as sr
from pydub import AudioSegment
import os


def convert_audio_to_text(audio_file_path):
    """
    Nhận vào đường dẫn file ghi âm (.webm, .wav, .mp3 từ frontend),
    Chuyển đổi về chuẩn định dạng WAV và trả về văn bản text tiếng Anh.
    """
    recognizer = sr.Recognizer()

    # Định dạng ghi âm từ trình duyệt thường là .webm hoặc .ogg, cần convert về .wav để thư viện đọc được
    base, ext = os.path.splitext(audio_file_path)
    wav_path = base + "_converted.wav"

    try:
        # Convert file âm thanh bằng pydub
        sound = AudioSegment.from_file(audio_file_path)
        sound.export(wav_path, format="wav")

        # Tiến hành nhận diện giọng nói tiếng Anh
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # Dùng Google Speech Recognition API (Miễn phí, không cần key)
            text = recognizer.recognize_google(audio_data, language="en-US")

        # Dọn dẹp file tạm sau khi xử lý xong
        if os.path.exists(wav_path):
            os.remove(wav_path)

        return text
    except sr.UnknownValueError:
        return "Không thể nhận diện được giọng nói, hãy thử nói rõ ràng hơn!"
    except sr.RequestError as e:
        return f"Lỗi hệ thống nhận diện giọng nói: {str(e)}"
    except Exception as e:
        return f"Lỗi xử lý file âm thanh: {str(e)}"