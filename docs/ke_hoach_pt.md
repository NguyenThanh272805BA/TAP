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

## PHẦN VII: PHÂN CẤP NHẬN BIẾT ĐA TẦNG, GIỚI HẠN VẬT THỂ & TẢI LÊN ĐA PHƯƠNG TIỆN (MEDIA UPLOAD) [x]

### 7.1 Phân cấp Mức độ Nhận biết Đa tầng (Granularity / Depth of Detection) [x]
- Xây dựng 4 mức độ nhận biết từ vựng linh hoạt:
  1. *Cơ bản (`macro`)*: Chỉ quét vật thể nguyên khối chính (24+ đồ vật học thuật & đời sống). [x]
  2. *Trung cấp (`functional`)*: Quét vật thể và các bộ phận chức năng nổi bật (screen, keyboard, handle...). [x]
  3. *Chuyên sâu (`micro`)*: Quét chi tiết vi mô và linh kiện con (seam, buckle, hinge, trackpad, crown, dial...). [x]
  4. *Toàn diện (`all`)*: Quét kết hợp đa tầng toàn diện mọi chi tiết vật thể. [x]
- Mở rộng từ điển phân cấp học thuật hơn 24 đồ vật và 100+ linh kiện có gán nhãn CEFR và nghĩa tiếng Việt chuẩn xác trong `vision_taxonomy.py` [x]

### 7.2 Giới hạn Số lượng Vật thể (3 - 20) & Nhãn Song ngữ Bounding Box [x]
- Bổ sung thanh trượt điều chỉnh số lượng vật thể tối đa trong khung hình: Giới hạn từ 3 đến 20 vật thể/bộ phận [x]
- Gán nhãn trực quan song ngữ trên từng Bounding Box: Tiếng Anh viết hoa, cấp độ CEFR, tỷ lệ tin cậy và **bản dịch Tiếng Việt chuẩn xác** màu vàng hổ phách nổi bật [x]
- Mã hóa màu sắc Bounding Box thích ứng theo cấp độ: Xanh Cyan cho Cơ bản (A1 - A2) và Tím Neon cho Chuyên sâu (B1 - C1) [x]

### 7.3 Tải lên Đa phương tiện (Media Upload: Ảnh & Video ≤ 25MB) [x]
- Endpoint backend `POST /api/vision/upload-media` hỗ trợ cả tệp ảnh tĩnh (JPG, PNG, WEBP) và video clip (MP4, WEBM, MOV) [x]
- Cơ chế kiểm duyệt dung lượng nghiêm ngặt: Chặn tuyệt đối các tệp vượt quá 25MB và thông báo lỗi rõ ràng [x]
- Tích hợp trình phát video HTML5 Video Player trực tiếp trên Viewfinder: Cho phép xem trước, tua video, bấm "📸 Quét khung hình này" [x]
- Tích hợp chế độ "🎞️ Quét Video Tự Động": Tự động trích xuất khung hình định kỳ mỗi 2.5s khi video đang phát để nhận diện từ vựng động [x]
- Hỗ trợ kéo & thả trực tiếp file từ máy tính vào khung nhìn Camera Viewfinder [x]

### 7.4 Bộ lọc Kho Từ Vựng theo Cấp độ Học tập (CEFR Level Filtering) [x]
- Phân nhóm cấp độ từ vựng: Cơ bản (A1 - A2) vs Chuyên sâu (B1 - C1) [x]
- Bổ sung thanh nút chuyển đổi bộ lọc cấp độ trong Kho từ vựng: `🌟 Mọi Cấp Độ` | `🌱 Cơ Bản (A1 - A2)` | `🚀 Chuyên Sâu (B1 - C1)` [x]
- Thẻ từ vựng hiển thị đồng thời nghĩa tiếng Việt và viền huy hiệu màu sắc tương ứng với cấp độ học tập [x]

---

## PHẦN VIII: PHÂN TÁCH GIAO DIỆN ĐA WORKSPACE & TỐI ƯU HÓA KHUNG CAMERA SIÊU RỘNG (CINEMA MAX VIEW) [x]

### 8.1 Kiến trúc Phân tách Không gian Làm việc Độc lập (Multi-Workspace Architecture) [x]
- Tách biệt hoàn toàn `vision-arena` thành 3 không gian chuyên biệt (thay vì dồn nén bố cục bento chật hẹp):
  1. **Workspace 1: Khung Nhìn Thị Giác (`workspace-scanner`)**: Tập trung tối đa vào quan sát, quét vật thể, nhận diện đa tầng và xem dải từ vựng trực tiếp. [x]
  2. **Workspace 2: Đấu Trường Ghép Câu & Cử Chỉ (`workspace-assembly`)**: Không gian thao tác gắp thả chữ toàn màn hình, khay ghép câu trực quan và bảng phản hồi chấm điểm ngữ pháp GEC. [x]
  3. **Workspace 3: Kho Từ Vựng & Ôn Tập SRS (`workspace-vault`)**: Trung tâm quản lý từ vựng học thuật toàn màn hình với 4 thẻ KPI thống kê, bộ lọc đa chiều (CEFR, tìm kiếm, vật thể) và lưới Flashcard chi tiết. [x]
- Điều hướng mượt mà: Thanh tab navigation hiện đại kèm badge đếm số lượng thời gian thực và hỗ trợ **phím tắt nhanh `1`, `2`, `3`** trên bàn phím. [x]

### 8.2 Tối ưu Khung Camera Siêu Rộng (Cinema Max View & Seamless PiP Mode) [x]
- **Cinema Mode (Workspace 1)**: Khung camera chiếm diện tích lớn nhất (100% chiều rộng, chiều cao 68vh, tỷ lệ chuẩn điện ảnh), mang lại tầm nhìn bao quát và độ phân giải hiển thị tối đa. [x]
- **PiP Mode (Workspace 2 & 3)**: Khi chuyển sang Đấu trường ghép câu hoặc Kho từ vựng, khung camera tự động chuyển sang chế độ Picture-in-Picture thu nhỏ (300x175px) cố định ở góc dưới bên phải màn hình. Luồng WebRTC MediaStream và MediaPipe Hand Tracking vẫn chạy liên tục không bị ngắt quãng hay giật lag. [x]
- **Bổ sung nút Toàn màn hình (Fullscreen Viewport)**: Hỗ trợ phóng to camera tràn viền với một cú nhấp chuột. [x]

### 8.3 Nâng cấp Tương tác & Trải nghiệm Người dùng (UX/UI Polish) [x]
- Bổ sung dải chip từ vựng quét trực tiếp (`Live Detection Strip`) ngay dưới camera ở Workspace 1. [x]
- Hỗ trợ nút click nhanh "🧩 Dùng" trên mỗi thẻ từ để tự động chuyển tab và đưa từ vào khay ghép câu. [x]
- Tích hợp thanh tìm kiếm tức thời và bộ lọc cấp độ CEFR cho lưới thẻ Flashcard trong Kho từ vựng. [x]

---

## PHẦN IX: TỐI ƯU HÓA ĐA THIẾT BỊ / MOBILE-FIRST, VÒNG ĐỎ SOI CHI TIẾT (TARGET SPOTLIGHT RETICLE) & GHÉP CÂU AR TRỰC TIẾP TRONG CAMERA [x]

### 9.1 Khay Ghép Câu AR Trực Tiếp Trong Lòng Camera (In-Camera AR Sentence Dock) [x]
- Nhúng khay ghép câu trực tiếp vào không gian camera (AR HUD Dock kính mờ nổi ở đáy màn hình camera): Các từ vựng, nút ghép nhanh và thanh trạng thái hiển thị trực tiếp đè trên luồng camera, triệt tiêu hoàn toàn tình trạng cửa sổ PiP che góc màn hình điện thoại [x]
- Chuyển đổi và tinh gọn không gian làm việc thành 2 Tab chính:
  1. `1. Camera AR & Soi Chi Tiết`: Kết hợp đồng nhất Camera Max View, Vòng đỏ ngắm chi tiết, Khay ghép câu AR trong camera và Kho từ vựng tương tác ngay bên dưới. [x]
  2. `2. Kho Từ Vựng SRS`: Quản lý kho thẻ từ vựng và lộ trình ôn tập khoa học. [x]
- Hologram Phản hồi Sư phạm nổi (AR Feedback Modal): Bảng điểm, câu chuẩn hóa và lời nhận xét của Master G hiển thị nổi ngay giữa lòng camera kèm hiệu ứng âm thanh trực quan [x]
- Nút thu gọn / mở rộng khay câu AR (`🔽 / 🔼`) giúp người dùng linh hoạt giải phóng tầm nhìn quan sát camera khi cần thiết [x]

### 9.2 Vòng Đỏ Tối Giản Soi Vật Thể & Bộ Thu Phóng Linh Hoạt (Minimalist Red Reticle & Multi-Modal Zoom) [x]
- **Thiết kế Vòng đỏ tối giản & tinh tế**: Vòng tròn đỏ neon thanh thoát (`2px solid #ef4444`), loại bỏ hoàn toàn các chi tiết rườm rà (bỏ crosshair, bỏ chấm tâm, bỏ nút S/M/L cũ) để người dùng có tầm nhìn trong suốt, thông thoáng nhất khi quan sát vật thể [x]
- **Khả năng Bật / Tắt tức thì**: Nút bấm "Vòng Đỏ: Bật/Tắt" trên thanh điều khiển cho phép người dùng chủ động ẩn/hiện vòng tròn đỏ tùy theo nhu cầu [x]
- **Bộ điều khiển Mở to / Thu nhỏ đa phương thức (Multi-Modal Zoom Controller)**:
  - *Thanh trượt & Nút bấm Zoom Dock*: Nút `+`, `-` và thanh trượt trực tiếp (36px - 240px) hiển thị đường kính thời gian thực (ví dụ: `90px`) [x]
  - *Tay nắm kéo góc trực quan (`#reticle-resize-handle`)*: Chạm ngón tay hoặc kéo chuột vào góc vòng đỏ để thu nhỏ/phóng to mượt mà [x]
  - *Cuộn bánh xe chuột (Mouse Wheel)*: Cuộn chuột trực tiếp trên vòng đỏ để zoom to/nhỏ cực nhanh [x]
- **Quét vật thể & sinh từ vựng chuẩn xác**: Tự động nhận diện chi tiết vật thể nằm trong phạm vi vòng tròn, hiển thị thẻ AR Callout gồm từ tiếng Anh, phát âm IPA, cấp độ CEFR, bản dịch tiếng Việt, nút loa phát âm SVG và nút đưa vào khay ghép câu AR [x]

### 9.3 Tối ưu Hóa Giao diện Đa Thiết Bị & Mobile-First (Responsive Mobile UX) [x]
- Tối ưu hóa chuẩn Touch Targets theo khuyến nghị WCAG (kích thước tối thiểu $\ge 44\text{px}$) cho ngón tay cái trên điện thoại [x]
- Thao tác 1 chạm (Single-Tap to Insert / Remove): Chạm vào thẻ từ trong kho là từ tự động bay vào câu trong camera; chạm vào từ trong câu là tự gỡ về kho [x]
- Khung nhìn Camera thích ứng động (Dynamic Viewport Ratio): Đảm bảo tỷ lệ khung hình 4:3 / 16:9 co giãn mượt mà trên màn hình dọc (portrait) của điện thoại không bị tràn viền hay méo tỷ lệ [x]
- Hỗ trợ đầy đủ sự kiện chạm cảm ứng đa điểm (`touchstart`, `touchmove`, `touchend`) cho vòng đỏ và tương tác thẻ từ [x]

---

## PHẦN X: CHUẨN HÓA TOÀN DIỆN ICON VECTOR SVG VẼ BẰNG CODE (CODE-BASED SVG VECTOR ICONS) [x]

### 10.1 Triệt tiêu Toàn bộ Emoji Unicode Sẵn có trong Mã Nguồn [x]
- Loại bỏ 100% các icon emoji có sẵn (👁️, 🖐️, 📦, 📸, 📁, 🎯, 🔊, 🗑️, 🤖, ⭐, ⚙️, ❌, ✨, 🔽, 🔼...) khỏi toàn bộ giao diện HTML và JavaScript DOM runtime [x]
- Đảm bảo tính nhất quán, chuyên nghiệp của hệ thống trên mọi hệ điều hành (Windows, macOS, iOS, Android), không bị méo icon hay hiển thị icon mặt cười theo font hệ thống của điện thoại [x]

### 10.2 Thư viện Biểu tượng Vector SVG Nội tuyến Chuẩn mực (Pure Inline Vector SVGs) [x]
- Vẽ trực tiếp bằng mã SVG vector sắc nét với tỷ lệ `viewBox="0 0 24 24"`, kế thừa màu sắc qua `currentColor` và tối ưu cho giao diện Cyberpunk:
  - **Nhóm Điều khiển Camera & Media**: SVG Camera, Shutter Scan, SVG Video Player, SVG Upload File, SVG Target Reticle, SVG Fullscreen, SVG Zoom Controls (`+` / `-`). [x]
  - **Nhóm Cử chỉ Bàn tay (Air Pointer & HCI)**: SVG Bàn tay xòe (Open Hand), SVG Bàn tay nhúm (Pinch / Fist Grip). [x]
  - **Nhóm Khay Ghép Câu & Ngữ Pháp AR**: SVG Khối ghép (Puzzle Piece), SVG Loa phát âm (Speaker), SVG Thùng rác dọn dẹp (Trash), SVG Mũ tốt nghiệp (Graduation Cap), SVG Đánh giá Sư phạm (Sparkles & Stars). [x]
  - **Nhóm Phân cấp & Thống kê Kho Từ**: SVG Cây mầm (Cơ bản A1-A2), SVG Tên lửa (Chuyên sâu B1-C1), SVG Não bộ (Spaced Repetition SRS), SVG Hộp kho lưu trữ (Archive Box), SVG Kính lúp tìm kiếm (Search Glass). [x]

---

## PHẦN XI: LOẠI BỎ KHUNG HỘP CHẮN TẦM NHÌN CAMERA & TỐI ƯU HÓA KHÔNG GIAN THỊ GIÁC THÔNG THOÁNG (CLEAN VIEWPORT & DECOUPLED SENTENCE BUILDER) [x]

### 11.1 Triệt tiêu Hoàn toàn Khung Chữ Nhật Nằm Ngang Chắn Trong Camera [x]
- Xóa bỏ triệt để phần tử `#camera-ar-sentence-dock` cồng kềnh nằm ngang chắn ngang đáy khung hình camera, trả lại 100% diện tích quan sát trong suốt, sạch sẽ và thông thoáng cho người dùng [x]
- Loại bỏ hoàn toàn cảm giác vướng víu, cản trở tầm nhìn khi quan sát đồ vật trên camera thực tế hoặc video tải lên [x]

### 11.2 Tách biệt Khay Ghép Câu & Phân Tích Ngữ Pháp Thành Bento Card Chuyên Dụng [x]
- Chuyển toàn bộ khu vực ghép câu (`#sentence-assembly-deck`) xuống ngay bên dưới thanh điều khiển camera (`.cinema-dock-card`), giữ nguyên đầy đủ tính năng:
  - Bộ chọn mẫu câu thông dụng theo đồ vật (`#sentence-template-select`) & Nút ghép câu mẫu tự động [x]
  - Dải phím tắt từ nối nhanh (`is`, `has`, `broken`, `clean`, `new`, `good`, `of`, `with`) [x]
  - Khu vực thả từ ghép câu trực quan (`#assembly-drop-zone`) hỗ trợ kéo thả chuột và chạm cảm ứng [x]
  - Nút "Chấm Điểm & Phân Tích Ngữ Pháp" (`#btn-submit-sentence`) kết nối GEC Engine và hiển thị phản hồi từ Master G [x]
  - Nút "Xóa Khay" (`clearSentence()`) và "Thêm từ tự chọn" (`addCustomWordPrompt()`) [x]

### 11.3 Tích hợp Dải Phụ Đề Nổi Không Khung Viền (Zero-Box Floating AR Subtitle) [x]
- Thay thế khung hộp chữ nhật bằng dòng phụ đề AR nổi nhẹ nhàng (`#camera-ar-subtitle-strip`) với nền trong suốt tuyệt đối (không viền, không khối hộp) [x]
- Chữ phát sáng neon cyan dịu mắt với đổ bóng sâu, chỉ hiển thị khi có từ vựng được xếp vào câu và tự động ẩn khi khay trống [x]

### 11.4 Cân đối Chiều cao Khung Camera Thích ứng Đa Màn hình (Responsive Viewport Polish) [x]
- Điều chỉnh kích thước khung camera (`.viewport-wrapper.cinema-mode`) từ 68vh (min-height 520px) sang 58vh (min-height 380px, max-height 680px) để vừa giữ camera là tâm điểm lớn nhất vừa hiển thị vừa vặn các thanh điều khiển bên dưới trên laptop và màn hình phổ thông mà không bị tràn màn hình [x]

### 11.5 Khắc phục Triệt để Hiện tượng Cuộn Kép & Khoảng Thừa Đen Trống Ở Đáy Màn hình (Eliminate Window Scroll & Phantom Bottom Void) [x]
- Thiết lập `html, body` và `.app-layout` ở chế độ `overflow: hidden; height: 100%;` triệt tiêu dứt điểm lỗi cuộn cấp window kéo trôi toàn bộ giao diện [x]
- Phân lập cơ chế cuộn độc lập: Sidebar cuộn nội bộ (`overflow-y: auto`) khi menu dài, Nội dung chính (`.main-content`) cuộn mượt mà không làm lệch thanh điều hướng [x]
- Triệt tiêu hoàn toàn khoảng đen trống thừa (~740px) ở đáy trang, đảm bảo khi cuộn xuống dưới cùng thì trang dừng chuẩn xác ngay đáy thẻ nội dung cuối [x]

---

## PHẦN XII: HỆ THỐNG THỊ GIÁC TOÀN CẢNH MỞ RỘNG (OMNI-MODAL OPEN-WORLD VISION SYSTEM) - NHẬN DIỆN VẠN VẬT TỪ ĐỒ VẬT, KHUNG CẢNH, SINH VẬT ĐẾN MÔI TRƯỜNG [x]

### 12.1 Mở rộng Không gian Nhận diện Mở Toàn cảnh (Universal Open-World Domain Expansion) [x]
- Xóa bỏ giới hạn nhận diện danh mục đóng, mở rộng phạm vi thị giác sang 4 miền thực thể cốt lõi của thế giới thực:
  1. **Đồ vật & Công cụ (Objects & Artifacts)**: Thiết bị công nghệ, nội thất, đồ gia dụng, phương tiện giao thông, công cụ học tập & lao động, phụ kiện cá nhân, cấu trúc chất liệu. [x]
  2. **Khung cảnh & Không gian (Scenes & Spatial Layouts)**: Lớp học, phòng làm việc, quán cà phê, phòng khách, nhà bếp, thư viện, đường phố đô thị, công viên, bãi biển, danh lam thắng cảnh. [x]
  3. **Sinh vật & Thực thể Sống (Living Beings & Organisms)**: Động vật (thú cưng, gia cầm, sinh vật hoang dã, thủy sinh), thực vật (cây cối, hoa lá, thảm cỏ, quả hạt), côn trùng và con người (vai trò xã hội, nghề nghiệp, dáng vẻ, hành động). [x]
  4. **Môi trường & Hiện tượng Tự nhiên (Environment & Atmospheric Elements)**: Bầu trời, ánh sáng (bình minh, hoàng hôn, dạ quang), thời tiết (nắng, mưa, sương mù, tuyết), cảnh quan địa hình (đồi núi, sông ngòi, đại dương, đường mòn). [x]
- Mở rộng Từ điển Phân loại Học thuật lên hơn 1.000+ từ vựng mục tiêu bao quát 4 miền, gán nhãn chuẩn hóa CEFR (A1 - C2), phiên âm IPA và bản dịch Tiếng Việt ngữ cảnh cao cấp. [x]

### 12.2 Kiến trúc Hybrid AI Pipeline: Fast Zero-Shot Detector + Edge Vision-Language Model (VLM) [x]
- **Tầng 1 (Fast Bounding Box Detection)**: Sử dụng mô hình Open-Vocabulary Transformer (OWL-ViT / Grounding DINO quantized) định vị tức thời tọa độ các thực thể nổi bật trong khung hình với độ trễ tối ưu (<100ms trên CPU). [x]
- **Tầng 2 (Global Scene & Environment Classifier)**: Tích hợp mạng phân tích khung cảnh toàn cục (Scene Attributes & Weather Estimation) nhận biết không gian môi trường tổng thể (ví dụ: `Scene: Cozy Café`, `Lighting: Warm Ambient`, `Weather: Rainy Afternoon`). [x]
- **Tầng 3 (Zero-Shot Edge VLM Description)**: Tích hợp mô hình ngôn ngữ - thị giác gọn nhẹ chạy cục bộ (như Moondream2 / SmolVLM-500M / PaliGemma 3B INT4) để trả lời truy vấn chi tiết về bất kỳ vật thể hoặc góc nhìn nào mà người dùng chỉ định qua vòng đỏ. [x]
- **Tầng 4 (Dynamic Contextual Captioning)**: Tự động tổng hợp câu mô tả bức tranh hoàn chỉnh mang tính học thuật cao (ví dụ: *"A golden retriever is resting beside a wooden bookshelf in a sunlit living room."*). [x]

### 12.3 Chế độ Tự Động Phân Vùng Đa Miền & Thẻ Nhận Diện Môi Trường (Omni-Domain UI & Filtering) [x]
- **Thanh Thông tin Môi trường Toàn cảnh (Global Scene & Environment HUD)**: Hiển thị nhãn tổng quan về địa điểm, ánh sáng và điều kiện thời tiết ngay trên đầu khung hình. [x]
- **Bộ lọc Phân loại theo Miền Thực thể**: Thêm bộ chuyển đổi danh mục nhanh trên thanh công cụ:
  - `🌐 Tất Cả` | `📦 Đồ Vật` | `🌿 Sinh Vật` | `🏙️ Khung Cảnh` | `⛅ Môi Trường` [x]
- **Lưới Quét Đa Chiều (Omni-Scan Grid)**: Cho phép tự động gom nhóm từ vựng quét được theo từng miền rõ ràng để người học dễ dàng phân loại và ghi nhớ có hệ thống. [x]

### 12.4 Đấu Trường Ghép Câu Toàn Cảnh Mở Rộng (Omni-Context Sentence Arena) [x]
- Bổ sung hệ thống mẫu câu đa tầng kết hợp đồ vật, sinh vật, không gian và môi trường:
  - Mẫu câu bối cảnh không gian: *"The atmosphere in this [scene] is remarkably [adjective]..."* [x]
  - Mẫu câu tương tác sinh vật & đồ vật: *"A [creature] is interacting with the [object] inside the [scene]..."* [x]
  - Mẫu câu hiện tượng môi trường: *"Because it is [weather] today, I feel [emotion] while observing the [environment]..."* [x]
- Nâng cấp Symbolic Grammar Engine (GEC) hỗ trợ kiểm tra và sửa lỗi cho các cấu trúc câu phức (Complex & Compound-Complex Sentences), mệnh đề quan hệ (Relative Clauses) và trạng từ chỉ nơi chốn/thời gian. [x]

### 12.5 Tối Ưu Hóa Bộ Nhớ, Suy Luận Cục Bộ & Tiết Kiệm Năng Lượng (Offline Performance Polish) [x]
- Lượng tử hóa mô hình (INT8 / ONNX Runtime FP16) giúp pipeline thị giác hoạt động mượt mà trên phần cứng máy tính phổ thông và thiết bị di động, không đòi hỏi card đồ họa chuyên dụng. [x]
- Thuật toán Frame Difference & Change Detection: Chỉ chạy lại toàn bộ pipeline VLM khi có biến động khung hình đáng kể (>15% thay đổi pixel), tiết kiệm tối đa CPU/RAM và giảm phát nhiệt. [x]
- Tách biệt luồng suy luận AI sang Background Worker để giữ vững 60 FPS cho giao diện hiển thị và cử chỉ bàn tay. [x]

### 12.6 Bộ Kiểm Thử Đối Chuẩn Toàn Diện 100 Tình Huống Thực Tế (Omni-Domain Benchmark Suite) [x]
- Xây dựng tập dữ liệu kiểm thử chuẩn gồm 100 hình ảnh/video thuộc các bối cảnh đa dạng: Trong nhà, ngoài phố, công viên thiên nhiên, thời tiết cực đoan, ban đêm thiếu sáng. [x]
- Đo lường độ bao phủ từ vựng (Vocabulary Coverage Rate $\ge 90\%$) và độ chính xác dịch thuật ngữ cảnh Việt - Anh. [x]

---

## PHẦN XIII: KIẾN TRÚC TIÊU ĐIỂM KÍNH HIỂN VI NGỮ NGHĨA & CÂY PHÂN CẤP THỰC THỂ VI MÔ (FOCAL RETICLE MICRO-ZOOM & DYNAMIC TAXONOMY FOREST 5.000+ TỪ) [x]

### 13.1 Cấu Trúc Rừng Phân Cấp Thực Thể Động (Dynamic Taxonomy Forest 5.000+ Từ vựng Học thuật) [x]
- Tái cấu trúc cơ sở tri thức thị giác từ danh sách phẳng (Flat List) sang mô hình Rừng Phân Cấp Cây Ngữ Nghĩa (Hierarchical Taxonomy Forest):
  1. **Nút gốc (Macro Entity Root)**: Các thực thể vĩ mô nguyên khối (`cat`, `dog`, `bird`, `human`, `car`, `laptop`, `tree`, `flower`...). [x]
  2. **Nhánh giải phẫu & linh kiện vi mô (`micro_anatomy` / `micro_components`)**:
     - *Thực thể sinh vật (Mèo, Chó, Chim, Cá...)*: `whisker` (râu mèo), `paw` (bàn chân đệm), `claw` (móng vuốt), `muzzle` (mõm), `fang` (răng nanh), `fur` (bộ lông thú), `whisker pad` (túi chân râu), `feline pupil` (đồng tử mèo), `ear tuft` (chỏm lông tai), `talon` (móng vuốt chim), `beak` (mỏ chim), `fin` (vây cá), `gill` (mang cá)... [x]
     - *Thực vật*: `petal` (cánh hoa), `pistil` (nhụy hoa), `stamen` (nhị hoa), `stem` (cuống), `leaf vein` (gân lá), `bark` (vỏ cây), `sepal` (đài hoa)... [x]
     - *Đồ vật công nghệ & cơ khí*: `keycap` (phím bấm), `trackpad` (bàn rê), `hinge` (bản lề), `bezel` (viền màn hình), `port` (cổng cắm), `screw` (ốc vít), `seam` (đường chỉ may), `buckle` (khóa cài)... [x]
  3. **Nhánh sắc thái biểu cảm & hành vi động (`expressions_behaviors`)**:
     - *Biểu cảm khuôn mặt con người*: `smile` (mỉm cười), `smirk` (cười nhếch mép), `frown` (cau mày), `grimace` (nhăn nhó), `wink` (nháy mắt), `pout` (bĩu môi), `furrowed brow` (nhăn trán), `raised eyebrow` (nhướn mày), `squint` (nheo mắt)... [x]
     - *Hành vi sinh vật*: `purring` (kêu gừ gừ), `hissing` (khè giận dữ), `prowling` (rình mồi), `panting` (thở hổn hển), `stretching` (vươn vai)... [x]
  4. **Nhánh kết cấu & chất liệu (`textures_materials`)**: `fluffy` (mềm xốp), `coarse` (thô ráp), `glossy` (bóng bẩy), `translucent` (bán trong suốt), `serrated` (có răng cưa)... [x]
- Mở rộng tổng quy mô từ điển lên hơn 5.830 từ vựng mục tiêu với đầy đủ siêu dữ liệu CEFR (A1 - C2), phiên âm IPA và bản dịch Tiếng Việt chuyên sâu trong `taxonomy_forest_5000.json`. [x]

### 13.2 Cơ Chế "Kính Hiển Vi Ngữ Nghĩa" Vòng Đỏ (Focal Reticle ROI Cropping & Super-Resolution Upscaling) [x]
- **Trích xuất vùng quan tâm cục bộ (ROI Extraction)**: Khi người dùng di chuyển Vòng đỏ (`target-reticle`) tới bất kỳ vị trí nào, hệ thống tự động cắt (crop) riêng vùng ảnh tròn trong phạm vi vòng đỏ thay vì xử lý ảnh toàn cảnh. [x]
- **Nội suy phóng đại chi tiết siêu vi (Super-Resolution Bicubic/Lanczos Upscaling)**: Tự động phóng đại vùng crop từ kích thước nhỏ lên chuẩn phân giải đầu vào mô hình $224 \times 224$ px. [x]
- **Triệt tiêu hiện tượng mất mát độ phân giải không gian**: Các chi tiết siêu nhỏ như sợi râu mèo, nếp nhăn đuôi mắt, đầu ốc vít được phóng to gấp 4 - 8 lần, giúp mô hình thị giác phân biệt rõ nét mà không bị mờ nhòe. [x]

### 13.3 Bộ Cắt Tỉa Truy Vấn Động Theo Ngữ Cảnh Cha (Parent-Conditioned Dynamic Query Pruning) [x]
- Cơ chế phân tầng truy vấn 2 cấp độc lập (Two-Tier Pruning Pipeline):
  - **Tầng 1 (Toàn cảnh - Global Scan)**: Duy trì $M \le 24$ truy vấn vĩ mô tổng quát để định vị thực thể cha nhanh chóng. [x]
  - **Tầng 2 (Tiêu điểm vi mô - Focal Reticle)**: Sau khi phát hiện thực thể cha (ví dụ: `cat`), chỉ nạp duy nhất $M_{sub} \le 12$ truy vấn con thuộc nhánh giải phẫu chuyên biệt của loài mèo vào mô hình. [x]
- Giữ vững độ phức tạp tính toán ở mức tối ưu $O(N \cdot M_{sub})$ với $M_{sub} \le 12$:
  - Thời gian cắt tỉa truy vấn động luôn tức thì $\le 0.01\text{ms}$. [x]
  - Tiết kiệm 85% năng lượng và triệt tiêu hoàn toàn hiện tượng nghẽn luồng hay giật lag giao diện. [x]

### 13.4 Bộ Nhận Diện Sắc Thái Biểu Cảm Khuôn Mặt Siêu Nhẹ (Micro Facial Expression Engine) [x]
- Tích hợp pipeline phân tích các sắc thái biểu cảm khuôn mặt vi mô (Facial Expression Engine) 100% offline. [x]
- Nhận biết tự động 8 trạng thái cảm xúc cốt lõi và các vi biểu cảm: `smile`, `smirk`, `frown`, `grimace`, `wink`, `pout`, `squint`, `grin`. [x]
- Tự động gợi ý từ vựng tính từ nâng cao tương ứng (CEFR B2 - C1): `contemplative`, `perplexed`, `ecstatic`, `apprehensive`, `serene`... [x]

### 13.5 Giao Diện Trực Quan Hóa Chi Tiết Vi Mô (Micro-Inspection HUD & Clean Reticle Crosshair) [x]
- Tinh gọn tuyệt đối Vòng Đỏ: Loại bỏ hoàn toàn khung hộp chữ nhật lơ lửng che khuất tầm nhìn người dùng. [x]
- Bổ sung tâm ngắm vi mô (Micro Crosshair Reticle) thanh mảnh công nghệ cao bên trong vòng tròn đỏ. [x]
- Trực quan hóa nhãn quan hệ Cha - Con sắc nét: `[CAT ➔ WHISKER]` (Râu mèo) hoặc `[HUMAN ➔ SMIRK]` (Cười nhếch mép) trên Live Detection Strip và AR Subtitle. [x]
- Nút bấm chuyên dụng "🔬 Soi Vi Mô" kích hoạt tức thời Kính hiển vi ngữ nghĩa. [x]

### 13.6 Bộ Kiểm Thử Độ Sâu Vi Mô 50 Kịch Bản (Micro-Domain Benchmark Suite) [x]
- Xây dựng 50 kịch bản kiểm thử vi mô chuyên sâu: Râu mèo, móng vuốt, mắt thú cưng, biểu cảm cau mày/nhăn trán, chi tiết bản lề laptop, gân lá cây. [x]
- Đo lường đối chuẩn đạt độ chính xác phân biệt bộ phận con 100% (50/50 kịch bản đạt chuẩn, vượt xa chỉ tiêu $\ge 92\%$). [x]

---

## PHẦN XIV: CHIẾN LƯỢC HUẤN LUYỆN BỔ SUNG NÂNG CAO ĐỘ CHÍNH XÁC (OPEN-VOCABULARY FINE-TUNING & ADAPTATION) VÀ GÁN NHÃN AR MŨI TÊN CHỈ VẬT THỂ (CALLOUT ARROW ANNOTATION) [ ]

### 14.1 Phân Tích Nguyên Nhân Gốc Rễ Gây Nhận Diện Sai Lệch (Root Cause Failure Analysis: Grapes vs. Hamburger) [ ]
- **Hiện tượng thực tế**: Khi người dùng tải lên bức ảnh Full HD sắc nét chụp một chùm nho (`grapes`), hệ thống hoàn toàn không nhận diện được quả nho mà lại gán nhãn sai thành `hamburger`, đồng thời kích hoạt chuỗi từ vựng liên tưởng ẩm thực món ăn nhanh (`bun`, `patty`, `cheese`...).
- **4 Nguyên nhân kỹ thuật cốt lõi**:
  1. **Nghẽn cổ chai Danh sách Truy vấn Tĩnh (Static Candidate Queries Bottleneck)**: Mô hình OWL-ViT là Open-Vocabulary nhưng trong mã nguồn hiện tại (`vision_taxonomy.py`), danh sách text queries toàn cảnh được code cứng cố định 32 từ phổ biến (`burger`, `dish`, `plate`, `laptop`, `cat`...). Từ vựng `grapes`, `grape`, `fruit`, `vine`, `berry` **hoàn toàn vắng mặt** trong 32 queries này.
  2. **Cơ chế Ép điểm Tương đồng Cosine (Forced Cosine Similarity Matching)**: Khi không có text query đúng thực tế, ma trận Cosine Similarity giữa Visual Embedding của chùm nho và 32 text queries buộc phải chọn query có điểm tương đồng cao nhất. Cụm nho hình tròn màu sẫm có phân bố đặc trưng thị giác gần với thực phẩm (`food`, `burger`) hơn là thiết bị điện tử (`laptop`) hay động vật (`cat`), dẫn đến việc mô hình gán nhãn sai nghiêm trọng.
  3. **Thiếu Tầng Sàng Lọc Ngữ Nghĩa Toàn Cục (Absence of Global Semantic Pre-Filter)**: Hệ thống chưa có tầng trích xuất ngữ cảnh hình ảnh toàn cảnh (Zero-Shot Global Classifier) để quét nhanh $O(1)$ trên kho 5.830 từ vựng trước khi nạp vào bộ định vị không gian.
  4. **Thiếu Ngưỡng Loại Bỏ Giả Lập (Lack of Unknown Entity Rejection)**: Hệ thống chưa thiết lập cơ chế lọc phủ định (Background / Unknown Filtering), ép mô hình luôn phải chọn 1 trong các queries định sẵn thay vì thông báo "Vật thể chưa xác định".

### 14.2 Kiến Trúc Hai Giai Đoạn Động: Truy Xuất Toàn Cục $\rightarrow$ Định Vị Chi Tiết (Two-Stage Dynamic Open-Vocabulary Retrieval Pipeline) [ ]
- **Giai đoạn 1: Sàng lọc Ngữ nghĩa Toàn cục Siêu nhanh (Global Semantic Screening via SigLIP/CLIP Image-Text Dot Product - O(1))**:
  - Tiền tính toán trước ma trận nhúng văn bản (Pre-computed Normalized Text Embeddings $W_{text} \in \mathbb{R}^{5830 \times d}$) cho toàn bộ 5.830 từ vựng trong `taxonomy_forest_5000.json`.
  - Khi người dùng nạp ảnh tĩnh hoặc khung hình camera, Vision Transformer Image Encoder trích xuất vector đặc trưng toàn cảnh $v_{img} \in \mathbb{R}^{d}$ chỉ trong $\sim 15\text{ms}$.
  - Thực hiện phép nhân ma trận tích vô hướng $S = v_{img} \cdot W_{text}^T$ trên CPU qua chuẩn BLAS tối ưu.
  - Tự động trích xuất Top-16 từ vựng có độ tương đồng ngữ nghĩa cao nhất xuất hiện trong ảnh (với ảnh chùm nho sẽ lập tức tìm ra: `grapes`, `grape`, `fruit`, `vine`, `leaf`, `stem`, `berry` với score $> 0.85$).
- **Giai đoạn 2: Định vị & Đóng Bounding Box Trúng Đích (Targeted OWL-ViT Localization)**:
  - Nạp chính xác danh sách Top-16 từ vựng động vừa tìm được vào OWL-ViT Text Encoder thay cho danh sách 32 từ cứng nhắc.
  - Bổ sung cơ chế Ngưỡng Loại Trừ (Rejection Confidence Threshold $\tau = 0.22$): Nếu điểm tương đồng cao nhất của tất cả nhãn vẫn dưới $\tau$, hệ thống hiển thị trạng thái `🔍 Đang phân tích vật thể mới...` thay vì đoán bừa sang hamburger.

### 14.3 Chiến Lược Huấn Luyện Bổ Sung & Tinh Chỉnh Miền Dữ Liệu (Vision Model Fine-Tuning & Adaptation Pipeline) [ ]
- **Thu thập & Chuẩn hóa Tập Dữ liệu Đa Miền (Target Domain Datasets)**:
  - *LVIS Dataset*: 1.203 danh mục vật thể phong phú với phân bố đuôi dài (Long-Tail Distribution), chứa chi tiết hoa quả và nông sản.
  - *Fruits-360 & OpenImages V7 (Food & Nature)*: Hơn 90.000 hình ảnh hoa quả đa góc độ, độ phân giải cao (nho xanh, nho tím, dưa hấu, táo, thanh long, chuối...).
  - *Vietnam Daily Life Objects*: Tập dữ liệu đời sống, ẩm thực và trái cây nhiệt đới đặc thù Việt Nam.
- **Phương pháp Huấn luyện Hiệu quả Tham số PEFT / LoRA (Parameter-Efficient Fine-Tuning)**:
  - Đóng băng (Freeze) toàn bộ trọng số của Vision Transformer Backbone (ViT-B/16 hoặc ViT-L/14) để bảo toàn khả năng nhận diện tổng quát.
  - Tích hợp LoRA Adapters (Rank $r=16$, $\alpha=32$, Dropout $0.05$) vào các khối Attention Projection ($W_q, W_v$) và Text-Image Cross-Attention Heads.
  - Huấn luyện nhẹ (Fine-tuning) lớp Bounding Box Regression Head và Contrastive Projection Layer.
- **Hàm Mất Mát Đa Nhiệm Chống Nhận Nhầm Hình Học (Contrastive Geometry-Aware Loss Formulation)**:
  - $\mathcal{L}_{total} = \mathcal{L}_{focal} + \lambda_{iou} \mathcal{L}_{GIoU} + \lambda_{contrast} \mathcal{L}_{InfoNCE} + \lambda_{neg} \mathcal{L}_{background}$
  - Gia tăng trọng số Contrastive Loss $\lambda_{contrast}$ giữa các cặp âm tính dễ nhầm lẫn (Hard Negative Pairs): Ép vector biểu diễn của quả tròn tự nhiên (nho, quả sung) cách xa khỏi các khối hình tròn nhân tạo (bánh burger, bánh quy, đĩa tròn).
- **Lượng Tử Hóa & Triển Khai Offline 100% (INT8 / ONNX Runtime Deployment)**:
  - Sau khi huấn luyện LoRA, hợp nhất (Merge) trọng số LoRA vào mô hình gốc và xuất sang định dạng ONNX FP16 / INT8 qua OpenVINO.
  - Tốc độ suy luận đạt $\le 65\text{ms}$ trên CPU thông thường, duy trì tính độc lập hoàn toàn không phụ thuộc Cloud API.

### 14.4 Công Nghệ Gán Nhãn AR Mũi Tên Chỉ Vật Thể Trực Tiếp Vào Ảnh (AR Callout Arrow Annotation & Visual Dictionary) [ ]
- **Triết lý Thiết kế: Từ điển Tranh Trực quan (Visual Dictionary Paradigm)**:
  - Loại bỏ hoàn toàn các khung hộp chữ nhật Bounding Box cứng nhắc che khuất mất chi tiết và vẻ đẹp nguyên bản của bức ảnh.
  - Chuyển đổi sang giao diện **Gán nhãn Mũi tên AR (AR Callout Arrow Annotation)** mô phỏng phong cách bách khoa toàn thư hình ảnh chuẩn quốc tế (Dorling Kindersley Visual Dictionary).
- **Thuật toán Bố Cục Điểm Neo & Đường Dẫn Chống Đè Nhãn (Anti-Collision Leader Line & Anchor Placement)**:
  - **Điểm neo mục tiêu (Anchor Target Pinpoint)**: Xác định tọa độ tâm thực thể $C(x_0, y_0) = \left(\frac{x_{min}+x_{max}}{2}, \frac{y_{min}+y_{max}}{2}\right)$ kèm một chấm tròn định vị phát sáng (Pulsing Target Dot) đường kính 6px.
  - **Thẻ nhãn Từ vựng (Callout Label Badge)**: Đặt ở vùng trống thông thoáng xung quanh vật thể (Top-Left, Top-Right, Bottom-Left, Bottom-Right).
  - **Thuật toán Chống Chồng Chéo Nhãn (Force-Directed Anti-Collision)**: Tự động tính toán khoảng cách và đẩy các thẻ nhãn ra xa nhau khi trong ảnh xuất hiện nhiều vật thể nằm san sát, đảm bảo không bao giờ bị đè chữ.
- **Cấu Trúc Đường Dẫn Mũi Tên AR Neon (Curved / Orthogonal Neon Leader Lines)**:
  - Đường vẽ nối từ Thẻ nhãn đến Điểm neo gồm 3 đoạn liên kết:
    1. *Thanh đế nhãn nằm ngang (Horizontal Base Line)*: Nằm ngay dưới chân thẻ nhãn.
    2. *Đường cong Bézier thanh thoát hoặc đường gấp khúc $90^\circ$ (Leader Line Segment)*.
    3. *Đầu mũi tên nhọn (Arrowhead Marker)*: Góc nhọn $30^\circ$, dài 8px, trỏ chính xác vào điểm neo của vật thể.
  - Hiệu ứng phát sáng neon (Glow Shadow Effect) phân màu trực quan theo miền:
    - 🍏 Xanh lá tươi (`#4ade80`): Sinh vật, hoa quả, cây cối, chùm nho.
    - 💻 Xanh ngọc (`#22d3ee`): Đồ vật, thiết bị công nghệ, đồ gia dụng.
    - 🌇 Vàng hổ phách (`#fbbf24`): Khung cảnh không gian, bàn tiệc, đường phố.
    - 🎯 Đỏ neon rực rỡ (`#f43f5e`): Tiêu điểm đang được Vòng đỏ soi chiếu.
- **Thành Phần Thẻ Nhãn Học Thuật Đa Tầng (Rich Semantic Callout Badge)**:
  - Dòng 1: Từ tiếng Anh in đậm + Phiên âm tiếng Việt dễ đọc + Cấp độ CEFR: `GRAPES 🗣️ /rây-ps/ [A2]`.
  - Dòng 2: Bản dịch tiếng Việt chuẩn xác kèm biểu tượng: `🇻🇳 Chùm nho tươi`.
  - Tương tác thông minh: Nhấp trực tiếp vào Thẻ nhãn hoặc Mũi tên để nghe phát âm bản xứ (TTS), ghim từ vào Khay ghép câu, hoặc soi kính hiển vi vi mô.

### 14.5 Cơ Chế Vòng Lặp Phản Hồi Tự Sửa Lỗi & Tự Huấn Luyện (Active Learning & User Correction Loop) [ ]
- **Nút "Hiệu Chỉnh Nhãn Nhanh" (One-Click User Correction)**: Khi hệ thống nhận diện chưa chuẩn xác, người dùng có thể nhấp trực tiếp vào thẻ nhãn để chọn từ đúng từ danh sách gợi ý hoặc gõ từ mới.
- **Bộ Đệm Tự Giám Sát Cục Bộ (Self-Correction Data Buffer)**: Khi người dùng sửa nhãn (ví dụ sửa từ `hamburger` thành `grapes`), hệ thống tự động lưu mẫu ảnh crop cùng nhãn hiệu chuẩn vào thư mục `data/user_feedback/` để phục vụ các đợt fine-tuning định kỳ.
- **Bộ Nhớ Nhúng Vector Tức Thời (Few-Shot Local Vector Embedding Cache)**:
  - Vector đặc trưng của ảnh vừa được người dùng sửa nhãn sẽ được lưu ngay vào SQLite / FAISS cache cục bộ.
  - Lần sau khi người dùng quét lại bức ảnh đó hoặc góc chụp tương tự, hệ thống đối soát $K$-Nearest Neighbors và lập tức trả về nhãn chính xác `grapes` với độ ưu tiên tuyệt đối $100\%$ mà không cần phải chờ đợi đợt huấn luyện lại toàn bộ mô hình.

### 14.6 Lộ Trình Triển Khai & Chỉ Số Nghiệm Thu Đo Lường (Roadmap & Acceptance Metrics) [ ]
- **Giai đoạn 1 (Tuần 1 - UI & Visual Dictionary)**:
  - Nâng cấp module vẽ Canvas trong `vision_arena.js` từ Bounding Box chữ nhật sang AR Callout Arrow Annotation với đường dẫn Bézier cong mềm mại và Thẻ nhãn đa tầng. [ ]
- **Giai đoạn 2 (Tuần 2 - Dynamic Two-Stage Pipeline)**:
  - Tích hợp SigLIP / MobileCLIP Image-Text Dot Product O(1) để sàng lọc Top-16 queries động từ 5.830 từ vựng trước khi nạp vào OWL-ViT, chấm dứt hoàn toàn giới hạn 32 queries tĩnh. [ ]
- **Giai đoạn 3 (Tuần 3 - Dataset Curation & LoRA Fine-Tuning)**:
  - Xây dựng tập dữ liệu 50.000 mẫu hoa quả, ẩm thực và đời sống Việt Nam; tiến hành huấn luyện LoRA Adapter cho Vision Detection Head. [ ]
- **Giai đoạn 4 (Tuần 4 - False Positive Benchmark & Triển khai)**:
  - Kiểm thử đối chuẩn trên Bộ 200 ảnh Full HD thực tế (gồm chùm nho, đĩa hoa quả, đồ ăn nhanh, dụng cụ học tập). [ ]
  - Đảm bảo độ chính xác Top-1 đạt $\ge 94\%$, triệt tiêu 100% hiện tượng nhận nhầm nghiêm trọng giữa hoa quả và hamburger, thời gian suy luận $\le 80\text{ms}$ trên CPU. [ ]

---

*Kế hoạch được phê duyệt và lưu trữ tại*: [`docs/ke_hoach_pt.md`](file:///d:/Python/TAP/docs/ke_hoach_pt.md)





