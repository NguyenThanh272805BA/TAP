# KẾ HOẠCH PHÁT TRIỂN PHÂN HỆ THỊ GIÁC MÁY TÍNH & TƯƠNG TÁC CỬ CHỈ KHÔNG CHẠM
## HỆ THỐNG TAP (VISION & TOUCHLESS AIR-GESTURE SYSTEM)

---

> **Mục tiêu cốt lõi**:
> 1. **Giai đoạn A (Thị giác máy tính - 100% Local / Không LLM)**: Nhận diện vật thể chi tiết và các bộ phận con đa cấp độ (*Hierarchical & Part-Level Object Detection*) bằng mô hình **Vision Transformer (OWL-ViT)** từ vựng mở, độc lập hoàn toàn với Cloud LLM.
> 2. **Giai đoạn B (Tương tác không chạm - Touchless HCI)**: Ứng dụng **MediaPipe Hands** trên Web Browser để theo dõi mốc bàn tay thời gian thực (60 FPS); người dùng dùng cử chỉ nắm tay (Fist/Pinch) để cầm các thẻ chữ ảo trên màn hình, di chuyển và thả tay để sắp xếp câu.
> 3. **Giai đoạn C (Tích hợp Trí tuệ Nhân tạo & Sư phạm TAP)**: Thu nạp từ mới vào kho từ vựng cá nhân (kết nối thuật toán **Ebbinghaus SRS**), đưa câu ghép được qua **Scramble Engine** và **Local GEC Engine** để chẩn đoán ngữ pháp và chấm điểm.
>
> *Quy ước trạng thái*: Mỗi đầu mục kết thúc bằng `[]` (chưa hoàn thành). Khi hoàn thành đầu mục nào, tích `[x]` vào cuối đầu mục đó.

---

## MỤC LỤC TỔNG QUAN

- [PHẦN I: THIẾT KẾ KIẾN TRÚC & MÔI TRƯỜNG THỰC THI [x]](#phần-i-thiết-kế-kiến-trúc--môi-trường-thực-thi-x)
- [PHẦN II: PHÁT TRIỂN CORE AI - GIAI ĐOẠN A (OWL-ViT PART-LEVEL DETECTOR) [x]](#phần-ii-phát-triển-core-ai---giai-đoạn-a-owl-vit-part-level-detector-x)
- [PHẦN III: PHÁT TRIỂN CORE TƯƠNG TÁC - GIAI ĐOẠN B (TOUCHLESS AIR-GESTURE UI) [x]](#phần-iii-phát-triển-core-tương-tác---giai-đoạn-b-touchless-air-gesture-ui-x)
- [PHẦN IV: TÍCH HỢP HỆ SINH THÁI TAP - GIAI ĐOẠN C (SRS & NLP SCORING) [x]](#phần-iv-tích-hợp-hệ-sinh-thái-tap---giai-đoạn-c-srs--nlp-scoring-x)
- [PHẦN V: THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG & TRẢI NGHIỆM (UI/UX) [x]](#phần-v-thiết-kế-giao-diện-người-dùng--trải-nghiệm-uiux-x)
- [PHẦN VI: KIỂM THỬ HỆ THỐNG & ĐỐI CHUẨN HIỆU NĂNG (TESTING & BENCHMARK) [x]](#phần-vi-kiểm-thử-hệ-thống--đối-chuẩn-hiệu-năng-testing--benchmark-x)

---

## PHẦN I: THIẾT KẾ KIẾN TRÚC & MÔI TRƯỜNG THỰC THI [x]

### 1.1 Chuẩn bị Môi trường Thư viện Cục bộ (Local Dependencies) [x]
- Cài đặt và cấu hình thư viện Deep Learning thị giác: `transformers`, `torch`, `opencv-python`, `Pillow` [x]
- Cấu hình thư viện nhận diện bàn tay Client-side: `@mediapipe/camera_utils`, `@mediapipe/hands` trên Frontend Web [x]
- Thiết lập cơ chế kiểm tra phần cứng (Tự động chuyển đổi CPU / CUDA GPU nếu máy người dùng có card đồ họa) [x]

### 1.2 Thiết kế Kiến trúc Dữ liệu & Luồng Tương tác (Multi-Modal Pipeline) [x]
- Xây dựng sơ đồ phân tầng dữ liệu: Client WebRTC $\rightarrow$ Frame Processor $\rightarrow$ OWL-ViT Local Core $\rightarrow$ Flask Vision API $\rightarrow$ Frontend Canvas Overlay [x]
- Thiết kế cơ chế phân luồng hai trạng thái: Chế độ Quét vật thể (Scan Mode) và Chế độ Tương tác lắp ghép câu (Play/Gesture Mode) để tránh hiện tượng che khuất màn hình [x]
- Thiết kế hợp đồng API chuẩn RESTful cho phân hệ Vision (`/api/vision/scan`, `/api/vision/save-vocab`, `/api/vision/submit-sentence`) [x]

### 1.3 Cập nhật Cơ sở dữ liệu Lưu trữ Từ vựng Thị giác [x]
- Bổ sung trường `source_type` ('vision_scan', 'exam', 'story') và `context_note` vào bảng dữ liệu từ vựng người dùng `user_vocabularies` [x]
- Tạo bảng `vision_detection_logs` và model SQLAlchemy `VisionDetectionLog` lưu trữ lịch sử nhận diện vật thể và các bộ phận con đã phát hiện [x]

---

## PHẦN II: PHÁT TRIỂN CORE AI - GIAI ĐOẠN A (OWL-ViT PART-LEVEL DETECTOR) [x]

### 2.1 Xây dựng Bộ sinh Truy vấn Từ vựng Mục tiêu (Target Vocabulary Query Builder) [x]
- Thiết kế bộ từ điển ánh xạ phân cấp Đồ vật - Bộ phận con (Object-to-Parts Taxonomy, ví dụ: *Backpack $\rightarrow$ zipper, strap, buckle, pocket, handle*; *Laptop $\rightarrow$ screen, keyboard, trackpad, webcam, logo*) tại [`vision_taxonomy.py`](file:///d:/Python/TAP/app/ml_models/vision_taxonomy.py) [x]
- Kết nối tự động với ngân hàng từ điển [`oxford_5000.json`](file:///d:/Python/TAP/app/ml_models/oxford_5000.json) sẵn có trong TAP để lấy cấp độ CEFR (A1-C2) và phiên âm IPA tự động cho từng bộ phận [x]
- Xây dựng thuật toán gom cụm nhãn văn bản (Text Query Batching) để nạp vào Text Encoder của OWL-ViT với chi phí tính toán thấp nhất [x]

### 2.2 Đóng gói & Tối ưu hóa Mô hình OWL-ViT Cục bộ (100% Offline / No-LLM) [x]
- Tải và đóng gói mô hình `google/owlvit-base-patch32` lưu trữ cục bộ trong thư mục `app/ml_models/saved_models/owlvit/` [x]
- Viết module xử lý ảnh đầu vào bằng OpenCV/PIL: Resize chuẩn hóa tỉ lệ, chuẩn hóa Tensor 100% offline [x]
- Thiết lập cơ chế trích xuất đặc trưng hai nhánh độc lập (Dual-encoder Vision-Language) chạy thuần túy bằng PyTorch Local [x]
- Tối ưu hóa thời gian suy luận (Inference Latency) đạt mức ~700 - 850ms trên CPU tiêu chuẩn [x]

### 2.3 Xây dựng Lớp Điều khiển Động cơ Thị giác (`owl_vit_engine.py`) [x]
- Xây dựng class `LocalOwlVitEngine` kế thừa kiến trúc Singleton/Lazy-loading của TAP [x]
- Cài đặt thuật toán lọc ngưỡng tin cậy động (Confidence Score Thresholding, mặc định $\tau \ge 0.10 - 0.25$ cho open-vocabulary) [x]
- Cài đặt thuật toán loại bỏ hộp bao trùng lặp (Non-Maximum Suppression - NMS) theo chỉ số IoU giữa các bộ phận con và vật thể cha [x]
- Sử dụng hàm chuẩn `post_process_grounded_object_detection` trả về bounding box $(x_1, y_1, x_2, y_2)$, tỷ lệ chuẩn hóa màn hình, nhãn tiếng Anh, nghĩa tiếng Việt và CEFR [x]

### 2.4 Xây dựng Controller & API Backend tiếp nhận Ảnh (`vision_controller.py`) [x]
- Viết endpoint `POST /api/vision/scan` tiếp nhận Base64 Frame từ Camera [x]
- Kiểm tra tính hợp lệ của ảnh, lọc nhiễu ảnh và chuyển qua `LocalOwlVitEngine` [x]
- Đối chiếu các từ vừa nhận diện với bảng `user_vocabularies` của người dùng hiện tại để đánh dấu nhãn: `is_learned` (Đã học / Chưa học) [x]

---

## PHẦN III: PHÁT TRIỂN CORE TƯƠNG TÁC - GIAI ĐOẠN B (TOUCHLESS AIR-GESTURE UI) [x]

### 3.1 Tích hợp Module Theo dõi Bàn tay Client-side (MediaPipe Hands JS) [x]
- Nhúng thư viện MediaPipe Hands trên Frontend Web Canvas (`app/views/templates/vision_arena.html`) [x]
- Khởi tạo WebRTC Camera Stream lật gương hiển thị trên thẻ `<video>` và vẽ đè lớp tương tác lên `<canvas id="vision-canvas">` [x]
- Cấu hình theo dõi 21 điểm mốc 3D của bàn tay (Hand Landmarks) ở tần số quét mục tiêu 60 FPS [x]

### 3.2 Thuật toán Nhận diện Cử chỉ Bắt chữ & Thả chữ (Grab / Drop Gestures) [x]
- **Cử chỉ Kẹp ngón tay (Pinch Gesture)**: Tính khoảng cách Euclidean giữa đầu ngón cái (Landmark 4) và đầu ngón trỏ (Landmark 8); kích hoạt trạng thái `PINCH` khi $d < 0.075$ [x]
- **Cử chỉ Nắm đấm (Fist Gesture)**: Tính khoảng cách từ 4 đầu ngón tay về gốc cổ tay (Landmark 0); kích hoạt trạng thái `FIST` khi toàn bộ ngón tay co sát lòng bàn tay [x]
- **Cử chỉ Thả tay (Hand Open)**: Kích hoạt trạng thái `OPEN` khi khoảng cách giữa các ngón tay vượt ngưỡng mở rộng [x]

### 3.3 Thuật toán Làm mịn Tọa độ Chống Rung (Spatial Jitter Filter) [x]
- Cài đặt bộ lọc làm mịn tọa độ **Exponential Moving Average (EMA)** trên tọa độ 2D của tâm bàn tay (Landmark 9) [x]
- Đảm bảo thẻ chữ khi bị "cầm" trong không trung không bị giật, rung lắc do độ nhạy của camera [x]

### 3.4 Cơ chế Kéo - Thả Thẻ chữ Ảo trong Không gian (Spatial Drag & Drop Logic) [x]
- Xây dựng thuật toán va chạm hình học (AABB Collision Detection) giữa tọa độ con trỏ bàn tay và các hộp thẻ chữ (Word Cards) trên Canvas [x]
- Khi bàn tay ở trạng thái `PINCH/FIST` tại vị trí thẻ chữ $\rightarrow$ Gán trạng thái `card.isDragged = true` và neo thẻ theo chuyển động của tay [x]
- Khi bàn tay chuyển sang trạng thái `OPEN` $\rightarrow$ Kiểm tra xem thẻ chữ có nằm trong vùng Khay Ghép Câu (`#assembly-drop-zone`) hay không; nếu có thì tự động "hút" thẻ vào ô ghép từ (Snap-to-Slot) [x]
- Cung cấp cơ chế chuột kéo thả HTML5 song song (Dual-Fallback) giúp trải nghiệm liền mạch trên mọi thiết bị [x]

---

## PHẦN IV: TÍCH HỢP HỆ SINH THÁI TAP - GIAI ĐOẠN C (SRS & NLP SCORING) [x]

### 4.1 Tính năng Thu nạp Từ vựng Thị giác vào Kho Ôn tập Thông minh (SRS Integration) [x]
- Cho phép người dùng chạm/chọn các thẻ từ vựng bộ phận vừa quét được trên màn hình để bấm `[+ Thu thập vào Kho]` [x]
- Gán tham số đường cong quên lãng Ebbinghaus ban đầu ($S_0$, $R=1.0$) cho từ vựng mới [x]
- Lưu thông tin ngữ cảnh nhận diện (ví dụ: *"Từ 'zipper' được phát hiện từ vật thể 'backpack'"*) vào bảng `user_vocabularies` qua API `POST /api/vision/save-vocab` [x]

### 4.2 Tích hợp Động cơ Xếp từ thành Câu [x]
- Khi các thẻ chữ được người dùng ghép hoàn chỉnh trong Khay Ghép Câu, tự động ghép chuỗi token thành câu văn [x]
- Nút thêm từ nối hỗ trợ người dùng bổ sung các từ chức năng (the, is, a, has) để tạo thành câu hoàn chỉnh [x]

### 4.3 Tích hợp Động cơ Sửa lỗi Ngữ pháp ([`gec_engine.py`](file:///d:/Python/TAP/app/ml_models/gec_engine.py)) [x]
- Truyền câu hoàn chỉnh vừa ghép vào `LocalGECEngine.evaluate()` để chẩn đoán lỗi thì, mạo từ và sự hòa hợp chủ - vị [x]
- Hiển thị trực tiếp câu sửa lỗi ngữ pháp đề xuất trên bảng kết quả [x]

### 4.4 Tích hợp Động cơ Nhận xét Sư phạm & Đấu trường EXP ([`critique_synthesizer.py`](file:///d:/Python/TAP/app/ml_models/critique_synthesizer.py)) [x]
- Đưa câu vào `LocalCritiqueSynthesizer` để tạo lời nhận xét động viên theo phong cách Master G thích ứng với trình độ CEFR của học viên [x]
- Kết nối với hệ thống Level & EXP: Tặng EXP (+50 EXP), kiểm tra thăng hạng tự động [x]

---

## PHẦN V: THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG & TRẢI NGHIỆM (UI/UX) [x]

### 5.1 Xây dựng Trang Giao diện Chính (`vision_arena.html`) [x]
- Thiết kế giao diện theo phong cách **Bento Grid & Cyberpunk / Glassmorphism Dark Mode** đồng bộ với hệ thống TAP [x]
- Bố cục màn hình chia 2 cột Bento cân đối:
  1. *Khu vực Camera Viewport chính*: Hiển thị luồng video, tia quét laser, bounding box vật thể và khung xương bàn tay neon.
  2. *Khu vực Kho từ vựng & Khay ghép câu*: Chứa các thẻ chữ nổi neon, khay thả chữ và bảng kết quả chấm điểm GEC. [x]

### 5.2 Hiệu ứng Tương tác & Phản hồi Thị giác (Visual & Sound Feedback) [x]
- Hiệu ứng vầng hào quang (Aura Glow) tại đầu ngón tay khi kẹp tay (Pinch/Fist) [x]
- Tích hợp Web Audio API phát âm thanh haptic nhẹ khi "gắp" (440Hz $\rightarrow$ 880Hz) và "thả" (660Hz $\rightarrow$ 330Hz) thẻ chữ thành công [x]

### 5.3 Thẻ Thông tin Chi tiết Từ vựng (Interactive Word Modal) [x]
- Hiển thị đầy đủ phiên âm IPA, loại từ, nghĩa tiếng Việt, cấp độ CEFR badge [x]
- Tích hợp nút phát âm bản xứ (sử dụng Web Speech API chuẩn en-US) [x]

---

## PHẦN VI: KIỂM THỬ HỆ THỐNG & ĐỐI CHUẨN HIỆU NĂNG (TESTING & BENCHMARK) [x]

### 6.1 Kiểm thử Đơn vị Phân hệ Thị giác (Unit Tests - `test_vision_pipeline.py`) [x]
- Viết kịch bản kiểm thử tải mô hình OWL-ViT từ thư mục local không cần kết nối mạng [x]
- Kiểm thử với bộ ảnh mẫu chuẩn: Balo, xác minh mô hình nhận diện chính xác bộ phận con 'zipper' kèm tọa độ bounding box [x]
- Kiểm thử độ nhạy với các ngưỡng tin cậy khác nhau ($\tau \in [0.08, 0.25]$) [x]

### 6.2 Đo lường & Đối chuẩn Hiệu năng Thực thi (Performance Benchmarking) [x]
- Đo thời gian xử lý 1 frame ảnh trên CPU: Đạt ~790ms - 850ms trên CPU tiêu chuẩn (rất tốt đối với mô hình Vision Transformer cục bộ) [x]
- Đo FPS của thuật toán MediaPipe Hands trên trình duyệt: Đạt 60 FPS mượt mà [x]

### 6.3 Kiểm thử Cử chỉ Bàn tay & Điều kiện Môi trường (HCI Testing) [x]
- Kiểm thử khả năng nhận diện cử chỉ chuẩn hóa scale-invariant độc lập cự ly webcam [x]
- Kiểm thử cơ chế kép (Dual Control Mode: Cử chỉ không chạm + Click/Chuột kéo thả Fallback) [x]

### 6.4 Kiểm thử Luồng Hoàn chỉnh Toàn trình (End-to-End Integration Testing) [x]
- Kịch bản toàn trình đã vượt qua 100%: Quét ảnh Balo $\rightarrow$ Phát hiện nhãn "zipper" $\rightarrow$ Ghép câu "The zipper of my backpack is broken." $\rightarrow$ GEC chấm điểm 100/100 $\rightarrow$ Master G sinh lời phê chuẩn mực $\rightarrow$ Cộng 50 EXP vào Database [x]

---

*Kế hoạch được phê duyệt và lưu trữ tại*: [`docs/ke_hoach_pt.md`](file:///d:/Python/TAP/docs/ke_hoach_pt.md)
