/**
 * VISION ARENA & AIR GESTURE INTERACTION ENGINE (TAP 2026)
 * Tích hợp MediaPipe Hands Client-Side + Local OWL-ViT Backend API
 */

let videoElement = null;
let canvasElement = null;
let canvasCtx = null;
let cameraStream = null;
let mediapipeHands = null;

let isCameraActive = false;
let isScanning = false;
let currentDetectedParts = [];
let primaryObject = "object";

// Quản lý trạng thái cử chỉ
let handPosition = { x: 0, y: 0 };
let smoothedHand = { x: 0, y: 0 };
let currentGesture = "NONE"; // NONE, OPEN, PINCH, FIST
let grabbedElement = null;

// Thống kê hiệu năng
let lastFrameTime = performance.now();
let frameCount = 0;
let currentFPS = 0;

document.addEventListener("DOMContentLoaded", () => {
    videoElement = document.getElementById("webcam-video");
    canvasElement = document.getElementById("vision-canvas");
    if (canvasElement) {
        canvasCtx = canvasElement.getContext("2d");
    }

    // Khởi tạo kích thước canvas đồng bộ
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    // Khởi tạo MediaPipe Hands nếu có sẵn
    initMediaPipeHands();
});

function resizeCanvas() {
    if (!canvasElement || !canvasElement.parentElement) return;
    const rect = canvasElement.parentElement.getBoundingClientRect();
    canvasElement.width = rect.width;
    canvasElement.height = rect.height;
}

/**
 * 1. KHỞI TẠO VÀ ĐIỀU KHIỂN CAMERA WEBRTC
 */
async function toggleCamera() {
    if (isCameraActive) {
        stopCamera();
    } else {
        await startCamera();
    }
}

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            },
            audio: false
        });

        cameraStream = stream;
        videoElement.srcObject = stream;
        await videoElement.play();

        isCameraActive = true;
        document.getElementById("btn-toggle-camera").classList.add("cyber-btn-pink");
        document.getElementById("cam-icon").innerText = "⏹️";
        document.getElementById("cam-text").innerText = "Dừng Camera";
        document.getElementById("btn-scan-frame").disabled = false;
        document.getElementById("status-hud").innerHTML = "🟢 Camera: Đang chạy";

        resizeCanvas();
        requestAnimationFrame(renderLoop);

    } catch (err) {
        console.error("Lỗi truy cập Camera:", err);
        alert("Không thể truy cập Camera. Vui lòng cấp quyền truy cập Camera trong trình duyệt!");
        document.getElementById("status-hud").innerHTML = "❌ Camera: Bị chặn";
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    if (videoElement) {
        videoElement.srcObject = null;
    }

    isCameraActive = false;
    document.getElementById("btn-toggle-camera").classList.remove("cyber-btn-pink");
    document.getElementById("cam-icon").innerText = "📹";
    document.getElementById("cam-text").innerText = "Bật Camera";
    document.getElementById("btn-scan-frame").disabled = true;
    document.getElementById("status-hud").innerHTML = "🔴 Camera: Đang tắt";
    document.getElementById("gesture-text").innerText = "Camera đã tắt";

    if (canvasCtx && canvasElement) {
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }
}

/**
 * 2. TÍCH HỢP MEDIAPIPE HANDS & NHẬN DIỆN CỬ CHỈ (60 FPS CLIENT-SIDE)
 */
function initMediaPipeHands() {
    if (typeof Hands === "undefined") {
        console.warn("MediaPipe Hands chưa nạp xong từ CDN. Đang thử lại...");
        setTimeout(initMediaPipeHands, 1000);
        return;
    }

    try {
        mediapipeHands = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        mediapipeHands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        mediapipeHands.onResults(onHandResults);
        console.log("[x] MediaPipe Hands khởi tạo thành công!");
    } catch (e) {
        console.error("Lỗi khởi tạo MediaPipe Hands:", e);
    }
}

function onHandResults(results) {
    if (!canvasCtx || !canvasElement) return;

    // Tính toán FPS
    frameCount++;
    const now = performance.now();
    if (now - lastFrameTime >= 1000) {
        currentFPS = Math.round((frameCount * 1000) / (now - lastFrameTime));
        document.getElementById("fps-hud").innerText = `⚡ FPS: ${currentFPS}`;
        frameCount = 0;
        lastFrameTime = now;
    }

    // Xóa frame cũ
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    // Vẽ lại các bounding boxes từ lần quét trước (nếu có)
    drawDetectedBoundingBoxes();

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];

        // Lấy tọa độ bàn tay: Ngón trỏ tip (8), ngón cái tip (4), tâm lòng bàn tay (9)
        // Vì video bị lật gương (scaleX(-1)), tọa độ x cần lật: 1.0 - x
        const rawX = (1.0 - landmarks[9].x) * canvasElement.width;
        const rawY = landmarks[9].y * canvasElement.height;

        // Bộ lọc EMA làm mịn chống rung tay (Alpha = 0.35)
        const alpha = 0.35;
        smoothedHand.x = alpha * rawX + (1 - alpha) * smoothedHand.x;
        smoothedHand.y = alpha * rawY + (1 - alpha) * smoothedHand.y;
        handPosition = { x: smoothedHand.x, y: smoothedHand.y };

        // Vẽ khung xương bàn tay Cyberpunk Neon
        drawHandSkeleton(landmarks);

        // Phân loại cử chỉ: Kẹp ngón tay (Pinch) vs Nắm tay (Fist) vs Mở tay (Open)
        classifyGesture(landmarks);

        // Xử lý tương tác gắp/thả thẻ chữ bằng không gian
        handleSpatialDragAndDrop();

    } else {
        currentGesture = "NONE";
        document.getElementById("gesture-emoji").innerText = "🖐️";
        document.getElementById("gesture-text").innerText = "Chưa thấy bàn tay";

        // Thả thẻ nếu đang giữ mà mất dấu tay
        if (grabbedElement) {
            releaseGrabbedElement(false);
        }
    }
}

function classifyGesture(landmarks) {
    // 1. Khoảng cách Euclidean giữa ngón cái tip (4) và ngón trỏ tip (8)
    const dx = landmarks[4].x - landmarks[8].x;
    const dy = landmarks[4].y - landmarks[8].y;
    const pinchDist = Math.sqrt(dx * dx + dy * dy);

    // 2. Khoảng cách từ các đầu ngón tay (8, 12, 16, 20) về cổ tay (0)
    const wrist = landmarks[0];
    const fingerTips = [8, 12, 16, 20];
    let avgDistToWrist = 0;
    fingerTips.forEach(idx => {
        const fdx = landmarks[idx].x - wrist.x;
        const fdy = landmarks[idx].y - wrist.y;
        avgDistToWrist += Math.sqrt(fdx * fdx + fdy * fdy);
    });
    avgDistToWrist /= 4;

    // Phân loại cử chỉ
    if (pinchDist < 0.075) {
        currentGesture = "PINCH";
        document.getElementById("gesture-emoji").innerText = "👌";
        document.getElementById("gesture-text").innerText = "Kẹp ngón tay (Pinch)";
    } else if (avgDistToWrist < 0.25) {
        currentGesture = "FIST";
        document.getElementById("gesture-emoji").innerText = "✊";
        document.getElementById("gesture-text").innerText = "Nắm tay (Grab)";
    } else {
        currentGesture = "OPEN";
        document.getElementById("gesture-emoji").innerText = "🖐️";
        document.getElementById("gesture-text").innerText = "Bàn tay mở (Open)";
    }
}

function drawHandSkeleton(landmarks) {
    const w = canvasElement.width;
    const h = canvasElement.height;

    // Các cặp nối xương bàn tay chuẩn MediaPipe
    const connections = [
        [0, 1], [1, 2], [2, 3], [3, 4],       // Ngón cái
        [0, 5], [5, 6], [6, 7], [7, 8],       // Ngón trỏ
        [5, 9], [9, 10], [10, 11], [11, 12],  // Ngón giữa
        [9, 13], [13, 14], [14, 15], [15, 16],// Ngón áp út
        [13, 17], [17, 18], [18, 19], [19, 20],// Ngón út
        [0, 17]                               // Cổ tay
    ];

    canvasCtx.save();
    canvasCtx.lineWidth = 2.5;
    canvasCtx.strokeStyle = (currentGesture === "PINCH" || currentGesture === "FIST") ? "#f43f5e" : "#22d3ee";
    canvasCtx.shadowBlur = 10;
    canvasCtx.shadowColor = canvasCtx.strokeStyle;

    connections.forEach(([i, j]) => {
        const x1 = (1.0 - landmarks[i].x) * w;
        const y1 = landmarks[i].y * h;
        const x2 = (1.0 - landmarks[j].x) * w;
        const y2 = landmarks[j].y * h;

        canvasCtx.beginPath();
        canvasCtx.moveTo(x1, y1);
        canvasCtx.lineTo(x2, y2);
        canvasCtx.stroke();
    });

    // Vẽ các khớp nối (Joints)
    landmarks.forEach((pt, idx) => {
        const x = (1.0 - pt.x) * w;
        const y = pt.y * h;
        canvasCtx.beginPath();
        canvasCtx.arc(x, y, (idx === 4 || idx === 8) ? 6 : 3.5, 0, 2 * Math.PI);
        canvasCtx.fillStyle = (idx === 4 || idx === 8) ? "#fbbf24" : "#ffffff";
        canvasCtx.fill();
    });

    // Vẽ vầng sáng (Aura cursor) tại vị trí gắp của ngón trỏ & cái
    const grabX = (1.0 - (landmarks[4].x + landmarks[8].x) / 2) * w;
    const grabY = ((landmarks[4].y + landmarks[8].y) / 2) * h;

    canvasCtx.beginPath();
    canvasCtx.arc(grabX, grabY, (currentGesture === "PINCH" || currentGesture === "FIST") ? 18 : 8, 0, 2 * Math.PI);
    canvasCtx.fillStyle = (currentGesture === "PINCH" || currentGesture === "FIST") ? "rgba(244, 63, 94, 0.4)" : "rgba(34, 211, 238, 0.3)";
    canvasCtx.fill();
    canvasCtx.stroke();

    canvasCtx.restore();
}

/**
 * 3. LOGIC KÉO - THẢ BẰNG CỬ CHỈ BÀN TAY (AIR GESTURE DRAG & DROP)
 */
function handleSpatialDragAndDrop() {
    const isGrabbing = (currentGesture === "PINCH" || currentGesture === "FIST");

    if (isGrabbing) {
        if (!grabbedElement) {
            // Kiểm tra va chạm tọa độ bàn tay với các thẻ chữ trong Kho hoặc Khay
            // Chuyển đổi tọa độ canvas sang tọa độ viewport màn hình
            const canvasRect = canvasElement.getBoundingClientRect();
            const screenX = canvasRect.left + handPosition.x;
            const screenY = canvasRect.top + handPosition.y;

            const allTokens = document.querySelectorAll(".word-token");
            for (let token of allTokens) {
                const rect = token.getBoundingClientRect();
                // Nới rộng vùng tương tác chạm (Hitbox expansion: 25px)
                if (screenX >= rect.left - 25 && screenX <= rect.right + 25 &&
                    screenY >= rect.top - 25 && screenY <= rect.bottom + 25) {
                    
                    grabbedElement = token;
                    grabbedElement.classList.add("is-grabbed");
                    playHapticSound("grab");
                    break;
                }
            }
        } else {
            // Đang giữ thẻ chữ -> Di chuyển thẻ theo tay
            // Hiển thị hiệu ứng kéo trực quan
            const canvasRect = canvasElement.getBoundingClientRect();
            const screenX = canvasRect.left + handPosition.x;
            const screenY = canvasRect.top + handPosition.y;

            grabbedElement.style.position = "fixed";
            grabbedElement.style.left = `${screenX - 40}px`;
            grabbedElement.style.top = `${screenY - 20}px`;
            grabbedElement.style.zIndex = "9999";
        }
    } else {
        // Cử chỉ là OPEN hoặc thả tay
        if (grabbedElement) {
            releaseGrabbedElement(true);
        }
    }
}

function releaseGrabbedElement(checkDropZone = true) {
    if (!grabbedElement) return;

    grabbedElement.classList.remove("is-grabbed");
    grabbedElement.style.position = "";
    grabbedElement.style.left = "";
    grabbedElement.style.top = "";
    grabbedElement.style.zIndex = "";

    if (checkDropZone) {
        const dropZone = document.getElementById("assembly-drop-zone");
        const dropRect = dropZone.getBoundingClientRect();

        const canvasRect = canvasElement.getBoundingClientRect();
        const screenX = canvasRect.left + handPosition.x;
        const screenY = canvasRect.top + handPosition.y;

        // Nếu vị trí thả tay nằm trong Khay Ghép Câu -> Hút thẻ vào khay
        if (screenX >= dropRect.left && screenX <= dropRect.right &&
            screenY >= dropRect.top && screenY <= dropRect.bottom) {
            
            dropZone.appendChild(grabbedElement);
            playHapticSound("drop");
            updateSentenceSubmitButton();
        }
    }

    grabbedElement = null;
}

function renderLoop() {
    if (!isCameraActive || !videoElement) return;

    if (videoElement.readyState >= 2 && mediapipeHands) {
        mediapipeHands.send({ image: videoElement }).catch(err => {
            console.error("Lỗi gửi frame tới MediaPipe:", err);
        });
    }

    requestAnimationFrame(renderLoop);
}

/**
 * 4. QUÉT VẬT THỂ & TRÍCH XUẤT BỘ PHẬN CON (OWL-ViT BACKEND)
 */
async function captureAndScan() {
    if (!isCameraActive || !videoElement) {
        alert("Vui lòng bật camera trước khi quét!");
        return;
    }

    const scanBtn = document.getElementById("btn-scan-frame");
    const laser = document.getElementById("scan-laser");
    scanBtn.disabled = true;
    laser.style.display = "block";
    document.getElementById("status-hud").innerHTML = "🔍 Đang phân tích OWL-ViT...";

    try {
        // 1. Chụp 1 frame tĩnh từ thẻ Video
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = videoElement.videoWidth || 1280;
        tempCanvas.height = videoElement.videoHeight || 720;
        const ctx = tempCanvas.getContext("2d");
        ctx.drawImage(videoElement, 0, 0, tempCanvas.width, tempCanvas.height);
        const base64Image = tempCanvas.toDataURL("image/jpeg", 0.85);

        // 2. Gửi tới API Local Backend
        const category = document.getElementById("category-select").value || null;
        const threshold = parseFloat(document.getElementById("threshold-slider").value) || 0.14;

        const startTime = performance.now();
        const response = await fetch("/api/vision/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: base64Image,
                target_category: category,
                threshold: threshold
            })
        });

        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        document.getElementById("latency-hud").innerText = `⏱️ Suy luận: ${latency} ms`;

        if (data.status === "success") {
            currentDetectedParts = data.detected_parts || [];
            primaryObject = data.primary_object || "object";

            // Hiển thị từ vựng ra Kho từ vựng
            renderWordPool(currentDetectedParts);
            document.getElementById("status-hud").innerHTML = `✅ Phát hiện: <b>${primaryObject}</b> (${currentDetectedParts.length} chi tiết)`;
        } else {
            alert(`Lỗi nhận diện: ${data.message}`);
            document.getElementById("status-hud").innerHTML = "⚠️ Nhận diện thất bại";
        }

    } catch (e) {
        console.error("Lỗi khi quét ảnh:", e);
        alert("Lỗi kết nối tới Server Vision!");
        document.getElementById("status-hud").innerHTML = "❌ Lỗi Server";
    } finally {
        laser.style.display = "none";
        scanBtn.disabled = false;
    }
}

/**
 * 5. VẼ BOUNDING BOX TRÊN CANVAS
 */
function drawDetectedBoundingBoxes() {
    if (!currentDetectedParts || currentDetectedParts.length === 0 || !canvasCtx) return;

    const w = canvasElement.width;
    const h = canvasElement.height;

    currentDetectedParts.forEach((part, index) => {
        const box = part.normalized_box;
        if (!box) return;

        // Vì video bị lật gương (scaleX(-1)), tọa độ xmin và xmax cần lật:
        const x1 = (1.0 - box.xmax) * w;
        const y1 = box.ymin * h;
        const boxW = (box.xmax - box.xmin) * w;
        const boxH = (box.ymax - box.ymin) * h;

        canvasCtx.save();
        // Viền Bounding Box Cyberpunk
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = "#22d3ee";
        canvasCtx.fillStyle = "rgba(6, 182, 212, 0.12)";
        canvasCtx.shadowBlur = 8;
        canvasCtx.shadowColor = "#22d3ee";

        canvasCtx.fillRect(x1, y1, boxW, boxH);
        canvasCtx.strokeRect(x1, y1, boxW, boxH);

        // Nhãn Bounding Box
        const labelText = `${part.word.toUpperCase()} [${part.cefr}] (${Math.round(part.confidence * 100)}%)`;
        canvasCtx.font = "bold 12px Inter, sans-serif";
        const textW = canvasCtx.measureText(labelText).width;

        canvasCtx.fillStyle = "rgba(2, 6, 23, 0.85)";
        canvasCtx.fillRect(x1, y1 - 22, textW + 12, 20);

        canvasCtx.fillStyle = "#67e8f9";
        canvasCtx.fillText(labelText, x1 + 6, y1 - 7);

        canvasCtx.restore();
    });
}

/**
 * 6. HIỂN THỊ KHO TỪ VỰNG NỔI & HỖ TRỢ CHUỘT KÉO THẢ (DUAL-FALLBACK)
 */
function renderWordPool(parts) {
    const pool = document.getElementById("word-pool");
    const countBadge = document.getElementById("word-count-badge");
    pool.innerHTML = "";

    if (!parts || parts.length === 0) {
        pool.innerHTML = `<div style="color: #64748b; font-style: italic; font-size: 13px; margin: auto;">Không tìm thấy chi tiết bộ phận nào. Hãy thử đổi góc chụp hoặc giảm ngưỡng tin cậy!</div>`;
        countBadge.innerText = "0 từ vựng";
        return;
    }

    countBadge.innerText = `${parts.length} từ vựng`;

    parts.forEach(part => {
        const token = createWordTokenElement(part.word, part.ipa, part.cefr, part.meaning, part.is_learned);
        pool.appendChild(token);
    });

    // Thêm các từ nối cơ bản để người dùng dễ ghép câu hoàn chỉnh
    ["the", "is", "has", "a", "my"].forEach(auxWord => {
        const auxToken = createWordTokenElement(auxWord, "", "A1", "Từ nối", true);
        pool.appendChild(auxToken);
    });
}

function createWordTokenElement(word, ipa, cefr, meaning, isLearned) {
    const token = document.createElement("div");
    token.className = "word-token";
    token.setAttribute("draggable", "true");
    token.setAttribute("data-word", word);

    token.innerHTML = `
        <span class="cefr-badge">${cefr || 'A1'}</span>
        <span style="font-weight: 700; color: #fff;">${word}</span>
        ${ipa ? `<span class="word-ipa">${ipa}</span>` : ''}
        <button type="button" style="background: none; border: none; cursor: pointer; color: #38bdf8; padding: 0 4px;" onclick="speakWord('${word}', event)" title="Nghe phát âm">🔊</button>
        ${!isLearned ? `<button type="button" class="btn-add-vocab" onclick="collectVocab('${word}', event)" title="Lưu vào kho ôn tập SRS">+ Thu thập</button>` : ''}
    `;

    // Gắn sự kiện chuột kéo thả HTML5 thông thường
    token.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", word);
        e.dataTransfer.setData("element-id", token.id || word);
        token.classList.add("is-grabbed");
    });

    token.addEventListener("dragend", () => {
        token.classList.remove("is-grabbed");
    });

    return token;
}

// Xử lý kéo thả bằng chuột trên Drop Zone
function handleDragOver(e) {
    e.preventDefault();
    document.getElementById("assembly-drop-zone").classList.add("drag-over");
}

function handleDragLeave(e) {
    document.getElementById("assembly-drop-zone").classList.remove("drag-over");
}

function handleDrop(e) {
    e.preventDefault();
    const dropZone = document.getElementById("assembly-drop-zone");
    dropZone.classList.remove("drag-over");

    const word = e.dataTransfer.getData("text/plain");
    if (!word) return;

    // Tìm token nguồn trong pool hoặc tạo mới
    const token = document.querySelector(`.word-token[data-word="${word}"]`);
    if (token) {
        dropZone.appendChild(token);
        playHapticSound("drop");
        updateSentenceSubmitButton();
    }
}

/**
 * 7. THU THẬP TỪ VỰNG VÀO KHO ÔN TẬP SRS (EBBINGHAUS)
 */
async function collectVocab(word, event) {
    if (event) event.stopPropagation();

    try {
        const response = await fetch("/api/vision/save-vocab", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                word: word,
                parent_object: primaryObject
            })
        });

        const data = await response.json();
        if (data.status === "success") {
            alert(`🎉 ${data.message}`);
            // Đổi nút thu thập thành đã thu thập
            if (event && event.target) {
                event.target.outerHTML = `<span style="font-size: 10px; color: #4ade80;">✓ Đã lưu</span>`;
            }
        } else {
            alert(`Thông báo: ${data.message}`);
        }
    } catch (e) {
        console.error("Lỗi khi lưu từ vựng:", e);
        alert("Lỗi kết nối tới kho dữ liệu từ vựng!");
    }
}

/**
 * 8. CHẤM ĐIỂM CÂU VĂN GHÉP ĐƯỢC (GEC ENGINE & CRITIQUE SYNTHESIZER)
 */
function updateSentenceSubmitButton() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const words = dropZone.querySelectorAll(".word-token");
    document.getElementById("btn-submit-sentence").disabled = (words.length === 0);
}

function clearSentence() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const pool = document.getElementById("word-pool");
    const tokens = Array.from(dropZone.querySelectorAll(".word-token"));
    tokens.forEach(t => pool.appendChild(t));
    updateSentenceSubmitButton();
    document.getElementById("feedback-deck").style.display = "none";
}

function addCustomWordPrompt() {
    const customWord = prompt("Nhập từ tiếng Anh bạn muốn thêm vào khay (ví dụ: 'broken', 'clean', 'old'):");
    if (customWord && customWord.trim()) {
        const pool = document.getElementById("word-pool");
        const token = createWordTokenElement(customWord.trim().toLowerCase(), "", "A2", "Tự bổ sung", true);
        pool.appendChild(token);
    }
}

async function submitSentence() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const tokens = dropZone.querySelectorAll(".word-token");
    if (tokens.length === 0) return;

    const words = Array.from(tokens).map(t => t.getAttribute("data-word"));
    const sentence = words.join(" ");

    const submitBtn = document.getElementById("btn-submit-sentence");
    submitBtn.disabled = true;
    submitBtn.innerHTML = "<span>⏳</span> Đang chấm điểm...";

    try {
        const response = await fetch("/api/vision/submit-sentence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sentence: sentence,
                words_used: words,
                primary_object: primaryObject
            })
        });

        const data = await response.json();
        if (data.status === "success") {
            const feedbackDeck = document.getElementById("feedback-deck");
            feedbackDeck.style.display = "block";

            document.getElementById("score-badge").innerText = `Điểm: ${data.score}/100`;
            document.getElementById("result-original").innerText = data.original_sentence;
            document.getElementById("result-corrected").innerText = data.corrected_sentence;
            document.getElementById("result-critique").innerText = data.feedback || "Cấu trúc câu rất tốt!";
            document.getElementById("result-exp").innerHTML = `<span>⭐</span> +${data.exp_awarded} EXP đã được cộng vào tài khoản của bạn!`;

            feedbackDeck.scrollIntoView({ behavior: "smooth" });
        } else {
            alert(`Lỗi khi chấm câu: ${data.message}`);
        }
    } catch (e) {
        console.error("Lỗi submit câu:", e);
        alert("Lỗi khi kết nối tới engine chấm câu!");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "<span>✨</span> Chấm Điểm & Phân Tích Ngữ Pháp";
    }
}

function speakWord(word, event) {
    if (event) event.stopPropagation();
    if ("speechSynthesis" in window) {
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.lang = "en-US";
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }
}

function playHapticSound(type) {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === "grab") {
            osc.frequency.setValueAtTime(440, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.08);
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
            osc.start();
            osc.stop(ctx.currentTime + 0.08);
        } else {
            osc.frequency.setValueAtTime(660, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(330, ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.12, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
            osc.start();
            osc.stop(ctx.currentTime + 0.1);
        }
    } catch (e) {
        // Bỏ qua nếu audio context bị khóa
    }
}

function resetArena() {
    currentDetectedParts = [];
    document.getElementById("word-pool").innerHTML = `<div style="color: #64748b; font-style: italic; font-size: 13px; margin: auto;">Bấm "Bật Camera" và hướng đồ vật trước ống kính, sau đó nhấn "Quét Chi Tiết Đồ Vật"...</div>`;
    document.getElementById("word-count-badge").innerText = "0 từ vựng";
    clearSentence();
    if (canvasCtx && canvasElement) {
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }
}
