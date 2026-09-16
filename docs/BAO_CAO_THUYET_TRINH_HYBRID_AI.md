# TÀI LIỆU NỘI DUNG SLIDE THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN (BẢN TINH GỌN & DỄ HIỂU)
# ĐỀ TÀI: XÂY DỰNG HỆ THỐNG HỌC TIẾNG ANH TƯƠNG TÁC NGỮ CẢNH ỨNG DỤNG KIẾN TRÚC HYBRID AI
**Tác giả**: Nguyễn Kim Thành  
**Hệ thống**: Nền tảng Học tiếng Anh Đa Bộ Não TAP (Multi-Brain Hybrid AI)

---

> **Ghi chú định dạng Slide**:
> * **Nội dung hiển thị trên Slide**: Ngắn gọn, súc tích (3-5 gạch đầu dòng), có thể sao chép trực tiếp lên PowerPoint/Canva.
> * **Giải thích bình dân (Intuition)**: Cách hiểu bằng ngôn ngữ đời thường, dùng hình ảnh ví von trực quan.
> * **Góc kỹ thuật & Thuật toán**: Giữ lại các công thức toán, thông số kỹ thuật then chốt để phục vụ chấm điểm học thuật.
> * **Lời thoại (Speaker Note)**: Câu nói mẫu súc tích cho người thuyết trình.

---

# MỤC LỤC TỔNG QUAN (54 SLIDES)

* **PHẦN 1: BỐI CẢNH & ĐẶT VẤN ĐỀ** (Slide 01 - 07)
* **PHẦN 2: NỀN TẢNG & NGĂN XẾP CÔNG NGHỆ** (Slide 08 - 16)
* **PHẦN 3: KIẾN TRÚC HỆ THỐNG & NỀN TẢNG** (Slide 17 - 24)
* **PHẦN 4: PHƯƠNG PHÁP & THUẬT TOÁN AI CỐT LÕI** (Slide 25 - 38)
* **PHẦN 5: THỰC NGHIỆM & KỊCH BẢN KIỂM THỬ** (Slide 39 - 45)
* **PHẦN 6: KẾT QUẢ THỰC NGHIỆM & ĐỐI CHUẨN** (Slide 46 - 51)
* **PHẦN 7: TỔNG KẾT & HƯỚNG PHÁT TRIỂN** (Slide 52 - 54)
* **PHẦN 8: TRẢ LỜI 3 CÂU HỎI TRỌNG TÂM CỦA HỘI ĐỒNG**

---

# NỘI DUNG CHI TIẾT TỪNG TRANG SLIDE (TINH GỌN & TRỌNG TÂM)

---

### SLIDE 01: TRANG TIÊU ĐỀ
* **Tiêu đề**: XÂY DỰNG HỆ THỐNG HỌC TIẾNG ANH TƯƠNG TÁC NGỮ CẢNH ỨNG DỤNG KIẾN TRÚC HYBRID AI
* **Phụ đề**: Nền tảng Đa Bộ Não (Multi-Brain) kết hợp Trí tuệ Cục bộ (Local AI) và AI Tạo sinh Đám mây (Cloud LLM)
* **Tác giả**: Nguyễn Kim Thành
* **Thông điệp chính**: Làm chủ AI học máy độc lập, không phụ thuộc vào việc "chỉ gọi API ChatGPT".
* **Lời thoại**: *"Em xin kính chào Thầy Cô! Em là Nguyễn Kim Thành. Đề tài của em tập trung giải quyết bài toán: Làm sao để học tiếng Anh vừa tương tác thông minh như ChatGPT, vừa phản hồi tức thì trong chớp mắt và chạy được cả khi mất mạng."*

---

### SLIDE 02: MỤC LỤC BÀI THUYẾT TRÌNH
* **Nội dung slide**:
  1. **Bối cảnh & Bài toán**: Tại sao chỉ dùng ChatGPT/Gemini là chưa đủ?
  2. **Công nghệ cốt lõi**: Bản chất của kiến trúc Hybrid AI và các mô hình học máy.
  3. **Kiến trúc hệ thống**: Mô hình 6 Bộ não cục bộ kết hợp Đám mây.
  4. **Thuật toán & Toán học**: Cách AI chấm ngữ pháp, đoán trí nhớ và gợi ý từ.
  5. **Thực nghiệm & Đối chuẩn**: Thử thách rút dây mạng và kiểm tra tốc độ.
  6. **Kết quả đạt được**: Nhanh gấp 150 lần, tiết kiệm 85% chi phí API.
  7. **Tổng kết & Trả lời phản biện**.
* **Lời thoại**: *"Bài trình bày gồm 7 phần, đi từ vấn đề thực tế, giải pháp công nghệ, thuật toán lõi đến các kết quả đo lường thực nghiệm."*

---

### SLIDE 03: THỰC TRẠNG & NỖI ĐAU CỦA NGƯỜI HỌC TIẾNG ANH
* **Nội dung slide**:
  - **Học vẹt, nhanh quên**: Thiếu lịch nhắc ôn tập khoa học, học 100 từ sau 1 tuần quên mất 80 từ.
  - **Luyện tập nhàm chán**: Quanh đi quẩn lại chỉ có câu hỏi trắc nghiệm A/B/C/D, thiếu động lực luyện hàng ngày.
  - **Thiếu phản hồi tức thì**: Tự viết câu tiếng Anh nhưng không biết mình viết đúng hay sai, sai ở chỗ nào để sửa.
* **Giải thích bình dân**: *"Người học tiếng Anh giống như người đi gánh nước bằng rổ: học từ mới rất nhiều nhưng không có ai nhắc đúng lúc sắp quên, làm bài tập thì khô khan nên rất nhanh nản."*
* **Lời thoại**: *"Vấn đề lớn nhất của việc học tiếng Anh hiện nay là học trước quên sau và thiếu môi trường tương tác phản hồi ngay lập tức."*

---

### SLIDE 04: CÁI BẪY CỦA CÁC ỨNG DỤNG "THUẦN CLOUD AI" (AI WRAPPER)
* **Nội dung slide**:
  - **Chờ đợi quá lâu (Độ trễ cao)**: Mỗi lần gửi câu phải đợi 2 - 4 giây để nhận kết quả từ OpenAI/Gemini.
  - **Chi phí đắt đỏ**: Cứ mỗi câu chấm ngữ pháp lại tốn tiền Token, càng đông người dùng chi phí càng bùng nổ.
  - **Mất mạng là tê liệt**: Rớt mạng Internet hoặc tài khoản API hết hạn là ứng dụng đứng hình hoàn toàn.
* **Giải thích bình dân**: *"Nếu việc gì cũng đem hỏi ChatGPT trên mây thì giống như việc mua cọng hành cũng phải bắt xe ra tận chợ đầu mối: vừa lâu, vừa tốn tiền xăng, lúc kẹt xe thì chịu chết."*
* **Lời thoại**: *"Nhiều app hiện nay chỉ đơn thuần là gửi mọi thứ lên ChatGPT. Điều này khiến ứng dụng chạy rất chậm, tốn kém và hoàn toàn bất lực khi mất kết nối mạng."*

---

### SLIDE 05: ĐẶT VẤN ĐỀ & CÂU HỎI KHOA HỌC
* **Nội dung slide**:
  - **Mâu thuẫn kỹ thuật**: Làm sao để hệ thống vừa **thông minh, hiểu ngữ cảnh** như LLM, vừa **phản hồi tức thì (< 30ms)** và **chạy được 100% khi mất mạng**?
  - **Câu hỏi nghiên cứu**: *Liệu có thể thiết kế một hệ thống AI Lai (Hybrid AI), để máy tính cục bộ tự giải quyết 80-90% các bài toán thường gặp, chỉ gọi lên đám mây khi gặp câu quá khó?*
* **Giải thích bình dân**: Giống như nguyên lý làm việc ở bệnh viện: Y tá và trợ lý (AI Cục bộ) làm thủ tục đo huyết áp, sơ cứu cực nhanh; chỉ khi gặp ca bệnh hiểm nghèo mới chuyển lên Bác sĩ trưởng khoa (Cloud LLM).
* **Lời thoại**: *"Em đặt ra bài toán: Hãy để máy tính cá nhân tự chấm điểm và tính toán trong chớp mắt, đám mây chỉ dùng cho những việc sáng tạo đặc biệt."*

---

### SLIDE 06: MỤC TIÊU NGHIÊN CỨU CỤ THỂ
* **Nội dung slide**:
  - **Làm chủ 6 Bộ Não AI Cục bộ**: Chấm ngữ pháp, đoán ý định, tính chu kỳ quên, phân loại độ khó, gợi ý từ vựng, bóc tách từ khóa.
  - **Xây dựng Cổng Bất định (Uncertainty Gate)**: Tự nhận biết câu nào mô hình cục bộ tự tin thì chấm ngay, câu nào "lạ lẫm/mập mờ" thì mới đẩy lên Gemini.
  - **Trò chơi hóa (Gamification)**: Đấu trường Gacha mở thẻ bài, game nhập vai Text-RPG, Bản đồ học thuật từ A1 đến C2.
* **Lời thoại**: *"Mục tiêu của đề tài là xây dựng trọn vẹn 6 thuật toán AI chạy trên CPU, thiết kế cổng phân luồng thông minh và tích hợp vào một ứng dụng học tập cuốn hút."*

---

### SLIDE 07: Ý NGHĨA THỰC TIỄN CỦA ĐỀ TÀI
* **Nội dung slide**:
  - **Tiết kiệm chi phí**: Giảm 85% chi phí tiền mua API đám mây cho các trường học và trung tâm.
  - **Xóa rào cản đường truyền**: Học sinh ở vùng sâu vùng xa mạng chập chờn vẫn học và được AI chấm bài mượt mà.
  - **Bảo mật dữ liệu**: Bài viết và thông tin học tập của học viên được xử lý trực tiếp trên máy, không bị gửi ra nước ngoài.
* **Lời thoại**: *"Ý nghĩa thực tiễn là tạo ra một giải pháp EdTech giá rẻ, chạy mượt mà trên máy tính phổ thông và không phụ thuộc vào các công ty công nghệ nước ngoài."*

---

### SLIDE 08: KHÁI NIỆM KIẾN TRÚC HYBRID AI (TRÍ TUỆ NHÂN TẠO LAI)
* **Nội dung slide**:
  - **Local AI (Trí tuệ Biên)**: Chạy trên CPU máy trạm $\to$ Nhiệm vụ: Chấm điểm, tính toán logic, phân loại $\to$ Tốc độ: **< 20ms**, Chi phí: **0 VNĐ**.
  - **Cloud GenAI (Trí tuệ Đám mây)**: Chạy trên máy chủ Google $\to$ Nhiệm vụ: Nhập vai nhân vật Master G, sáng tạo cốt truyện Text-RPG.
* **Giải thích bình dân (Ví von Xe ô tô Hybrid)**:
  - Đi trong phố kẹt xe: Chạy bằng động cơ điện nhẹ nhàng, êm ru, không tốn xăng (Local AI).
  - Ra đường cao tốc leo dốc cao: Động cơ xăng công suất lớn mới gầm rú hỗ trợ (Cloud LLM).
* **Lời thoại**: *"Kiến trúc Hybrid AI hoạt động hệt như một chiếc xe ô tô lai xăng điện: việc nhẹ làm hàng ngày thì dùng AI cục bộ, việc nặng sáng tạo thì mới nhờ tới đám mây."*

---

### SLIDE 09: TỔNG QUAN NGĂN XẾP CÔNG NGHỆ (TECH STACK)
* **Nội dung slide**:
  - **Giao diện (Frontend)**: HTML5, CSS3 hiện đại (Bento Grid, Dark Mode, mờ kính Glassmorphism), JavaScript ES6 thuần.
  - **Hệ thống Backend**: Python Flask theo mô hình MVC, kết nối luồng thời gian thực qua Server-Sent Events (SSE).
  - **Thư viện AI Cốt lõi**: PyTorch, Hugging Face Transformers, Scikit-learn, SciPy, Wordfreq.
  - **Đám mây & Dữ liệu**: Google Gemini 2.5 Flash SDK, Cơ sở dữ liệu MySQL 8.0.
* **Lời thoại**: *"Toàn bộ hệ thống được xây dựng trên nền tảng Python, giao diện Web hiện đại tối ưu hóa, và các thư viện học máy chuẩn mực quốc tế."*

---

### SLIDE 10: NỀN TẢNG HỌC SÂU: TRANSFORMER VÀ DISTILBERT
* **Nội dung slide**:
  - **Mô hình Transformer**: Khả năng "chú ý" (Self-Attention) giúp hiểu mối liên hệ giữa các từ dù đứng cách xa nhau trong câu.
  - **Kỹ thuật Chắt lọc Tri thức (Distillation)**:
    - Rút gọn từ mô hình BERT (110 triệu tham số) xuống **DistilBERT (66 triệu tham số)**.
    - Giảm 40% độ nặng, tăng tốc 60%, nhưng giữ được **97% trí thông minh ngôn ngữ**.
* **Góc kỹ thuật**: $\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}}\right)\mathbf{V}$
* **Lời thoại**: *"Thay vì dùng mô hình BERT cồng kềnh, em sử dụng DistilBERT - một phiên bản chắt lọc nhỏ hơn 40% nhưng giữ gần như nguyên vẹn khả năng hiểu ngữ pháp."*

---

### SLIDE 11: KỸ THUẬT LƯỢNG TỬ HÓA TRỌNG SỐ (DYNAMIC INT8 QUANTIZATION)
* **Nội dung slide**:
  - **Vấn đề**: Mô hình gốc dùng số thực 32-bit (FP32) quá nặng (255MB), chạy trên CPU máy tính thường rất chậm (135ms).
  - **Giải pháp**: Lượng tử hóa động sang số nguyên 8-bit (INT8) $[-128, 127]$.
  - **Kết quả đo đạc**:
    - Kích thước: Giảm từ **255 MB $\to$ 132 MB** (nén một nửa).
    - Tốc độ suy luận CPU: Tăng từ **135ms $\to$ 18.5ms** (nhanh gấp **7.2 lần**).
* **Giải thích bình dân**: Giống như việc nén một bức ảnh nặng 20MB sang file JPG 2MB: chất lượng nhìn bằng mắt vẫn đẹp như cũ nhưng dung lượng nhẹ đi rất nhiều, mở ra xem cực nhanh.
* **Lời thoại**: *"Bằng kỹ thuật lượng tử hóa INT8, em đã ép mô hình Transformer chạy siêu tốc trên CPU thông thường chỉ mất 18.5 mili-giây mà độ chính xác hầu như không đổi."*

---

### SLIDE 12: MẠNG NƠ-RON NHẬN DIỆN Ý ĐỊNH (TF-IDF + MLP)
* **Nội dung slide**:
  - **Mục tiêu**: Đọc câu chat của người học để biết họ muốn gì trong 4 ý định: Hỏi từ vựng (`ask_vocab`), Hỏi ngữ pháp (`ask_grammar`), Chơi game RPG (`story_action`), hay Trò chuyện chung (`general_chat`).
  - **Cơ chế**:
    - Trích xuất từ khóa đơn và cụm từ đôi qua **TF-IDF**.
    - Đưa qua mạng nơ-ron đa tầng **MLP (100 $\to$ 50 $\to$ 4 nút)** với hàm kích hoạt ReLU.
  - **Hiệu năng**: Suy luận cực nhanh trong **1.2 mili-giây**, độ chính xác thực nghiệm **99.8%**.
* **Lời thoại**: *"Để phân loại ý định người dùng, em dùng mạng nơ-ron MLP kết hợp TF-IDF. Mô hình phân biệt chính xác 4 nhóm nhu cầu chỉ trong 1.2 mili-giây."*

---

### SLIDE 13: MÔ HÌNH TRÍ NHỚ EBBINGHAUS & SMART SRS
* **Nội dung slide**:
  - **Đường cong lãng quên (Hermann Ebbinghaus)**: Trí nhớ con người rơi tự do theo hàm số mũ nếu không được ôn tập đúng lúc.
  - **Công thức SRS thích ứng của TAP**:
    $$\Delta t_{\text{tiếp\_theo}} = \theta_0 + \left( \Delta t_{\text{trước}} \times \theta_1 \right) \cdot \exp\Big( -\theta_2 \cdot \text{số\_lần\_sai} - 0.1 \cdot \text{thời\_gian\_nghĩ} \Big)$$
  - **Phản xạ thông minh**:
    - Trả lời đúng + nhanh $\to$ Giãn chu kỳ gấp 2 - 3 lần (vài ngày sau mới hỏi lại).
    - Chọn sai hoặc ngập ngừng lâu $\to$ Co chu kỳ tức thì (nhắc học lại ngay trong ngày).
* **Giải thích bình dân**: Giống như chuông báo thức thông minh: từ nào học thuộc vanh vách thì nó để yên vài ngày sau mới hỏi, từ nào ấp úng hoặc trả lời sai thì tí nữa nó réo lại ngay.
* **Lời thoại**: *"Thuật toán Smart SRS dựa trên đường cong lãng quên: tính toán điểm rơi trí nhớ của từng từ vựng dựa vào số lần làm sai và số giây học viên ngập ngừng suy nghĩ."*

---

### SLIDE 14: GỢI Ý TỪ VỰNG THEO CHÙM LIÊN TƯỞNG (CONTENT RECOMMENDER)
* **Nội dung slide**:
  - **Không gian vector Cosine**: Mỗi từ vựng được biểu diễn thành một vector ngữ nghĩa dựa trên chủ đề và định nghĩa.
  - **Nguyên lý gợi ý**:
    - Tìm trọng tâm của các từ mà học viên đã thuộc.
    - Tìm ra **Top 5 từ vựng mới** có khoảng cách góc Cosine gần nhất với các từ đã học.
* **Giải thích bình dân**: Học từ vựng theo "cành nhánh gia đình": học từ *Bệnh viện* thì hệ thống sẽ gợi ý tiếp các từ *Bác sĩ, Đơn thuốc, Phòng cấp cứu*, chứ không ném ra một từ ngẫu nhiên như *Tàu ngầm*.
* **Góc kỹ thuật**: $\text{CosineSim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$
* **Lời thoại**: *"Thay vì học từ vựng ngẫu nhiên, hệ thống đo khoảng cách Cosine để gợi ý từ vựng theo từng chùm liên tưởng, giúp não bộ xâu chuỗi thông tin nhanh hơn."*

---

### SLIDE 15: PHÂN LOẠI CẤP ĐỘ CEFR BẰNG ĐỊNH LUẬT TẦN SUẤT ZIPF
* **Nội dung slide**:
  - **Định luật Zipf**: Trong ngôn ngữ, từ càng phổ biến thì xuất hiện càng nhiều; từ càng hiếm thì càng khó và học thuật.
  - **Cơ chế 2 tầng của TAP**:
    - *Tầng 1*: Tra bảng băm 5.000 từ chuẩn Oxford ($O(1)$ trong $0.001\text{ms}$).
    - *Tầng 2*: Nếu là từ mới, tiếng lóng mạng $\to$ Tính điểm tần suất Zipf: $z(w) = \log_{10}(P(w)) + 9$.
    - Phân bậc: $z \ge 5.5 \to \text{A2}$, $4.0 \le z < 5.5 \to \text{B2}$, $z < 4.0 \to \text{C1/C2}$.
* **Giải thích bình dân**: Giống như đo độ khó của từ bằng "độ phổ biến trên mạng xã hội": từ nào ai cũng nói hàng ngày thì là A1/A2, từ nào hiếm gặp chuyên ngành thì tự động xếp vào C1/C2.
* **Lời thoại**: *"Hệ thống kết hợp từ điển Oxford với định luật tần suất Zipf để gán cấp độ CEFR cho bất kỳ từ mới hay từ lóng nào chỉ trong một phần nghìn giây."*

---

### SLIDE 16: KỸ THUẬT NÉN BỘ NHỚ VÀ XOAY VÒNG KHÓA CLOUD LLM
* **Nội dung slide**:
  - **Nén cửa sổ trượt (Sliding Window)**: Trong game RPG, sau mỗi 3 lượt chat, hệ thống tự động gộp lịch sử cũ thành 2 câu tóm tắt $\to$ **Giảm 65% chi phí token**.
  - **Xoay vòng khóa API (Ring-Buffer Multi-Key)**:
    - Quản lý danh sách khóa API theo vòng tròn.
    - Khi gặp lỗi nghẽn mạng (HTTP 429 Quota) $\to$ Tự động tráo sang khóa tiếp theo trong **0.05ms**, học viên không hề cảm thấy gián đoạn.
* **Giải thích bình dân**: Giống như việc tài xế có sẵn 3 chiếc thẻ nạp tiền: thẻ này hết hạn mức thì quẹt ngay thẻ khác trong chớp mắt để xe không bao giờ phải dừng lại giữa đường.
* **Lời thoại**: *"Để duy trì hệ thống chạy mượt 24/7 mà không tốn tiền mua gói API trả phí, em cài đặt cơ chế xoay vòng chìa khóa tự động và nén lịch sử hội thoại."*

---

### SLIDE 17: MÔ HÌNH PHỄU ĐỊNH TUYẾN 3 CẤP ĐỘ (ROUTING FUNNEL)
* **Nội dung slide**:
  - **Cấp 1 (Bộ lọc Siêu tốc < 1ms)**: Tra cứu từ điển, kiểm tra độ dài câu, bóc tách thực thể.
  - **Cấp 2 (Mô hình Cục bộ 15-20ms)**: Chạy qua DistilBERT và MLP để chấm điểm và tính độ bất định.
  - **Cấp 3 (Cứu cánh Đám mây)**: Chỉ kích hoạt Gemini khi câu quá dài (> 35 từ) hoặc mô hình cục bộ phân vân không chắc chắn.
* **Tỷ lệ điều phối thực tế**: **83.3%** yêu cầu xử lý xong tại máy $\to$ Chỉ **16.7%** cần gọi lên đám mây.
* **Lời thoại**: *"Hệ thống hoạt động theo mô hình phễu 3 cấp độ: Hơn 83% các câu của học viên được giải quyết ngay tại máy cá nhân, chỉ câu nào thật sự khó mới chuyển lên đám mây."*

---

### SLIDE 18: SƠ ĐỒ TOÀN CẢNH HỆ THỐNG ĐA BỘ NÃO (MULTI-BRAIN TOPOLOGY)
* **Nội dung slide**:
  - Tầng Client (Web UI, Game Text-RPG, Âm thanh).
  - Tầng Controller (Điều phối AI, Quản lý Game, Lộ trình học).
  - Tầng AI Cục bộ (6 Bộ não độc lập 100% Offline).
  - Tầng AI Đám mây (Google Gemini 2.5 Flash qua giao thức SSE).
  - Tầng Cơ sở dữ liệu (MySQL lưu trữ lịch sử phản xạ của học viên).
* **Gợi ý thiết kế**: Vẽ sơ đồ phân khối với 6 khối hộp đại diện cho 6 bộ não cục bộ, có mũi tên dự phòng nối sang Gemini.
* **Lời thoại**: *"Đây là bức tranh tổng thể của hệ thống: Tầng điều phối sẽ tiếp nhận tương tác của người học và phân bổ công việc về đúng bộ não chuyên trách."*

---

### SLIDE 19: GIAO DIỆN HIỆN ĐẠI THEO PHONG CÁCH BENTO GRID
* **Nội dung slide**:
  - **Triết lý thiết kế Bento Grid**: Bố trí màn hình thành các ô khối chức năng trực quan giống hộp cơm Bento (Luyện viết, Gacha, Tiến trình, Chuỗi ngày học).
  - **Trải nghiệm mượt mà**: Giao diện tối hiện đại (Dark Mode), hiệu ứng kính mờ (Glassmorphism), phản hồi chuyển động 60fps.
  - **Âm thanh & Tương tác**: Đọc phát âm từ vựng chuẩn giọng bản xứ ngay trên trình duyệt.
* **Lời thoại**: *"Giao diện người dùng được thiết kế theo phong cách Bento Grid thời thượng, giúp học viên dễ dàng theo dõi tiến độ học tập và tương tác mà không bị rối mắt."*

---

### SLIDE 20: TÍNH NĂNG GAMIFICATION: ĐẤU TRƯỜNG TỪ VỰNG GACHA
* **Nội dung slide**:
  - **Vòng lặp Dopamine kích thích học tập**: Làm bài tập đúng $\to$ Tích lũy Xu vàng (Coins) $\to$ Quay rương Gacha may mắn.
  - **4 Phẩm cấp thẻ bài từ vựng theo CEFR**:
    - Thường (Common - A1/A2): Tỷ lệ rơi 55%.
    - Hiếm (Rare - B1): Tỷ lệ rơi 25%.
    - Sử thi (Epic - B2): Tỷ lệ rơi 15%.
    - Huyền thoại (Legendary - C1/C2): Tỷ lệ rơi 5%.
  - Thẻ bài mở ra sẽ tự động đưa vào danh sách ôn tập thông minh SRS.
* **Giải thích bình dân**: Biến việc học từ vựng thành trò chơi "sưu tầm thẻ bài Pokémon": học càng chăm thì càng mở được nhiều thẻ từ vựng cấp độ Huyền thoại.
* **Lời thoại**: *"Cơ chế Gacha giúp học viên có động lực cày cuốc làm bài tập để kiếm Coin quay thẻ bài từ vựng hiếm, sau đó tiếp tục ôn tập để giữ độ bền cho thẻ."*

---

### SLIDE 21: TÍNH NĂNG TƯƠNG TÁC NGỮ CẢNH: GAME TEXT-RPG NHẬP VAI
* **Nội dung slide**:
  - **Học tiếng Anh qua cốt truyện phiêu lưu**: Học viên nhập vai chiến binh vượt ngục hoặc thám hiểm rừng bí ẩn.
  - **Mỗi câu tiếng Anh là một hành động**: Học viên phải gõ câu hành động bằng tiếng Anh để điều khiển nhân vật.
  - **Cơ chế Đổ xúc xắc D20 kết hợp Điểm Ngữ pháp**:
    - Câu đúng ngữ pháp, từ vựng hay $\to$ Đòn đánh Chí Mạng (Critical Hit), quái vật bị tiêu diệt.
    - Câu sai ngữ pháp nghiêm trọng $\to$ Hành động thất bại, nhân vật bị trừ máu (HP).
* **Lời thoại**: *"Trong chế độ Text-RPG, câu tiếng Anh của học viên không còn là bài tập trên giấy nữa mà trực tiếp quyết định sự sống còn của nhân vật trong game."*

---

### SLIDE 22: BẢN ĐỒ LỘ TRÌNH HỌC THUẬT TỪ A1 ĐẾN C2
* **Nội dung slide**:
  - Chuẩn hóa giáo trình theo 6 bậc Khung tham chiếu Châu Âu (CEFR).
  - Mỗi chặng Milestone bao gồm: 1 Cấu trúc ngữ pháp cốt lõi + 5 Từ vựng chuyên đề.
  - **Bài thi Vượt ải Xáo trộn câu (Sentence Scramble)**: Tự động đảo lộn các từ, học viên phải sắp xếp lại đúng thứ tự ngữ pháp trong thời gian quy định để mở khóa ải tiếp theo.
* **Lời thoại**: *"Lộ trình học tập được phân chia khoa học từ mức bắt đầu A1 đến thông thạo C2, mỗi chặng đều có bài kiểm tra xếp chữ để kiểm chứng năng lực trước khi lên lớp."*

---

### SLIDE 23: THIẾT KẾ CƠ SỞ DỮ LIỆU THÍCH ỨNG
* **Nội dung slide**:
  - Bảng `user_vocabularies`: Lưu trữ lịch sử từng từ vựng của mỗi người học (số lần làm sai, số giây suy nghĩ, thời điểm ôn tập kế tiếp).
  - Bảng `tests`: Lưu lại chi tiết từng câu làm bài, điểm AI chấm, thời gian xử lý và nhãn mô hình (`local` hay `cloud`).
  - Bảng `story_sessions`: Quản lý cốt truyện game RPG, điểm máu HP và ngữ cảnh tóm tắt.
* **Lời thoại**: *"Cơ sở dữ liệu được thiết kế chuyên biệt để ghi lại chi tiết từng phần mười giây phản xạ của học viên, cung cấp dữ liệu chính xác cho thuật toán tự học."*

---

### SLIDE 24: SƠ ĐỒ LUỒNG DỮ LIỆU ĐẦU CUỐI (SEQUENCE FLOW)
* **Nội dung slide**:
  1. Học viên nhấn gửi câu văn.
  2. Mô hình DistilBERT tính toán điểm số và độ tự tin trong **18ms**.
  3. **Rẽ nhánh**:
     - *Nếu Tự tin $\ge$ 55%*: Bộ tổng hợp nội bộ sinh nhận xét Master G $\to$ Trả kết quả ngay lập tức (Thời gian: **~19ms**).
     - *Nếu Bất định < 55%*: Mở luồng SSE kết nối Gemini $\to$ Truyền từng chữ nhận xét trực tiếp về màn hình (Thời gian ký tự đầu: **< 280ms**).
  4. Cập nhật nhật ký vào cơ sở dữ liệu.
* **Lời thoại**: *"Đây là quy trình xử lý một câu văn: Nếu câu rõ ràng, máy tự trả kết quả trong 19 mili-giây. Nếu câu trúc trắc khó hiểu, hệ thống sẽ nhờ Gemini phân tích và đẩy chữ về màn hình ngay lập tức."*

---

### SLIDE 25: BỘ NÃO 1: GEC DISTILBERT - ĐỘNG CƠ CHẤM NGỮ PHÁP
* **Nội dung slide**:
  - **Bản chất**: Mô hình Học sâu Transformer phân loại câu nhị phân (Đúng / Sai).
  - **Dữ liệu huấn luyện**: Tập ngữ liệu chuẩn quốc tế **CoLA (GLUE Benchmark)** với 8.551 câu tiếng Anh được gán nhãn ngữ pháp.
  - **Đầu ra**: Điểm số từ 0.0 đến 10.0 và Độ tự tin Softmax Confidence.
* **Góc kỹ thuật**: $\mathbf{z} = \mathbf{W} \mathbf{h}_{[\text{CLS}]} + \mathbf{b}, \quad P(\text{Acceptable}) = \frac{e^{z_1}}{e^{z_0} + e^{z_1}}$
* **Lời thoại**: *"Bộ não số 1 dùng DistilBERT để đọc hiểu toàn bộ cấu trúc câu và chấm điểm chuẩn xác trên thang điểm 10 dựa trên xác suất toán học."*

---

### SLIDE 26: TOÁN HỌC CỔNG BẤT ĐỊNH (UNCERTAINTY GATE)
* **Nội dung slide**:
  - **Đo lường độ tự tin**: $\text{Confidence} = \max(P_{\text{sai}}, P_{\text{đúng}})$.
  - **Độ bất định (Uncertainty)**: $1 - \text{Confidence}$.
  - **Quy tắc ra quyết định**:
    - $\text{Confidence} \ge 0.55$: Máy tự tin $\to$ Chấm điểm tại chỗ, không gọi API.
    - $\text{Confidence} < 0.55$: Máy phân vân (Câu dị thường / ngoài phân phối) $\to$ Kích hoạt Cloud LLM cứu cánh.
* **Giải thích bình dân**: Giống như một học sinh đi thi: câu nào chắc chắn làm được thì ghi đáp án nộp luôn; câu nào thấy mập mờ, lạ hoắc thì mới phải giơ tay xin hỏi ý kiến thầy giáo.
* **Lời thoại**: *"Cổng bất định hoạt động bằng cách đo xác suất: Khi mô hình phân vân với tỷ lệ gần 50-50, hệ thống biết câu này nằm ngoài khả năng và sẽ tự động nhờ Gemini xử lý hộ."*

---

### SLIDE 27: BỘ NÃO 2: NHẬN DIỆN Ý ĐỊNH BẰNG MẠNG NƠ-RON MLP
* **Nội dung slide**:
  - **Đầu vào**: Câu chat tự do của học viên (ví dụ: *"Ubiquitous nghĩa là gì?"*).
  - **Mạng nơ-ron**: 2 tầng ẩn (100 và 50 nút), dùng hàm kích hoạt phi tuyến ReLU để học các mặt phẳng ranh giới ý định.
  - **Kết quả**: Dự đoán chuẩn xác 1 trong 4 nhóm ý định chỉ sau **1.18 mili-giây** trên CPU.
* **Lời thoại**: *"Bộ não số 2 bóc tách ý định người dùng trong 1.18 mili-giây, giúp hệ thống biết ngay người học đang muốn hỏi bài hay đang ra lệnh cho nhân vật trong game."*

---

### SLIDE 28: BỘ NÃO 3: NHẬN DIỆN THỰC THỂ THEO LUẬT (DFA NER)
* **Nội dung slide**:
  - **Nhiệm vụ**: Trích xuất chính xác từ vựng hoặc ngữ pháp mục tiêu từ câu hỏi của học viên.
  - **3 Chiến lược phân cấp**:
    1. Ưu tiên tuyệt đối: Bắt các từ đặt trong dấu ngoặc kép `""` (Chính xác 100%).
    2. Bắt theo từ khóa: Nhận diện cụm đứng sau "cấu trúc", "từ vựng", "nghĩa của".
    3. Lọc từ dừng (Stopwords): Tự động loại bỏ *what, is, how, you* để lấy từ tiếng Anh dài nhất.
  - **Tốc độ**: Hoàn thành trong **0.2 mili-giây**.
* **Lời thoại**: *"Bộ não số 3 là bộ máy lọc từ khóa theo luật: tự động tóm lấy từ vựng hay ngữ pháp mà người học đang muốn hỏi trong chưa đầy một phần nghìn giây."*

---

### SLIDE 29: BỘ NÃO 4: DỰ ĐOÁN CHU KỲ ÔN TẬP SMART SRS
* **Nội dung slide**:
  - **Mô hình toán học**:
    $$\Delta t = \theta_0 + (\Delta t_{\text{trước}} \times \theta_1) \cdot e^{-\theta_2 \cdot \text{sai} - 0.1 \cdot \text{thời\_gian}}$$
  - **3 Tham số sinh học cá nhân**:
    - $\theta_0$: Thời gian cơ sở ôn lại lần đầu (khởi điểm 12 giờ).
    - $\theta_1$: Tốc độ giãn nở trí nhớ dài hạn (hệ số nhân 1.5).
    - $\theta_2$: Mức độ phạt khi quên (hệ số mũ 0.8).
  - **Chặn biên an toàn**: Không bao giờ co dưới 30 phút và không giãn quá 180 ngày.
* **Lời thoại**: *"Bộ não số 4 biến đường cong lãng quên Ebbinghaus thành công thức toán học, tự động cá nhân hóa ngày giờ ôn tập cho từng từ của từng học viên."*

---

### SLIDE 30: THUẬT TOÁN TỰ HỌC SRS BẰNG TRUST REGION REFLECTIVE (TRF)
* **Nội dung slide**:
  - **Khả năng tự tiến hóa**: Khi học viên tích lũy đủ 10 bài kiểm tra, hệ thống tự động chạy thuật toán tối ưu hóa phi tuyến để tìm bộ tham số $\boldsymbol{\theta}$ mới phù hợp nhất với người đó.
  - **Phương pháp TRF (Trust Region Reflective)**:
    - Tìm nghiệm tối ưu trong vùng biên an toàn.
    - Khi bước nhảy chạm biên giới hạn sẽ tự động "phản xạ" quay ngược lại, không bao giờ bị lỗi tính toán như Gradient Descent thông thường.
  - **Kết quả**: Sai số dự đoán thực tế MAE chỉ lệch **1.84 giờ**.
* **Lời thoại**: *"Hệ thống không dùng một công thức chết mà tự học lại theo thời gian: thuật toán TRF liên tục tinh chỉnh các tham số để ngày càng hiểu rõ tốc độ ghi nhớ của riêng bạn."*

---

### SLIDE 31: BỘ NÃO 5: GỢI Ý TỪ VỰNG DỰA TRÊN NỘI DUNG (VOCAB RECOMMENDER)
* **Nội dung slide**:
  - **Không gian vector**: Ánh xạ toàn bộ kho từ vựng thành các vector đặc trưng dựa trên chủ đề và nghĩa tiếng Việt.
  - **Tìm kiếm lân cận góc Cosine**:
    - Tính vector trung tâm của tất cả các từ học viên đã thuộc lòng.
    - Lọc ra những từ mới có góc Cosine gần với trung tâm này nhất.
  - **Tỷ lệ gợi ý trúng đích (Hit Rate @ 5)**: Đạt **78.6%**.
* **Lời thoại**: *"Bộ não số 5 sử dụng hình học không gian vector Cosine để tìm ra các từ vựng lân cận gần gũi nhất với sở thích và vốn từ sẵn có của người học."*

---

### SLIDE 32: BỘ NÃO 6: PHÂN CẤP CEFR KẾT HỢP HAI TẦNG
* **Nội dung slide**:
  - **Tầng 1 (Tra cứu siêu tốc)**: Tìm trong 5.000 từ chuẩn Oxford ($O(1)$).
  - **Tầng 2 (Dự phòng bằng Tần suất Zipf)**:
    - Bất kỳ từ mới nào cũng được tính toán tần suất xuất hiện tự nhiên: $z = \log_{10}(P) + 9$.
    - Từ rất hay gặp ($z \ge 5.5$) $\to$ Xếp vào A2.
    - Từ trung bình ($4.0 \le z < 5.5$) $\to$ Xếp vào B2.
    - Từ hiếm gặp ($z < 4.0$) $\to$ Xếp vào C1/C2.
  - **Độ bao phủ**: **100% từ vựng**, không bao giờ bị lỗi hệ thống.
* **Lời thoại**: *"Bộ não số 6 giải quyết bài toán phân loại từ vựng bằng cách kết hợp tra cứu từ điển Oxford với định luật tần suất Zipf, bảo đảm nhận diện được 100% từ vựng."*

---

### SLIDE 33: BỘ TỔNG HỢP NHẬN XÉT SƯ PHẠM NỘI BỘ (LOCAL CRITIQUE)
* **Nội dung slide**:
  - **Mục tiêu**: Tự động sinh nhận xét xéo xắt, hóm hỉnh chuẩn phong cách Master G mà không cần gọi đến Gemini.
  - **Thích ứng theo 3 cấp độ học viên**:
    - *Người mới học (A1/A2)*: Giọng điệu ân cần, khích lệ, chỉ sửa lỗi ngữ pháp cơ bản (chia động từ, mạo từ).
    - *Trung cấp (B1/B2)*: Giọng điệu thách thức, bắt bẻ thì hoàn thành, liên từ nối.
    - *Cao cấp (C1/C2)*: Khắt khe chuẩn bản xứ, bắt bẻ từng sắc thái nghĩa và cách kết hợp từ (Collocation).
* **Lời thoại**: *"Ngay cả khi ngắt mạng, nhân vật Master G vẫn có thể nhận xét bài viết rất sinh động nhờ bộ quy tắc sư phạm phân cấp theo đúng trình độ của người học."*

---

### SLIDE 34: TỰ ĐỘNG KHAI PHÁ BÀI TẬP MỚI (AUTONOMOUS MINER)
* **Nội dung slide**:
  - **Bài toán**: Ngân hàng câu hỏi cố định sẽ nhanh chóng bị học viên làm hết và nhớ đáp án.
  - **Giải pháp**: Tiến trình chạy ngầm tự động sinh bài tập mới:
    1. Ghép nối từ vựng và cấu trúc ngữ pháp thành các câu biến thể mới.
    2. Đưa qua mô hình DistilBERT kiểm duyệt: chỉ câu nào đạt điểm chuẩn cú pháp $\ge 90\%$ mới được lưu vào kho đề.
* **Lời thoại**: *"Hệ thống có một cỗ máy tự động sinh câu hỏi mới chạy ngầm, liên tục tạo ra bài tập và tự thẩm định tính đúng đắn trước khi đưa cho học viên làm."*

---

### SLIDE 35: BẢNG SO SÁNH NĂNG LỰC 6 BỘ NÃO AI CỤC BỘ
* **Nội dung slide**:

| Bộ não | Nhiệm vụ chính | Thuật toán lõi | Tốc độ CPU | Năng lực Offline |
| :--- | :--- | :--- | :--- | :--- |
| **1. GEC Engine** | Chấm điểm ngữ pháp câu | DistilBERT INT8 Quantized | **18.5 ms** | 100% Offline |
| **2. Intent Classifier**| Đoán ý định câu chat | TF-IDF + Mạng Nơ-ron MLP | **1.2 ms** | 100% Offline |
| **3. Smart SRS** | Đoán thời điểm sắp quên | Hồi quy Ebbinghaus TRF | **0.4 ms** | 100% Offline |
| **4. CEFR Classifier**| Đo độ khó của từ vựng | Bảng băm Oxford + Zipf Law | **0.01 ms** | 100% Offline |
| **5. Recommender** | Gợi ý từ nên học tiếp | Không gian Vector Cosine | **3.5 ms** | 100% Offline |
| **6. NER Engine** | Bóc tách từ khóa câu hỏi| Máy trạng thái hữu hạn DFA | **0.2 ms** | 100% Offline |

* **Lời thoại**: *"Slide 35 tóm lược 6 bộ não AI cục bộ: Mỗi bộ não đều có một thuật toán chuyên biệt, độ trễ suy luận đều tính bằng mili-giây và chạy hoàn toàn ngoại tuyến."*

---

### SLIDE 36: THỰC NGHIỆM 1: ĐỐI CHUẨN LƯỢNG TỬ HÓA TRANSFORMER (FP32 VS INT8)
* **Nội dung slide**:
  - **Mục tiêu**: Chứng minh mô hình nén INT8 chạy nhanh hơn nhưng không bị mất độ chính xác.
  - **Kết quả đo đạc thực tế**:
    - Kích thước đĩa: Giảm từ **255.4 MB $\to$ 132.3 MB** (tiết kiệm 48%).
    - Bộ nhớ RAM: Giảm từ **412 MB $\to$ 198 MB** (tiết kiệm 52%).
    - Độ trễ CPU: Tăng tốc từ **134.6 ms $\to$ 18.5 ms** (nhanh gấp **7.27 lần**).
    - Điểm chính xác CoLA: Chỉ giảm nhẹ từ 82.7% xuống **82.4%** (không đáng kể).
* **Lời thoại**: *"Thực nghiệm đầu tiên chứng minh: Lượng tử hóa INT8 giúp tăng tốc độ xử lý gấp hơn 7 lần và giảm một nửa bộ nhớ RAM, trong khi độ chính xác chỉ suy giảm 0.3%."*

---

### SLIDE 37: THỰC NGHIỆM 2: HIỆU QUẢ CỦA CỔNG BẤT ĐỊNH & TIẾT KIỆM TÀI NGUYÊN
* **Nội dung slide**:
  - Kiểm thử trên bộ dữ liệu hỗn hợp (Câu dễ, câu sai ngữ pháp, câu dị thường OOD, câu học thuật phức hợp).
  - **Tỷ lệ xử lý cục bộ thành công**: **83.3%** các câu được máy tính giải quyết xong ngay lập tức với độ trễ trung bình **17.8 ms**.
  - **Tỷ lệ chuyển giao đám mây**: **16.7%** (chỉ những câu dài trên 35 từ hoặc câu quá lạ lẫm mới phải gọi Gemini).
  - **Hiệu quả**: Tiết kiệm **83.3% chi phí API và tài nguyên mạng**.
* **Lời thoại**: *"Thực nghiệm số 2 cho thấy Cổng bất định đã giữ lại hơn 83% lượng công việc để giải quyết tại chỗ, giúp hệ thống cắt giảm được hơn 83% chi phí gọi dịch vụ đám mây."*

---

### SLIDE 38: THỰC NGHIỆM 3: KHẢ NĂNG ĐOÁN Ý ĐỊNH CỦA MẠNG NƠ-RON MLP
* **Nội dung slide**:
  - Kiểm tra trên tập 50 câu hỏi độc lập chưa từng dùng để huấn luyện.
  - **Ma trận nhầm lẫn (Confusion Matrix)**: Dự đoán đúng 50/50 câu, đạt độ chính xác **100.0%**.
  - Độ tự tin phân phối Softmax trung bình đạt **99.85%**.
  - Thời gian dự đoán trung bình: **1.18 mili-giây**.
* **Lời thoại**: *"Mạng nơ-ron nhận diện ý định đạt độ chính xác tuyệt đối trên tập kiểm thử độc lập với thời gian phản hồi chỉ hơn 1 mili-giây."*

---

### SLIDE 39: THỰC NGHIỆM 4: MÔ PHỎNG CHU KỲ ÔN TẬP SMART SRS
* **Nội dung slide**:
  - **Học viên A (Nhớ tốt, phản xạ nhanh 1.2s)**: Chu kỳ giãn nhanh từ 1 ngày $\to$ 2.2 ngày $\to$ **5 ngày**.
  - **Học viên B (Đúng nhưng ngập ngừng 4.8s)**: Chu kỳ giãn chậm hơn: 1 ngày $\to$ 1.5 ngày $\to$ **2.5 ngày**.
  - **Học viên C (Sai 1 lần)**: Bị phạt co chu kỳ về **13.5 giờ** (ôn lại ngay trong ngày).
  - **Học viên D (Sai liên tiếp 3 lần)**: Bị phạt nặng co chu kỳ về **1.2 giờ** (bắt học lại tức thì).
* **Lời thoại**: *"Thực nghiệm mô phỏng chỉ ra thuật toán Smart SRS phản ứng rất nhạy: học sinh nhớ tốt được giãn ngày ôn, còn học sinh hay quên sẽ bị nhắc bài liên tục."*

---

### SLIDE 40: THỰC NGHIỆM 5: THỬ THÁCH RÚT DÂY MẠNG (100% OFFLINE TEST)
* **Nội dung slide**:
  - **Kịch bản kiểm thử**: Ngắt hoàn toàn Wi-Fi và mạng dây Internet của máy chủ.
  - **Thực hiện 15 thao tác liên tục**: Đăng nhập, quay Gacha, vượt ải xáo từ, nộp bài viết tự do, xem điểm AI chấm, xem nhận xét Master G, kiểm tra lịch ôn SRS.
  - **Kết quả**: **15/15 thao tác thành công 100%**, không xuất hiện bất kỳ thông báo lỗi mạng nào.
* **Giải thích bình dân**: Kể cả khi ngồi trên máy bay hay về quê mất mạng, học viên vẫn có thể mở máy ra học và được AI chấm bài bình thường.
* **Lời thoại**: *"Đây là bài kiểm tra ấn tượng nhất: Rút hoàn toàn dây mạng Internet, hệ thống vẫn chấm bài và vận hành trơn tru 100% các tính năng học tập."*

---

### SLIDE 41: KẾT QUẢ ĐO LƯỜNG ĐỘ TRỄ: NHANH HƠN 150 LẦN
* **Nội dung slide**:

| Tác vụ kiểm tra | Ứng dụng Thuần Cloud LLM | Nền tảng Hybrid AI (TAP) | Mức độ Tăng tốc |
| :--- | :--- | :--- | :--- |
| **Chấm điểm ngữ pháp câu** | 2.100 - 3.800 ms | **18.5 ms** | **Nhanh gấp ~150 lần** |
| **Phân loại ý định câu chat**| 1.200 - 1.800 ms | **1.2 ms** | **Nhanh gấp ~1.200 lần**|
| **Xác định cấp độ từ vựng** | 800 - 1.500 ms | **0.01 ms** | **Gần như tức thời** |
| **Tính toán lịch ôn chống quên**| Không hỗ trợ nội suy | **0.4 ms** | **Tức thời** |

* **Lời thoại**: *"So với việc gửi lên đám mây mất 2-3 giây, giải pháp cục bộ của TAP chấm câu chỉ trong 18.5 mili-giây, nhanh hơn tới 150 lần, xóa bỏ hoàn toàn cảm giác chờ đợi."*

---

### SLIDE 42: KẾT QUẢ TIẾT KIỆM CHI PHÍ VÀ TÀI NGUYÊN
* **Nội dung slide**:
  - **Cắt giảm 87.5% lượng Token đám mây**: Nhờ xử lý tại chỗ và cơ chế nén bộ nhớ ngữ cảnh.
  - **Bài toán chi phí cho 10.000 người dùng hàng ngày**:
    - Dùng Cloud LLM thuần túy: Tốn **$500 - $700 USD/tháng** tiền API.
    - Dùng Hybrid AI của TAP: Giảm xuống **< $35 USD/tháng** (thậm chí 0 đồng nếu dùng xoay vòng khóa miễn phí).
  - **Mức tiêu thụ RAM**: Toàn bộ hệ thống chạy êm ái dưới **450 MB RAM**.
* **Lời thoại**: *"Về mặt kinh tế, hệ thống giúp tiết kiệm tới 87.5% chi phí API. Một trường học có 10.000 học sinh có thể tiết kiệm hàng chục triệu đồng tiền máy chủ mỗi tháng."*

---

### SLIDE 43: ĐỘ CHÍNH XÁC KHOA HỌC CỦA TỪNG BỘ NÃO
* **Nội dung slide**:
  - **Bộ não GEC DistilBERT**: Đạt độ chính xác **82.38%**, F1-Score **0.811** trên tập chuẩn CoLA.
  - **Bộ não Intent Classifier**: Macro F1-Score đạt **0.988**.
  - **Bộ não Smart SRS**: Sai số tuyệt đối trung bình (MAE) chỉ **1.84 giờ** so với thực tế.
  - **Bộ não CEFR Zipf**: Hệ số tương quan Spearman đạt **$\rho = 0.842$** so với từ điển Cambridge.
  - **Bộ não Recommender**: Tỷ lệ gợi ý trúng đích Hit Rate @ 5 đạt **78.6%**.
* **Lời thoại**: *"Tất cả các bộ não AI cục bộ đều được kiểm chứng bằng các chỉ số khoa học định lượng khắt khe, bảo đảm tính chính xác và tin cậy cao."*

---

### SLIDE 44: ĐÁNH GIÁ TRẢI NGHIỆM NGƯỜI DÙNG THỰC TẾ
* **Nội dung slide**:
  - Thử nghiệm trên nhóm 30 học viên trong 4 tuần:
    - **Tỷ lệ giữ chân sau 7 ngày (Day-7 Retention)**: Đạt **73.3%** (vượt xa mức trung bình 25-30% của các ứng dụng EdTech thông thường).
    - **Thời gian học trung bình**: **18.5 phút/ngày** nhờ cơ chế game Text-RPG và vòng lặp Gacha.
    - **Điểm hài lòng hệ thống (SUS Score)**: Đạt **86.4 / 100 điểm** (Xếp hạng A - Xuất sắc).
* **Lời thoại**: *"Khảo sát trên 30 người dùng thử trong 4 tuần cho thấy tỷ lệ giữ chân đạt 73.3%, cao gấp hơn 2.5 lần so với các phần mềm học thông thường."*

---

### SLIDE 45: GIẢI QUYẾT BÀI TOÁN "TAM GIÁC VÀNG" TRONG KỸ THUẬT AI
* **Nội dung slide**:
  - **Đỉnh 1: Tốc độ siêu việt**: Phản hồi dưới 20 mili-giây nhờ chạy trực tiếp trên CPU.
  - **Đỉnh 2: Chi phí tiệm cận 0 đồng**: Không tốn token đám mây cho các thao tác hàng ngày.
  - **Đỉnh 3: Trải nghiệm thông minh ngữ cảnh**: Vẫn có sự tham gia của Cloud LLM khi cần viết cốt truyện và nhận xét cá tính.
* **Lời thoại**: *"Hệ thống đã giải quyết thành công bài toán Tam giác Vàng trong kỹ thuật phần mềm AI: vừa nhanh, vừa rẻ, lại vừa thông minh."*

---

### SLIDE 46: TỔNG KẾT KẾT QUẢ ĐẠT ĐƯỢC
* **Nội dung slide**:
  - [x] Huấn luyện và lượng tử hóa thành công mô hình `DistilBERT INT8` chạy thời gian thực trên CPU.
  - [x] Xây dựng trọn vẹn 6 thuật toán AI cục bộ chạy 100% ngoại tuyến.
  - [x] Thiết kế Cổng bất định và cơ chế xoay vòng khóa API phòng thủ lỗi 429.
  - [x] Hoàn thiện ứng dụng Web Full-stack đầy đủ tính năng: Bento UI, Gacha, Text-RPG, Lộ trình A1-C2.
  - [x] Kiểm chứng định lượng toàn bộ hệ thống qua các kịch bản đối chuẩn.
* **Lời thoại**: *"Đề tài đã hoàn thành 100% các mục tiêu đặt ra, tạo ra một sản phẩm hoàn chỉnh có tính ứng dụng cao và nền tảng thuật toán vững vàng."*

---

### SLIDE 47: NHÌN NHẬN HẠN CHẾ CỦA HỆ THỐNG
* **Nội dung slide**:
  - **Bản chất GEC**: Mô hình DistilBERT hiện tại mới dừng ở mức phát hiện lỗi đúng/sai, việc gợi ý sửa câu chi tiết vẫn cần kết hợp với luật hoặc LLM.
  - **Khởi đầu lạnh của SRS (Cold-Start)**: Thuật toán Ebbinghaus cần học viên làm bài tối thiểu 10 lần mới bắt đầu dự đoán cá nhân hóa thật sự chuẩn xác.
  - **Vector TF-IDF còn thưa**: Bộ gợi ý từ vựng đôi khi chưa bắt được các từ đồng nghĩa sâu nếu chúng không trùng từ khóa giải nghĩa.
* **Lời thoại**: *"Nhìn nhận khách quan, hệ thống vẫn còn một số điểm cần cải thiện như việc tự động sửa câu trực tiếp và khắc phục vấn đề khởi đầu lạnh của thuật toán trí nhớ."*

---

### SLIDE 48: HƯỚNG PHÁT TRIỂN TIẾP THEO
* **Nội dung slide**:
  - **Tích hợp Seq2Seq GEC cục bộ**: Nén mô hình nhỏ như **Flan-T5-small** để vừa chấm điểm vừa viết lại câu đúng ngay trên CPU.
  - **Nâng cấp chuẩn FSRS**: Chuyển đổi mô hình trí nhớ sang chuẩn FSRS hiện đại với 3 biến trạng thái nhận thức.
  - **Đánh giá phát âm qua giọng nói (Speech AI)**: Tích hợp mô hình Whisper nén cục bộ để chấm điểm phát âm tiếng Anh trực tiếp từ micro.
* **Lời thoại**: *"Trong giai đoạn tới, em sẽ phát triển thêm tính năng nhận diện giọng nói để chấm điểm phát âm và nâng cấp mô hình AI tự sửa câu ngay tại máy."*

---

### SLIDE 49: LỜI CẢM ƠN & PHIÊN THẢO LUẬN / Q&A
* **Nội dung slide**:
  - *"Em xin chân thành cảm ơn Quý Thầy Cô trong Hội đồng đã lắng nghe!"*
  - **Tác giả**: Nguyễn Kim Thành.
  - **Đề tài**: Xây dựng hệ thống học Tiếng Anh tương tác ngữ cảnh ứng dụng kiến trúc Hybrid AI.
  - **Demo trực tiếp**: Sẵn sàng trình diễn các tính năng và bài test ngắt mạng 100% Offline.
* **Lời thoại**: *"Em xin cảm ơn Thầy Cô đã lắng nghe. Em đã chuẩn bị sẵn hệ thống để trình chiếu Demo trực tiếp và xin kính mời Thầy Cô đặt câu hỏi phản biện!"*

---

# PHẦN 8: TRẢ LỜI 3 CÂU HỎI TRỌNG TÂM CỦA HỘI ĐỒNG (SÚC TÍCH & BẢN CHẤT)

---

## CÂU HỎI 1: NHIỆM VỤ GIẢI QUYẾT CỤ THỂ?

Hệ thống giải quyết **4 nhiệm vụ cụ thể**:

1. **Chấm điểm ngữ pháp câu viết tức thì (< 20ms)**: Học viên gõ một câu tự do là máy tính chấm ngay đúng hay sai trên thang điểm 10, tính được độ tự tin của câu đó mà không cần đợi 2-3 giây gọi API đám mây.
2. **Cá nhân hóa lịch ôn tập chống quên (Smart SRS)**: Bỏ cơ chế ôn tập cứng nhắc (như 1 ngày, 3 ngày cố định). Hệ thống đo số lần làm sai và số giây học viên ấp úng ngập ngừng để tính ra đúng thời điểm não bộ sắp quên từ đó và nhắc ôn tập lại.
3. **Hiểu ý định người học trong chớp mắt (1.2ms)**: Đọc câu chat tự do để biết ngay học viên muốn hỏi từ vựng, hỏi ngữ pháp, hay đang ra lệnh cho nhân vật trong game RPG mà không cần phụ thuộc vào mạng Internet.
4. **Cắt giảm chi phí và vận hành khi mất mạng**: Giúp hệ thống chạy trơn tru 100% tính năng khi không có Internet; khi có mạng thì giải quyết hơn 83% công việc tại máy, tiết kiệm hơn 85% tiền mua API.

---

## CÂU HỎI 2: HƯỚNG GIẢI QUYẾT (MÔ TẢ TỪNG BƯỚC XÂY DỰNG CHƯƠNG TRÌNH)

### 1. Dataset & Bản đồ Tri thức:
* **Bản đồ ngữ pháp 6 bậc CEFR (A1 - C2)**: Chuẩn hóa toàn bộ cấu trúc câu từ thì đơn giản đến đảo ngữ điều kiện loại 3, câu chẻ nhấn mạnh; gắn sẵn từ vựng và bài thi xáo trộn từ tương ứng cho từng chặng.
* **Dữ liệu chuẩn quốc tế**:
  * Tập **CoLA (GLUE Benchmark)**: 8.551 câu tiếng Anh chuẩn và lỗi sai để huấn luyện DistilBERT.
  * Tập **Oxford 5000**: Bảng băm 5.000 từ vựng học thuật tra cứu trong 0.001ms.
  * Ngữ liệu **Wordfreq**: Kho tần suất hàng tỷ từ để phân cấp độ hiếm của từ mới.
  * Tập **TAP-NLU**: 200 mẫu câu hỏi đáp phân loại 4 nhóm ý định.

### 2. Mô hình & Thuật toán Cốt lõi:
* `DistilBERT INT8 Transformer`: Chấm ngữ pháp câu cục bộ trên CPU.
* `Uncertainty Gate (Cổng bất định)`: Ngưỡng tự tin $\tau = 0.55$ để quyết định máy tự chấm hay gửi lên Gemini.
* `TF-IDF + Mạng Nơ-ron MLP (100 -> 50 -> 4)`: Phân loại ý định câu chat trong 1.2ms.
* `Hồi quy phi tuyến Ebbinghaus + Thuật toán TRF`: Tự học và dự đoán chu kỳ ôn tập trí nhớ.
* `Content-Based Cosine Recommender`: Gợi ý từ vựng theo chùm liên tưởng.
* `Tần suất định luật Zipf`: Gán nhãn CEFR cho từ vựng trong $O(1)$.
* `Gemini 2.5 Flash + Ring-Buffer Key + Sliding Window`: Đám mây dự phòng và nén bộ nhớ game RPG.

### 3. Các bước Triển khai Thực tế (8 Bước):
* **Bước 1**: Huấn luyện DistilBERT trên tập dữ liệu CoLA bằng PyTorch, lưu checkpoint gốc FP32 (255MB).
* **Bước 2**: Lượng tử hóa động INT8 bằng `torch.quantization.quantize_dynamic`, nén mô hình xuống 132MB và tăng tốc 7.2 lần.
* **Bước 3**: Huấn luyện pipeline TF-IDF + MLP phân loại ý định, lưu file `intent_model.pkl`.
* **Bước 4**: Lập trình thuật toán Smart SRS bằng `scipy.optimize.curve_fit` với phương pháp Trust Region Reflective (TRF).
* **Bước 5**: Xây dựng backend Flask chuẩn MVC (`ai_controller`, `game_controller`, `roadmap_controller`) và cơ sở dữ liệu MySQL.
* **Bước 6**: Lập trình bộ kết nối Google Gemini với cơ chế xoay vòng chìa khóa chống lỗi 429 và truyền luồng Server-Sent Events (SSE).
* **Bước 7**: Xây dựng giao diện Bento Grid, bàn cờ Text-RPG và vòng lặp Gacha bằng HTML/CSS/JS thuần.
* **Bước 8**: Viết kịch bản kiểm thử tự động `test_critique_benchmark.py` để đo đạc định lượng tốc độ và độ chính xác.

---

## CÂU HỎI 3: DỰ KIẾN PHƯƠNG PHÁP & CHỈ SỐ ĐÁNH GIÁ

Hệ thống được đánh giá qua **4 nhóm chỉ số định lượng khắt khe**:

1. **Chỉ số Học máy (Machine Learning Metrics)**:
   * **GEC DistilBERT**: Đạt **Accuracy 82.38%**, **F1-Score 0.811** trên tập chuẩn CoLA.
   * **Intent Classifier**: Đạt **Macro F1 0.988** trên tập kiểm thử độc lập.
   * **Smart SRS**: Sai số tuyệt đối trung bình **MAE 1.84 giờ** (dự đoán sát điểm rơi quên lãng).
   * **CEFR Zipf**: Hệ số tương quan thứ bậc Spearman **$\rho = 0.842$** so với từ điển Cambridge EVP.
   * **Gợi ý từ vựng**: Tỷ lệ gợi ý trúng đích **Hit Rate @ 5 đạt 78.6%**.

2. **Chỉ số Kỹ thuật & Tối ưu Tài nguyên (Engineering Metrics)**:
   * **Độ trễ phản hồi**: Local AI đạt **18.51 ms** (nhanh hơn **~150 lần** so với gọi Cloud API mất 2.800 ms).
   * **Tỷ lệ nén**: Nén **48.2% dung lượng đĩa** và tiết kiệm **51.9% bộ nhớ RAM**.
   * **Tiết kiệm chi phí**: Cắt giảm **87.5% lượng Token API**, hơn **83.3%** yêu cầu được xử lý dứt điểm tại chỗ.

3. **Chỉ số Kháng lỗi & Bền bỉ (Robustness Metrics)**:
   * **Chịu tải Quota**: Tỷ lệ lỗi gián đoạn dịch vụ đạt **0.0%** khi gọi dồn dập nhờ bộ xoay vòng khóa Ring-Buffer.
   * **Tự chủ ngoại tuyến**: Đạt **100.0%** tính năng hoạt động bình thường khi rút hoàn toàn dây mạng Internet.

4. **Chỉ số Sư phạm & Trải nghiệm (Pedagogical & UX Metrics)**:
   * **Tỷ lệ giữ chân Day-7**: Đạt **73.3%** sau 4 tuần thử nghiệm (cao gấp 2.5 lần ứng dụng thông thường).
   * **Thời lượng học hàng ngày**: Đạt **18.5 phút/ngày** nhờ sức hút của Game Text-RPG và Gacha.
   * **Điểm hài lòng hệ thống (SUS Score)**: Đạt **86.4 / 100 điểm** (Xếp hạng A - Xuất sắc).
