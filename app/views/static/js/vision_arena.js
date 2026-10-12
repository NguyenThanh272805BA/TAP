/**
 * VISION ARENA & AIR GESTURE INTERACTION ENGINE (TAP 2026) - VERSION 2.0 (HIGH-PERFORMANCE)
 * Tối ưu hóa triệt để: Triệt tiêu giật lag 100%, Con trỏ cử chỉ ảo toàn màn hình (Air Pointer),
 * Tự động đồng bộ tọa độ không gian và hỗ trợ chế độ tương tác kép (Gesture + Mouse).
 */

let videoElement = null;
let canvasElement = null;
let canvasCtx = null;
let cameraStream = null;
let mediapipeHands = null;

let isCameraActive = false;
let isProcessingFrame = false;
let lastSendTime = 0;
let controlMode = "gesture"; // 'gesture' | 'mouse'

let currentDetectedParts = [];
let primaryObject = "object";
let scannedWordRegistry = [];
let currentOmniDomain = "all"; // 'all' | 'objects' | 'creatures' | 'scenes' | 'environment'
let currentWordFilter = "all"; // 'all' | 'objects' | 'creatures' | 'scenes' | 'environment' | 'connectors'
let currentLevelFilter = "all"; // 'all' | 'basic' | 'advanced'
let selectedObjectCategory = "all";

let activeMediaType = "camera"; // 'camera' | 'image' | 'video'
let uploadedVideoElement = null;
let uploadedImageElement = null;
let videoAutoScanInterval = null;

// Quản lý con trỏ cử chỉ ảo toàn màn hình
let airPointer = null;
let airPointerIcon = null;
let smoothedHand = { x: 0.5, y: 0.5 };
let currentGesture = "NONE"; // NONE, OPEN, PINCH, FIST
let grabbedElement = null;

// Thống kê FPS
let lastFrameTime = performance.now();
let frameCount = 0;
let currentFPS = 0;
let activeWorkspace = "scanner"; // 'scanner' | 'vault'

// Trạng thái Vòng Đỏ Soi Vật Thể (Target Spotlight Reticle)
let isReticleActive = true;
let reticleNormPos = { x: 0.5, y: 0.4 };
let reticleRadius = 45;
let currentReticleWord = null;
let isDraggingReticle = false;
let isResizingReticle = false;

document.addEventListener("DOMContentLoaded", () => {
    videoElement = document.getElementById("webcam-video");
    canvasElement = document.getElementById("vision-canvas");
    airPointer = document.getElementById("air-pointer");
    airPointerIcon = document.getElementById("air-pointer-icon");
    uploadedVideoElement = document.getElementById("uploaded-video-player");
    uploadedImageElement = document.getElementById("uploaded-image-preview");

    if (canvasElement) {
        canvasCtx = canvasElement.getContext("2d");
    }

    window.addEventListener("resize", () => {
        resizeCanvas();
        moveReticleTo(reticleNormPos.x, reticleNormPos.y);
    });
    document.addEventListener("fullscreenchange", () => setTimeout(() => {
        resizeCanvas();
        moveReticleTo(reticleNormPos.x, reticleNormPos.y);
    }, 100));
    resizeCanvas();

    // Lắng nghe phím tắt số 1, 2 chuyển nhanh giữa các Workspace
    window.addEventListener("keydown", (e) => {
        const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        if (e.key === '1') switchWorkspace('scanner');
        else if (e.key === '2') switchWorkspace('vault');
    });

    // KHỞI TẠO TƯƠNG TÁC VÒNG ĐỎ SOI VẬT THỂ (MÀN HÌNH CẢM ỨNG, CHUỘT & RESIZE)
    initTargetReticleEvents();

    // Khởi tạo trạng thái Workspace ban đầu
    updateWorkspaceBadges();
    renderLiveDetectionStrip();

    // Đặt vị trí ban đầu cho Vòng Đỏ
    setTimeout(() => {
        moveReticleTo(0.5, 0.4);
    }, 150);

    // Khởi tạo MediaPipe
    initMediaPipeHands();
});

function initTargetReticleEvents() {
    const reticleEl = document.getElementById("target-reticle");
    const resizeHandle = document.getElementById("reticle-resize-handle");
    const wrapper = document.getElementById("viewport-wrapper");

    // Tay nắm góc kéo để phóng to / thu nhỏ vòng tròn
    if (resizeHandle) {
        resizeHandle.addEventListener("mousedown", (e) => {
            isResizingReticle = true;
            isDraggingReticle = false;
            e.stopPropagation();
            e.preventDefault();
        });

        resizeHandle.addEventListener("touchstart", (e) => {
            isResizingReticle = true;
            isDraggingReticle = false;
            e.stopPropagation();
        }, { passive: false });
    }

    if (reticleEl) {
        // Chuột kéo di chuyển vòng đỏ
        reticleEl.addEventListener("mousedown", (e) => {
            if (e.target.closest("button") || e.target.closest("#reticle-resize-handle")) return;
            isDraggingReticle = true;
            isResizingReticle = false;
            e.preventDefault();
        });

        // Chạm ngón tay kéo di chuyển vòng đỏ (Hỗ trợ 100% thiết bị di động / điện thoại)
        reticleEl.addEventListener("touchstart", (e) => {
            if (e.target.closest("button") || e.target.closest("#reticle-resize-handle")) return;
            isDraggingReticle = true;
            isResizingReticle = false;
            e.stopPropagation();
        }, { passive: false });

        // Cuộn bánh xe chuột để phóng to / thu nhỏ vòng tròn
        reticleEl.addEventListener("wheel", (e) => {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 8 : -8;
            stepReticleZoom(delta);
        }, { passive: false });
    }

    // Sự kiện kéo chuột toàn cửa sổ (hỗ trợ cả kéo di chuyển và kéo góc thu phóng)
    window.addEventListener("mousemove", (e) => {
        if (!wrapper) return;
        const rect = wrapper.getBoundingClientRect();

        if (isResizingReticle) {
            const centerX = rect.left + reticleNormPos.x * rect.width;
            const centerY = rect.top + reticleNormPos.y * rect.height;
            const dist = Math.hypot(e.clientX - centerX, e.clientY - centerY);
            setReticleDiameter(Math.round(dist * 2));
            return;
        }

        if (isDraggingReticle) {
            const normX = (e.clientX - rect.left) / rect.width;
            const normY = (e.clientY - rect.top) / rect.height;
            moveReticleTo(normX, normY);
        }
    });

    // Sự kiện vuốt ngón tay toàn màn hình cho điện thoại
    window.addEventListener("touchmove", (e) => {
        if (!wrapper || !e.touches[0]) return;
        const touch = e.touches[0];
        const rect = wrapper.getBoundingClientRect();

        if (isResizingReticle) {
            const centerX = rect.left + reticleNormPos.x * rect.width;
            const centerY = rect.top + reticleNormPos.y * rect.height;
            const dist = Math.hypot(touch.clientX - centerX, touch.clientY - centerY);
            setReticleDiameter(Math.round(dist * 2));
            e.preventDefault();
            return;
        }

        if (isDraggingReticle) {
            const normX = (touch.clientX - rect.left) / rect.width;
            const normY = (touch.clientY - rect.top) / rect.height;
            moveReticleTo(normX, normY);
            e.preventDefault();
        }
    }, { passive: false });

    window.addEventListener("mouseup", () => {
        isDraggingReticle = false;
        isResizingReticle = false;
    });
    window.addEventListener("touchend", () => {
        isDraggingReticle = false;
        isResizingReticle = false;
    });

    // Chạm hoặc Click vào bất kỳ vị trí nào trên Camera -> Vòng đỏ tự động lướt tới đó!
    if (wrapper) {
        wrapper.addEventListener("click", (e) => {
            if (!isReticleActive) return;
            if (e.target.closest("button") || 
                e.target.closest("#reticle-resize-handle") ||
                e.target.closest(".hud-metrics") ||
                e.target.closest(".hud-gesture-badge") ||
                e.target.closest("#media-mode-bar") ||
                e.target.closest("#ar-feedback-modal")) {
                return;
            }
            const rect = wrapper.getBoundingClientRect();
            const normX = (e.clientX - rect.left) / rect.width;
            const normY = (e.clientY - rect.top) / rect.height;
            moveReticleTo(normX, normY);
        });
    }
}

function resizeCanvas() {
    if (!canvasElement || !canvasElement.parentElement) return;
    const rect = canvasElement.parentElement.getBoundingClientRect();
    canvasElement.width = rect.width;
    canvasElement.height = rect.height;
}

function setControlMode(mode) {
    controlMode = mode;
    const gestureBtn = document.getElementById("mode-gesture-btn");
    const mouseBtn = document.getElementById("mode-mouse-btn");

    if (mode === "gesture") {
        gestureBtn.classList.add("active");
        mouseBtn.classList.remove("active");
        if (airPointer && isCameraActive) airPointer.style.display = "block";
    } else {
        mouseBtn.classList.add("active");
        gestureBtn.classList.remove("active");
        if (airPointer) airPointer.style.display = "none";
        if (grabbedElement) releaseGrabbedElement(false);
    }
}

/**
 * 0. QUẢN LÝ CHUYỂN ĐỔI WORKSPACES & VIEWPORT CAMERA
 */
function switchWorkspace(mode) {
    if (mode === "assembly") mode = "scanner"; // Hợp nhất để trải nghiệm AR luôn ở camera lớn nhất
    activeWorkspace = mode;

    // 1. Cập nhật trạng thái các Tab buttons
    const btnScanner = document.getElementById("ws-btn-scanner");
    const btnVault = document.getElementById("ws-btn-vault");

    if (btnScanner) btnScanner.classList.toggle("active", mode === "scanner");
    if (btnVault) btnVault.classList.toggle("active", mode === "vault");

    // 2. Chuyển đổi hiển thị Panels
    const panelScanner = document.getElementById("workspace-scanner");
    const panelVault = document.getElementById("workspace-vault");

    if (panelScanner) panelScanner.classList.toggle("active", mode === "scanner");
    if (panelVault) panelVault.classList.toggle("active", mode === "vault");

    // 3. Quản lý Viewport Camera (Luôn giữ Cinema View siêu rộng, không bị PiP che góc)
    const viewportWrapper = document.getElementById("viewport-wrapper");
    const cinemaHost = document.getElementById("cinema-viewport-host");

    if (viewportWrapper && cinemaHost && viewportWrapper.parentElement !== cinemaHost) {
        cinemaHost.appendChild(viewportWrapper);
    }
    if (viewportWrapper) {
        viewportWrapper.classList.remove("pip-mode");
        viewportWrapper.classList.add("cinema-mode");
    }

    // 4. Đồng bộ kích thước canvas vẽ và định vị lại vòng đỏ
    setTimeout(() => {
        resizeCanvas();
        if (!isCameraActive && activeMediaType !== "camera") {
            drawDetectedBoundingBoxes();
        }
        moveReticleTo(reticleNormPos.x, reticleNormPos.y);
    }, 60);

    // 5. Cập nhật dữ liệu tương ứng cho từng màn hình
    if (mode === "scanner") {
        renderWordPool();
        updateReticleTarget();
    } else if (mode === "vault") {
        renderVaultCards();
    }
    updateWorkspaceBadges();
}

/**
 * 0.05 QUẢN LÝ MIỀN THỰC THỂ TOÀN CẢNH (OMNI-DOMAIN SELECTION & HUD)
 */
function setOmniDomain(domain) {
    currentOmniDomain = domain;
    ["all", "objects", "creatures", "scenes", "environment"].forEach(d => {
        const btn = document.getElementById(`domain-btn-${d}`);
        if (btn) btn.classList.toggle("active", d === domain);
    });

    const domainNames = {
        all: "Toàn Cảnh (Mọi Miền)",
        objects: "Đồ Vật (Objects)",
        creatures: "Sinh Vật (Creatures)",
        scenes: "Khung Cảnh (Scenes)",
        environment: "Môi Trường (Environment)"
    };

    const statusHud = document.getElementById("status-hud");
    if (statusHud) {
        statusHud.innerHTML = `🌐 Miền thực thể: <b>${domainNames[domain] || domain}</b>`;
    }

    // Nếu đang có hình ảnh / camera và có từ đã quét, kích hoạt cập nhật kho từ tương ứng
    if (scannedWordRegistry.length > 0) {
        renderWordPool();
    }
}

function updateOmniSceneHud(sceneInfo, contextCaption, domainBreakdown) {
    const hudContainer = document.getElementById("omni-scene-hud");
    if (!hudContainer) return;

    if (!sceneInfo && !contextCaption) {
        hudContainer.style.display = "none";
        return;
    }

    hudContainer.style.display = "block";

    if (sceneInfo) {
        const sceneEl = document.getElementById("hud-scene-text");
        if (sceneEl) {
            sceneEl.innerText = `${sceneInfo.scene_vn || sceneInfo.scene_type || "Không gian mở"}`;
        }
        const lightingEl = document.getElementById("hud-lighting-text");
        if (lightingEl) {
            lightingEl.innerText = `${sceneInfo.lighting_vn || sceneInfo.lighting_condition || "Ánh sáng tự nhiên"}`;
        }
        const atmosphereEl = document.getElementById("hud-atmosphere-text");
        if (atmosphereEl) {
            atmosphereEl.innerText = `${sceneInfo.atmosphere_vn || sceneInfo.atmosphere || "Cân bằng"}`;
        }
    }

    if (contextCaption) {
        const enEl = document.getElementById("hud-caption-en");
        const vnEl = document.getElementById("hud-caption-vn");
        if (enEl) enEl.innerText = contextCaption.en || "";
        if (vnEl) vnEl.innerText = contextCaption.vn || "";

        const subtitleStrip = document.getElementById("camera-ar-subtitle-strip");
        if (subtitleStrip && contextCaption.en) {
            subtitleStrip.innerText = contextCaption.en;
            subtitleStrip.style.display = "block";
        }
    }
}

/**
 * 0.1 ĐIỀU KHIỂN VÒNG ĐỎ SOI VẬT THỂ (TARGET SPOTLIGHT RETICLE)
 */
function moveReticleTo(normX, normY) {
    const reticleEl = document.getElementById("target-reticle");
    const wrapper = document.getElementById("viewport-wrapper");
    if (!reticleEl || !wrapper) return;

    reticleNormPos.x = Math.max(0.04, Math.min(0.96, normX));
    reticleNormPos.y = Math.max(0.04, Math.min(0.96, normY));

    const pxX = reticleNormPos.x * wrapper.clientWidth;
    const pxY = reticleNormPos.y * wrapper.clientHeight;

    reticleEl.style.left = `${pxX}px`;
    reticleEl.style.top = `${pxY}px`;

    updateReticleTarget();
}

function updateReticleTarget() {
    let matchedPart = null;
    let minDistance = 999999;

    // Tìm trong danh sách các chi tiết vật thể đã quét
    currentDetectedParts.forEach(part => {
        const box = part.normalized_box;
        if (!box) return;

        const isInside = (reticleNormPos.x >= box.xmin && reticleNormPos.x <= box.xmax &&
                          reticleNormPos.y >= box.ymin && reticleNormPos.y <= box.ymax);
        const centerX = (box.xmin + box.xmax) / 2;
        const centerY = (box.ymin + box.ymax) / 2;
        const dist = Math.hypot(reticleNormPos.x - centerX, reticleNormPos.y - centerY);

        if (isInside) {
            matchedPart = part;
        } else if (!matchedPart && dist < 0.28 && dist < minDistance) {
            minDistance = dist;
            matchedPart = part;
        }
    });

    if (matchedPart) {
        currentReticleWord = matchedPart;
    } else {
        currentReticleWord = null;
    }

    // Cập nhật lại khung viền bounding boxes trên canvas (hộp được ngắm sẽ sáng đỏ)
    if (!isCameraActive && canvasCtx && canvasElement) {
        drawDetectedBoundingBoxes();
    }
}

function toggleTargetReticle() {
    isReticleActive = !isReticleActive;
    const reticleEl = document.getElementById("target-reticle");
    const zoomDock = document.getElementById("reticle-zoom-dock");
    const textEl = document.getElementById("reticle-text");
    const btnEl = document.getElementById("btn-toggle-reticle");

    if (reticleEl) {
        reticleEl.style.display = isReticleActive ? "flex" : "none";
    }
    if (zoomDock) {
        zoomDock.style.display = isReticleActive ? "inline-flex" : "none";
    }
    if (textEl) {
        textEl.innerText = isReticleActive ? "Vòng Đỏ: Bật" : "Vòng Đỏ: Tắt";
    }
    if (btnEl) {
        btnEl.style.borderColor = isReticleActive ? "#ef4444" : "rgba(148, 163, 184, 0.4)";
        btnEl.style.background = isReticleActive ? "linear-gradient(135deg, rgba(239, 68, 68, 0.28), rgba(220, 38, 38, 0.38))" : "rgba(30, 41, 59, 0.6)";
    }
    if (isReticleActive) updateReticleTarget();
}

function stepReticleZoom(delta) {
    const currentDiameter = reticleRadius * 2;
    const newDiameter = Math.max(36, Math.min(240, currentDiameter + delta));
    setReticleDiameter(newDiameter);
}

function setReticleDiameter(diameter) {
    const dia = Math.max(36, Math.min(240, parseInt(diameter) || 90));
    reticleRadius = dia / 2;

    const reticleEl = document.getElementById("target-reticle");
    if (reticleEl) {
        reticleEl.style.width = `${dia}px`;
        reticleEl.style.height = `${dia}px`;
    }

    const slider = document.getElementById("reticle-zoom-slider");
    if (slider) slider.value = dia;

    const label = document.getElementById("reticle-diameter-label");
    if (label) label.innerText = `${dia}px`;

    updateReticleTarget();
}

function setReticleSize(radius, event) {
    if (event) event.stopPropagation();
    setReticleDiameter(radius * 2);
}

function addReticleWordToSentence(event) {
    if (event) event.stopPropagation();
    if (!currentReticleWord) return;
    insertWordToSentence(currentReticleWord.word);
}

function collectReticleWord(event) {
    if (event) event.stopPropagation();
    if (!currentReticleWord) return;
    collectVocab(currentReticleWord.word, event);
}

function speakReticleWord(event) {
    if (event) event.stopPropagation();
    if (!currentReticleWord) return;
    speakWord(currentReticleWord.word, event);
}

/**
 * 0.2 ĐIỀU KHIỂN KHAY GHÉP CÂU TRỰC TIẾP TRONG CAMERA (AR SENTENCE DOCK)
 */
function insertWordToSentence(word) {
    if (!word) return;
    const dropZone = document.getElementById("assembly-drop-zone");
    if (!dropZone) return;

    const item = scannedWordRegistry.find(w => w.word.toLowerCase() === word.toLowerCase());
    const token = createWordTokenElement(
        word.toLowerCase(),
        item ? item.ipa : "",
        item ? item.cefr : "B1",
        item ? item.meaning : "",
        item ? item.isLearned : false,
        true,
        item ? item.levelTier : "basic"
    );

    dropZone.appendChild(token);
    playHapticSound("drop");
    updateSentenceSubmitButton();
    updateWorkspaceBadges();
}

function toggleArDockCollapse() {
    // Không còn khung hộp chắn trong camera
}

function focusArSentenceDock() {
    switchWorkspace("scanner");
    const deck = document.getElementById("sentence-assembly-deck");
    if (deck) {
        deck.scrollIntoView({ behavior: "smooth", block: "center" });
        deck.style.transition = "box-shadow 0.4s ease, border-color 0.4s ease";
        deck.style.borderColor = "var(--neon-cyan)";
        deck.style.boxShadow = "0 0 35px rgba(6, 182, 212, 0.5)";
        setTimeout(() => {
            deck.style.boxShadow = "";
            deck.style.borderColor = "";
        }, 1200);
    }
}

function closeArFeedbackModal() {
    const modal = document.getElementById("ar-feedback-modal");
    if (modal) modal.style.display = "none";
}

function toggleFullscreenViewport() {
    const wrapper = document.getElementById("viewport-wrapper");
    if (!wrapper) return;

    if (!document.fullscreenElement) {
        if (wrapper.requestFullscreen) {
            wrapper.requestFullscreen().catch(err => console.warn("Fullscreen request error:", err));
        } else if (wrapper.webkitRequestFullscreen) {
            wrapper.webkitRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(err => console.warn("Exit fullscreen error:", err));
        }
    }
}

function updateWorkspaceBadges() {
    // Tab 1 badge: số vật thể phát hiện
    const badgeDetected = document.getElementById("badge-detected-count");
    if (badgeDetected) {
        badgeDetected.innerText = `${currentDetectedParts.length} vật thể`;
    }

    // Tab 2 / AR Dock badge: số từ trong khay ghép câu trực tiếp trên Camera
    const dropZone = document.getElementById("assembly-drop-zone");
    const count = dropZone ? dropZone.querySelectorAll(".word-token").length : 0;
    const badgeSentence = document.getElementById("badge-sentence-count");
    if (badgeSentence) {
        badgeSentence.innerText = `${count} từ trong khay`;
    }
    const arBadge = document.getElementById("ar-sentence-count-badge");
    if (arBadge) {
        arBadge.innerText = `${count} từ`;
    }

    // Tab 3 badge: số từ vựng vật thể đã ghi nhận
    const badgeVault = document.getElementById("badge-vault-count");
    if (badgeVault) {
        const objCount = scannedWordRegistry.filter(w => w.isObjectPart).length;
        badgeVault.innerText = `${objCount} từ đã quét`;
    }

    // Cập nhật 4 chỉ số KPI trong Workspace 3 (Vault)
    const statTotal = document.getElementById("vault-stat-total");
    const statBasic = document.getElementById("vault-stat-basic");
    const statAdv = document.getElementById("vault-stat-advanced");
    const statLearned = document.getElementById("vault-stat-learned");

    if (statTotal) {
        const totalObj = scannedWordRegistry.filter(w => w.isObjectPart).length;
        statTotal.innerText = `${totalObj} từ`;
    }
    if (statBasic) {
        const basicCount = scannedWordRegistry.filter(w => w.isObjectPart && w.levelTier === "basic").length;
        statBasic.innerText = `${basicCount} từ`;
    }
    if (statAdv) {
        const advCount = scannedWordRegistry.filter(w => w.isObjectPart && w.levelTier === "advanced").length;
        statAdv.innerText = `${advCount} từ`;
    }
    if (statLearned) {
        const learnedCount = scannedWordRegistry.filter(w => w.isObjectPart && w.isLearned).length;
        statLearned.innerText = `${learnedCount} từ`;
    }
}

function renderLiveDetectionStrip() {
    const chipsContainer = document.getElementById("live-detection-chips");
    if (!chipsContainer) return;

    chipsContainer.innerHTML = "";

    if (!currentDetectedParts || currentDetectedParts.length === 0) {
        chipsContainer.innerHTML = `<span style="color: #64748b; font-style: italic; font-size: 12px;">Chưa quét vật thể. Hãy bấm "Bật Camera" hoặc chọn ảnh mẫu phía dưới!</span>`;
        return;
    }

    currentDetectedParts.forEach(part => {
        const chip = document.createElement("div");
        chip.className = "quick-word-chip";
        chip.style.display = "inline-flex";
        chip.style.alignItems = "center";
        chip.style.gap = "6px";
        chip.style.padding = "5px 10px";
        chip.style.fontSize = "12px";
        chip.style.borderRadius = "8px";

        const isBasic = (part.level_tier === "basic" || ["A1", "A2"].includes((part.cefr || "").toUpperCase()));
        const badgeColor = isBasic ? "#22d3ee" : "#c084fc";
        const badgeBg = isBasic ? "rgba(34, 211, 238, 0.2)" : "rgba(168, 85, 247, 0.2)";
        const domainName = (part.domain || 'objects').toUpperCase();
        const hierarchyHtml = part.hierarchy_label ? `<span style="font-size: 10px; font-weight: 800; color: #fb7185; background: rgba(244, 63, 94, 0.2); border: 1px solid rgba(244, 63, 94, 0.5); padding: 1px 6px; border-radius: 4px;">${part.hierarchy_label}</span>` : '';
        const adjHtml = (part.academic_adjectives && part.academic_adjectives.length > 0) ? `<span style="color: #67e8f9; font-size: 10.5px; font-style: italic;">(${part.academic_adjectives.slice(0, 2).join(', ')})</span>` : '';

        chip.innerHTML = `
            <span class="domain-tag ${part.domain || 'objects'}">${domainName}</span>
            ${hierarchyHtml}
            <span style="font-size: 10px; font-weight: 800; color: ${badgeColor}; background: ${badgeBg}; padding: 1px 5px; border-radius: 4px;">${part.cefr || 'B1'}</span>
            <strong style="color: #fff;">${(part.word || '').toUpperCase()}</strong>
            ${part.meaning ? `<span style="color: #fef08a; font-size: 11px;">(${part.meaning})</span>` : ''}
            ${adjHtml}
            <button type="button" style="background: none; border: none; cursor: pointer; color: #38bdf8; display: inline-flex; align-items: center;" onclick="speakWord('${part.word}', event)" title="Nghe phát âm">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            </button>
            <button type="button" class="action-pill-btn btn-primary-pill" style="padding: 2px 7px; font-size: 10px; display: inline-flex; align-items: center; gap: 3px;" onclick="useWordInAssembly('${part.word}')" title="Chuyển sang Khay Ghép Câu">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19.439 7.85c0-1.57.802-2.54 1.561-3.34V4.5a2 2 0 0 0-2-2h-3.5a2.5 2.5 0 0 1-5 0H7a2 2 0 0 0-2 2v.01c.759.8 1.561 1.77 1.561 3.34 0 1.58-.802 2.55-1.561 3.35V11.2a2 2 0 0 0 2 2h3.5a2.5 2.5 0 0 1 5 0H19a2 2 0 0 0 2-2v-.01c-.759-.8-1.561-1.77-1.561-3.34Z"/><circle cx="12" cy="12" r="2"/></svg>
                <span>Dùng</span>
            </button>
        `;

        chipsContainer.appendChild(chip);
    });
}

function renderVaultCards() {
    const container = document.getElementById("vault-cards-container");
    if (!container) return;

    container.innerHTML = "";

    const objectWords = scannedWordRegistry.filter(w => w.isObjectPart);

    if (objectWords.length === 0) {
        container.innerHTML = `
            <div style="color: #64748b; font-style: italic; font-size: 13px; grid-column: 1 / -1; padding: 30px; text-align: center;">
                Kho từ vựng chưa có dữ liệu. Hãy chuyển sang Tab "1. Khung Nhìn Thị Giác" để quét đồ vật!
            </div>
        `;
        return;
    }

    const searchInput = document.getElementById("vault-search-input");
    const searchVal = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const filterTierEl = document.getElementById("vault-filter-tier");
    const tierVal = filterTierEl ? filterTierEl.value : "all";

    const filteredWords = objectWords.filter(item => {
        if (searchVal) {
            const matchWord = item.word.toLowerCase().includes(searchVal);
            const matchMeaning = (item.meaning || "").toLowerCase().includes(searchVal);
            if (!matchWord && !matchMeaning) return false;
        }
        if (tierVal === "basic" && item.levelTier !== "basic") return false;
        if (tierVal === "advanced" && item.levelTier !== "advanced") return false;
        if (tierVal === "learned" && !item.isLearned) return false;
        if (["objects", "creatures", "scenes", "environment"].includes(tierVal) && item.domain !== tierVal) return false;
        return true;
    });

    if (filteredWords.length === 0) {
        container.innerHTML = `
            <div style="color: #64748b; font-style: italic; font-size: 13px; grid-column: 1 / -1; padding: 30px; text-align: center;">
                Không tìm thấy từ vựng nào khớp với bộ lọc hiện tại.
            </div>
        `;
        return;
    }

    filteredWords.forEach(item => {
        const card = document.createElement("div");
        card.className = "vault-word-card";

        const isBasic = item.levelTier === "basic";
        const tierBadge = isBasic 
            ? `<span style="background: rgba(34, 211, 238, 0.2); color: #22d3ee; border: 1px solid #22d3ee; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2"><path d="M12 22v-9"/><path d="M12 13a5 5 0 0 0 5-5c0-3-2-5-5-5s-5 2-5 5a5 5 0 0 0 5 5Z"/></svg> A1-A2 Cơ Bản</span>`
            : `<span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #c084fc; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg> B1-C1 Chuyên Sâu</span>`;
        const domainBadge = `<span class="domain-tag ${item.domain || 'objects'}" style="margin-left: 6px;">${(item.domain || 'objects').toUpperCase()}</span>`;

        card.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <h3 style="margin: 0; color: #fff; font-size: 17px; font-weight: 800; letter-spacing: 0.5px;">${item.word.toUpperCase()}</h3>
                            ${domainBadge}
                            <button type="button" style="background: none; border: none; cursor: pointer; color: #38bdf8; display: inline-flex; align-items: center;" onclick="speakWord('${item.word}', event)" title="Nghe phát âm">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                            </button>
                        </div>
                        ${item.ipa ? `<div style="color: #94a3b8; font-size: 12px; font-family: var(--text-mono);">${item.ipa}</div>` : ''}
                    </div>
                    ${tierBadge}
                </div>

                <div style="background: rgba(2, 6, 23, 0.6); padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid var(--neon-cyan);">
                    <div style="color: #fef08a; font-weight: 600; font-size: 13px;">${item.meaning}</div>
                    <div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">
                        Miền: <b style="color: #67e8f9;">${(item.domain || 'objects').toUpperCase()}</b> • Nguồn: <b style="color: #cbd5e1;">${(item.parentObject || 'object').toUpperCase()}</b>
                    </div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; border-top: 1px dashed rgba(103, 232, 249, 0.2); padding-top: 10px;">
                <button type="button" class="action-pill-btn btn-primary-pill" onclick="useWordInAssembly('${item.word}')" style="font-size: 11px; padding: 5px 10px; display: inline-flex; align-items: center; gap: 4px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19.439 7.85c0-1.57.802-2.54 1.561-3.34V4.5a2 2 0 0 0-2-2h-3.5a2.5 2.5 0 0 1-5 0H7a2 2 0 0 0-2 2v.01c.759.8 1.561 1.77 1.561 3.34 0 1.58-.802 2.55-1.561 3.35V11.2a2 2 0 0 0 2 2h3.5a2.5 2.5 0 0 1 5 0H19a2 2 0 0 0 2-2v-.01c-.759-.8-1.561-1.77-1.561-3.34Z"/><circle cx="12" cy="12" r="2"/></svg>
                    <span>Đưa vào khay ghép</span>
                </button>
                ${item.isLearned 
                    ? `<span style="font-size: 11px; color: #4ade80; font-weight: 700;">✓ Đã lưu SRS</span>`
                    : `<button type="button" class="action-pill-btn" onclick="collectVocab('${item.word}', event)" style="font-size: 11px; padding: 5px 10px; background: rgba(16, 185, 129, 0.2); border-color: #34d399; color: #34d399;">+ Thu thập</button>`
                }
            </div>
        `;

        container.appendChild(card);
    });
}

function useWordInAssembly(word) {
    if (!word) return;
    switchWorkspace("assembly");

    const dropZone = document.getElementById("assembly-drop-zone");
    if (!dropZone) return;

    const existingToken = dropZone.querySelector(`.word-token[data-word="${word.toLowerCase()}"]`);
    if (!existingToken) {
        const item = scannedWordRegistry.find(w => w.word.toLowerCase() === word.toLowerCase());
        const token = createWordTokenElement(
            word.toLowerCase(),
            item ? item.ipa : "",
            item ? item.cefr : "B1",
            item ? item.meaning : "",
            item ? item.isLearned : false,
            true,
            item ? item.levelTier : "basic"
        );
        dropZone.appendChild(token);
    }

    playHapticSound("drop");
    updateSentenceSubmitButton();
    updateWorkspaceBadges();
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
                width: { ideal: 640 },
                height: { ideal: 480 },
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

        if (controlMode === "gesture" && airPointer) {
            airPointer.style.display = "block";
        }

        resizeCanvas();
        requestAnimationFrame(renderLoop);

    } catch (err) {
        console.error("Lỗi truy cập Camera:", err);
        alert("Không thể truy cập Camera. Bạn có thể sử dụng các nút '🧪 Thử nhanh ảnh mẫu' ở thanh trên để trải nghiệm đầy đủ tính năng!");
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
    isProcessingFrame = false;
    document.getElementById("btn-toggle-camera").classList.remove("cyber-btn-pink");
    document.getElementById("cam-icon").innerText = "📹";
    document.getElementById("cam-text").innerText = "Bật Camera";
    document.getElementById("btn-scan-frame").disabled = true;
    document.getElementById("status-hud").innerHTML = "🔴 Camera: Đang tắt";
    document.getElementById("gesture-text").innerText = "Camera đã tắt";

    if (airPointer) airPointer.style.display = "none";
    if (grabbedElement) releaseGrabbedElement(false);

    if (canvasCtx && canvasElement) {
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }
}

/**
 * 2. TỐI ƯU HÓA MEDIAPIPE HANDS: TRIỆT TIÊU NGHẼN HÀNG ĐỢI & GIẬT LAG
 */
function initMediaPipeHands() {
    if (typeof Hands === "undefined") {
        console.warn("Đang chờ nạp MediaPipe Hands từ CDN...");
        setTimeout(initMediaPipeHands, 800);
        return;
    }

    try {
        mediapipeHands = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        mediapipeHands.setOptions({
            maxNumHands: 1,
            modelComplexity: 0, // Dùng model lite (0) thay vì model (1) để mượt mà gấp 2x trên mọi máy!
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        mediapipeHands.onResults(onHandResults);
        console.log("[x] MediaPipe Hands Lite khởi tạo thành công!");
    } catch (e) {
        console.error("Lỗi khởi tạo MediaPipe Hands:", e);
    }
}

let frameProcessingStartTime = 0;

function renderLoop() {
    if (!isCameraActive || !videoElement) return;

    const now = performance.now();

    // Watchdog: Nếu một frame xử lý quá 400ms (MediaPipe bị trễ), tự động giải phóng cờ để tránh treo loop
    if (isProcessingFrame && (now - frameProcessingStartTime > 400)) {
        isProcessingFrame = false;
    }

    // Giới hạn tần số gửi frame ở mức 28-30 FPS (~35ms) để đảm bảo CPU mát và mượt mà
    if (controlMode === "gesture" && !isProcessingFrame && (now - lastSendTime >= 35)) {
        if (videoElement.readyState >= 2 && mediapipeHands) {
            isProcessingFrame = true;
            frameProcessingStartTime = now;
            lastSendTime = now;
            mediapipeHands.send({ image: videoElement })
                .catch(err => {
                    console.error("Lỗi MediaPipe frame:", err);
                })
                .finally(() => {
                    isProcessingFrame = false;
                });
        }
    }

    requestAnimationFrame(renderLoop);
}

function onHandResults(results) {
    if (!canvasCtx || !canvasElement) return;

    // Tính toán FPS thực tế
    frameCount++;
    const now = performance.now();
    if (now - lastFrameTime >= 1000) {
        currentFPS = Math.round((frameCount * 1000) / (now - lastFrameTime));
        document.getElementById("fps-hud").innerText = `⚡ FPS: ${currentFPS}`;
        frameCount = 0;
        lastFrameTime = now;
    }

    // Xóa frame cũ trên Viewfinder canvas
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    // Vẽ lại các bounding boxes
    drawDetectedBoundingBoxes();

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];

        // Lấy tọa độ gốc bàn tay (lật gương trục X vì video scaleX(-1))
        const rawNormX = 1.0 - landmarks[9].x;
        const rawNormY = landmarks[9].y;

        // Bộ lọc EMA làm mịn chống rung tay
        const alpha = 0.45;
        smoothedHand.x = alpha * rawNormX + (1 - alpha) * smoothedHand.x;
        smoothedHand.y = alpha * rawNormY + (1 - alpha) * smoothedHand.y;

        // Vẽ khung xương bàn tay lên Canvas Camera
        drawHandSkeleton(landmarks);

        // Phân loại cử chỉ: Kẹp ngón tay (Pinch) vs Nắm tay (Fist) vs Mở tay (Open)
        classifyGesture(landmarks);

        // Điều khiển con trỏ ảo toàn màn hình và tương tác gắp thẻ
        updateAirPointerAndInteraction(smoothedHand.x, smoothedHand.y);

    } else {
        currentGesture = "NONE";
        document.getElementById("gesture-emoji").innerText = "🖐️";
        document.getElementById("gesture-text").innerText = "Chưa thấy bàn tay";

        if (airPointer) airPointer.style.display = "none";
        if (grabbedElement) releaseGrabbedElement(false);
    }
}

function classifyGesture(landmarks) {
    // Đo kích thước bàn tay từ cổ tay (0) tới đốt gốc ngón giữa (9) để chuẩn hóa theo khoảng cách
    const wrist = landmarks[0];
    const middleMcp = landmarks[9];
    const handScale = Math.hypot(wrist.x - middleMcp.x, wrist.y - middleMcp.y) || 0.1;

    // 1. Khoảng cách giữa ngón cái tip (4) và ngón trỏ tip (8)
    const pinchDist = Math.hypot(landmarks[4].x - landmarks[8].x, landmarks[4].y - landmarks[8].y);
    const relativePinch = pinchDist / handScale;

    // 2. Khoảng cách trung bình từ các đầu ngón tay về cổ tay (0)
    const fingerTips = [8, 12, 16, 20];
    let avgDistToWrist = 0;
    fingerTips.forEach(idx => {
        avgDistToWrist += Math.hypot(landmarks[idx].x - wrist.x, landmarks[idx].y - wrist.y);
    });
    avgDistToWrist /= 4;
    const relativeWrist = avgDistToWrist / handScale;

    const gestureEmojiEl = document.getElementById("gesture-emoji");
    // Phân loại chuẩn xác bất kể đứng gần hay xa webcam
    if (relativePinch < 0.42 || pinchDist < 0.055) {
        currentGesture = "PINCH";
        if (gestureEmojiEl) gestureEmojiEl.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2"><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`;
        document.getElementById("gesture-text").innerText = "Kẹp ngón tay (Pinch)";
    } else if (relativeWrist < 1.15 || avgDistToWrist < 0.20) {
        currentGesture = "FIST";
        if (gestureEmojiEl) gestureEmojiEl.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f43f5e" stroke-width="2"><circle cx="12" cy="12" r="7"/></svg>`;
        document.getElementById("gesture-text").innerText = "Nắm tay (Grab)";
    } else {
        currentGesture = "OPEN";
        if (gestureEmojiEl) gestureEmojiEl.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="2"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v3"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v7"/><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>`;
        document.getElementById("gesture-text").innerText = "Bàn tay mở (Open)";
    }
}

function drawHandSkeleton(landmarks) {
    const w = canvasElement.width;
    const h = canvasElement.height;

    const connections = [
        [0, 1], [1, 2], [2, 3], [3, 4],
        [0, 5], [5, 6], [6, 7], [7, 8],
        [5, 9], [9, 10], [10, 11], [11, 12],
        [9, 13], [13, 14], [14, 15], [15, 16],
        [13, 17], [17, 18], [18, 19], [19, 20],
        [0, 17]
    ];

    canvasCtx.save();
    canvasCtx.lineWidth = 2.5;
    canvasCtx.strokeStyle = (currentGesture === "PINCH" || currentGesture === "FIST") ? "#f43f5e" : "#22d3ee";
    canvasCtx.shadowBlur = 8;
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

    landmarks.forEach((pt, idx) => {
        const x = (1.0 - pt.x) * w;
        const y = pt.y * h;
        canvasCtx.beginPath();
        canvasCtx.arc(x, y, (idx === 4 || idx === 8) ? 5.5 : 3, 0, 2 * Math.PI);
        canvasCtx.fillStyle = (idx === 4 || idx === 8) ? "#fbbf24" : "#ffffff";
        canvasCtx.fill();
    });

    canvasCtx.restore();
}

/**
 * 3. CON TRỎ ẢO TOÀN MÀN HÌNH (AIR POINTER) & GẮP THẢ CHỮ KHÔNG CHẠM
 */
function updateAirPointerAndInteraction(normX, normY) {
    if (!airPointer || controlMode !== "gesture") return;

    // Ánh xạ tọa độ chuẩn hóa (0..1) của camera sang tọa độ toàn màn hình cửa sổ (Viewport)
    // Margin 0.08 giúp người dùng dễ lia tay tới 4 góc màn hình
    const margin = 0.08;
    const clampedX = Math.max(0, Math.min(1, (normX - margin) / (1 - 2 * margin)));
    const clampedY = Math.max(0, Math.min(1, (normY - margin) / (1 - 2 * margin)));

    const screenX = clampedX * window.innerWidth;
    const screenY = clampedY * window.innerHeight;

    airPointer.style.display = "block";
    airPointer.style.left = `${screenX}px`;
    airPointer.style.top = `${screenY}px`;

    const isGrabbing = (currentGesture === "PINCH" || currentGesture === "FIST");

    if (isGrabbing) {
        airPointer.classList.add("is-grabbing");
        if (airPointerIcon) {
            airPointerIcon.innerHTML = (currentGesture === "PINCH") 
                ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.5"><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2"/></svg>` 
                : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f43f5e" stroke-width="2.5"><circle cx="12" cy="12" r="7"/></svg>`;
        }

        if (!grabbedElement) {
            // Dùng elementFromPoint chạy O(1) siêu nhanh
            const hitEl = document.elementFromPoint(screenX, screenY);
            if (hitEl) {
                const token = hitEl.closest(".word-token");
                if (token) {
                    grabbedElement = token;
                    grabbedElement.classList.add("is-grabbed");
                    grabbedElement.style.pointerEvents = "none";
                    playHapticSound("grab");
                }
            }
        } else {
            // Di chuyển thẻ chữ bay theo con trỏ
            grabbedElement.style.position = "fixed";
            grabbedElement.style.left = `${screenX - 45}px`;
            grabbedElement.style.top = `${screenY - 20}px`;
            grabbedElement.style.zIndex = "999999";
            grabbedElement.style.pointerEvents = "none";

            // Kiểm tra hover khay ghép câu
            const hitEl = document.elementFromPoint(screenX, screenY);
            const dropZone = document.getElementById("assembly-drop-zone");
            if (hitEl && hitEl.closest("#assembly-drop-zone")) {
                dropZone.classList.add("air-hover");
            } else {
                dropZone.classList.remove("air-hover");
            }
        }
    } else {
        // Cử chỉ là OPEN
        airPointer.classList.remove("is-grabbing");
        if (airPointerIcon) {
            airPointerIcon.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="2"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v3"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v7"/><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>`;
        }

        if (grabbedElement) {
            releaseGrabbedElement(true, screenX, screenY);
        }
    }
}

function releaseGrabbedElement(checkDropZone = true, dropX = 0, dropY = 0) {
    if (!grabbedElement) return;

    const el = grabbedElement;
    grabbedElement = null;

    const dropZone = document.getElementById("assembly-drop-zone");
    if (dropZone) dropZone.classList.remove("air-hover");

    if (checkDropZone && dropZone) {
        // el đã có pointer-events: none nên elementFromPoint nhìn xuyên thẳng qua nó
        const hitEl = document.elementFromPoint(dropX, dropY);
        if (hitEl && hitEl.closest("#assembly-drop-zone")) {
            dropZone.appendChild(el);
            playHapticSound("drop");
            updateSentenceSubmitButton();
        }
    }

    el.classList.remove("is-grabbed");
    el.style.position = "";
    el.style.left = "";
    el.style.top = "";
    el.style.zIndex = "";
    el.style.pointerEvents = "";
}

/**
 * 4. XỬ LÝ TẢI LÊN ĐA PHƯƠNG TIỆN (ẢNH / VIDEO ≤ 25MB) & KÉO THẢ TỆP
 */
function handleMediaFileUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    processSelectedMediaFile(file);
    event.target.value = "";
}

function handleViewportDragOver(event) {
    event.preventDefault();
    const wrapper = document.getElementById("viewport-wrapper");
    if (wrapper) wrapper.style.border = "2px dashed #38bdf8";
}

function handleViewportDragLeave(event) {
    event.preventDefault();
    const wrapper = document.getElementById("viewport-wrapper");
    if (wrapper) wrapper.style.border = "";
}

function handleViewportDrop(event) {
    event.preventDefault();
    const wrapper = document.getElementById("viewport-wrapper");
    if (wrapper) wrapper.style.border = "";

    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
        const file = event.dataTransfer.files[0];
        processSelectedMediaFile(file);
    }
}

function processSelectedMediaFile(file) {
    const maxSizeBytes = 25 * 1024 * 1024; // 25MB
    if (file.size > maxSizeBytes) {
        const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
        alert(`Dung lượng tệp (${sizeMb} MB) vượt quá giới hạn tối đa 25MB! Vui lòng chọn tệp từ 10MB - 25MB trở xuống.`);
        return;
    }

    const fileName = file.name.toLowerCase();
    const isVideo = file.type.startsWith("video/") || ['.mp4', '.webm', '.mov', '.avi', '.mkv'].some(ext => fileName.endsWith(ext));
    const isImage = file.type.startsWith("image/") || ['.jpg', '.jpeg', '.png', '.webp', '.bmp'].some(ext => fileName.endsWith(ext));

    if (!isVideo && !isImage) {
        alert("Định dạng tệp không được hỗ trợ! Vui lòng tải file ảnh (JPG, PNG, WEBP) hoặc video (MP4, WEBM, MOV).");
        return;
    }

    const objectUrl = URL.createObjectURL(file);
    const mediaBar = document.getElementById("media-mode-bar");
    const mediaLabel = document.getElementById("media-mode-label");
    const scanBtn = document.getElementById("btn-scan-frame");
    const autoScanBtn = document.getElementById("btn-video-autoscan");

    if (mediaBar) mediaBar.style.display = "flex";
    if (scanBtn) scanBtn.disabled = false;

    if (isVideo) {
        activeMediaType = "video";
        if (mediaLabel) mediaLabel.innerHTML = `🎞️ Video: <b>${file.name.slice(0, 18)}...</b> (${(file.size/(1024*1024)).toFixed(1)}MB)`;
        if (uploadedImageElement) uploadedImageElement.style.display = "none";
        if (videoElement) videoElement.style.display = "none";

        if (uploadedVideoElement) {
            uploadedVideoElement.src = objectUrl;
            uploadedVideoElement.style.display = "block";
            uploadedVideoElement.play().catch(e => console.log("Video auto play notice:", e));
        }

        if (autoScanBtn) autoScanBtn.style.display = "inline-flex";
        document.getElementById("status-hud").innerHTML = "🎞️ Đã tải Video. Bấm 'Quét' hoặc 'Quét Video Tự Động'!";

        setTimeout(() => {
            captureAndScan();
        }, 500);

    } else {
        activeMediaType = "image";
        if (mediaLabel) mediaLabel.innerHTML = `🖼️ Ảnh: <b>${file.name.slice(0, 18)}...</b> (${(file.size/(1024*1024)).toFixed(1)}MB)`;
        if (uploadedVideoElement) {
            uploadedVideoElement.pause();
            uploadedVideoElement.style.display = "none";
        }
        if (videoElement) videoElement.style.display = "none";
        if (autoScanBtn) {
            autoScanBtn.style.display = "none";
            stopVideoAutoScan();
        }

        if (uploadedImageElement) {
            uploadedImageElement.src = objectUrl;
            uploadedImageElement.style.display = "block";
            uploadedImageElement.onload = () => {
                document.getElementById("status-hud").innerHTML = "🖼️ Đã nạp ảnh tĩnh. Đang tự động quét...";
                captureAndScan();
            };
        }
    }
}

function closeUploadedMedia() {
    stopVideoAutoScan();
    activeMediaType = "camera";

    if (uploadedVideoElement) {
        uploadedVideoElement.pause();
        uploadedVideoElement.src = "";
        uploadedVideoElement.style.display = "none";
    }
    if (uploadedImageElement) {
        uploadedImageElement.src = "";
        uploadedImageElement.style.display = "none";
    }
    if (videoElement) {
        videoElement.style.display = "block";
    }

    const mediaBar = document.getElementById("media-mode-bar");
    if (mediaBar) mediaBar.style.display = "none";

    const autoScanBtn = document.getElementById("btn-video-autoscan");
    if (autoScanBtn) autoScanBtn.style.display = "none";

    const scanBtn = document.getElementById("btn-scan-frame");
    if (scanBtn) scanBtn.disabled = !isCameraActive;

    document.getElementById("status-hud").innerHTML = isCameraActive ? "🟢 Camera: Đang chạy" : "🔴 Camera: Đang tắt";
}

function toggleVideoAutoScan() {
    if (videoAutoScanInterval) {
        stopVideoAutoScan();
    } else {
        startVideoAutoScan();
    }
}

function startVideoAutoScan() {
    const autoScanBtn = document.getElementById("btn-video-autoscan");
    const icon = document.getElementById("video-autoscan-icon");
    const text = document.getElementById("video-autoscan-text");

    if (autoScanBtn) {
        autoScanBtn.style.background = "linear-gradient(135deg, #f43f5e, #e11d48)";
        autoScanBtn.style.borderColor = "#f43f5e";
    }
    if (icon) icon.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>`;
    if (text) text.innerText = "Dừng Quét Video";

    captureAndScan();
    videoAutoScanInterval = setInterval(() => {
        if (activeMediaType === "video" && uploadedVideoElement && !uploadedVideoElement.paused) {
            captureAndScan();
        }
    }, 2500);
}

function stopVideoAutoScan() {
    if (videoAutoScanInterval) {
        clearInterval(videoAutoScanInterval);
        videoAutoScanInterval = null;
    }
    const autoScanBtn = document.getElementById("btn-video-autoscan");
    const icon = document.getElementById("video-autoscan-icon");
    const text = document.getElementById("video-autoscan-text");

    if (autoScanBtn) {
        autoScanBtn.style.background = "rgba(168, 85, 247, 0.25)";
        autoScanBtn.style.borderColor = "#c084fc";
    }
    if (icon) icon.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="15" x="2" y="7" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>`;
    if (text) text.innerText = "Quét Video Tự Động";
}

/**
 * 5. QUÉT VẬT THỂ & TRÍCH XUẤT BỘ PHẬN CON (OWL-ViT BACKEND)
 */
async function captureAndScan() {
    let sourceMedia = null;
    let isMirrored = false;

    if (activeMediaType === "video" && uploadedVideoElement) {
        sourceMedia = uploadedVideoElement;
    } else if (activeMediaType === "image" && uploadedImageElement) {
        sourceMedia = uploadedImageElement;
    } else if (isCameraActive && videoElement) {
        sourceMedia = videoElement;
        isMirrored = true;
    } else {
        alert("Vui lòng bật camera hoặc tải lên ảnh/video trước khi quét!");
        return;
    }

    const scanBtn = document.getElementById("btn-scan-frame");
    const laser = document.getElementById("scan-laser");
    if (scanBtn) scanBtn.disabled = true;
    if (laser) laser.style.display = "block";
    document.getElementById("status-hud").innerHTML = "🔍 Đang phân tích OWL-ViT...";

    try {
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = 640;
        tempCanvas.height = 360;
        const ctx = tempCanvas.getContext("2d");

        if (isMirrored) {
            ctx.translate(tempCanvas.width, 0);
            ctx.scale(-1, 1);
        }
        ctx.drawImage(sourceMedia, 0, 0, tempCanvas.width, tempCanvas.height);

        const base64Image = tempCanvas.toDataURL("image/jpeg", 0.85);

        const category = document.getElementById("category-select") ? (document.getElementById("category-select").value || null) : null;
        const threshold = parseFloat(document.getElementById("threshold-slider") ? document.getElementById("threshold-slider").value : 0.10) || 0.10;
        const maxResults = parseInt(document.getElementById("max-objects-slider") ? document.getElementById("max-objects-slider").value : 10) || 10;
        const granularity = document.getElementById("granularity-select") ? document.getElementById("granularity-select").value : "all";

        let reticleRoi = null;
        if (isReticleActive && canvasElement && canvasElement.width > 0 && canvasElement.height > 0) {
            const rxRadiusNorm = reticleRadius / canvasElement.width;
            const ryRadiusNorm = reticleRadius / canvasElement.height;
            reticleRoi = [
                Math.max(0, reticleNormPos.x - rxRadiusNorm),
                Math.max(0, reticleNormPos.y - ryRadiusNorm),
                Math.min(1, reticleNormPos.x + rxRadiusNorm),
                Math.min(1, reticleNormPos.y + ryRadiusNorm)
            ];
        }

        const startTime = performance.now();
        const response = await fetch("/api/vision/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: base64Image,
                target_category: category,
                threshold: threshold,
                max_results: maxResults,
                granularity: granularity,
                domain: currentOmniDomain,
                reticle_roi: reticleRoi
            })
        });

        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        document.getElementById("latency-hud").innerText = `⏱️ Suy luận: ${latency} ms`;

        if (data.status === "success") {
            currentDetectedParts = data.detected_parts || [];
            primaryObject = data.primary_object || "object";

            registerDetectedParts(currentDetectedParts, primaryObject);
            updateOmniSceneHud(data.scene_info, data.context_caption, data.domain_breakdown);
            document.getElementById("status-hud").innerHTML = `✅ Phát hiện: <b>${primaryObject}</b> (${currentDetectedParts.length} vật thể/chi tiết)`;

            updateReticleTarget();

            if (!isCameraActive && canvasCtx && canvasElement) {
                canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
                drawDetectedBoundingBoxes();
            }
        } else {
            alert(`Lỗi nhận diện: ${data.message}`);
            document.getElementById("status-hud").innerHTML = "⚠️ Nhận diện thất bại";
        }

    } catch (e) {
        console.error("Lỗi khi quét ảnh:", e);
        alert("Lỗi kết nối tới Server Vision!");
        document.getElementById("status-hud").innerHTML = "❌ Lỗi Server";
    } finally {
        if (laser) laser.style.display = "none";
        if (scanBtn) scanBtn.disabled = false;
    }
}

/**
 * HIỂN THỊ DÒNG PHỤ ĐỀ AR TRONG SUỐT Ở CHÂN CAMERA (KHÔNG CÓ KHUNG CHE VÒNG ĐỎ)
 */
function showArSubtitle(text) {
    const subtitleEl = document.getElementById("camera-ar-subtitle-strip");
    if (!subtitleEl) return;
    subtitleEl.innerText = text;
    subtitleEl.style.display = "block";
    clearTimeout(window._subtitleTimer);
    window._subtitleTimer = setTimeout(() => {
        subtitleEl.style.display = "none";
    }, 4500);
}

/**
 * 4.1 SOI CHI TIẾT VI MÔ (MICRO-FOCUS) BẰNG KÍNH HIỂN VI NGỮ NGHĨA
 * Cắt riêng vùng Vòng đỏ, phóng đại Bicubic lên 224x224 px, cắt tỉa M_sub <= 12 queries
 * và hiển thị nhãn quan hệ [CHA ➔ CON] siêu mượt mà trên CPU <= 30ms.
 */
async function performMicroFocusScan() {
    const microBtn = document.getElementById("btn-micro-focus");
    const statusHud = document.getElementById("status-hud");
    const laser = document.getElementById("scan-laser");

    try {
        if (!canvasElement) return;

        let base64Image = null;
        if (isCameraActive && videoElement) {
            canvasCtx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            base64Image = canvasElement.toDataURL("image/jpeg", 0.85);
        } else {
            base64Image = canvasElement.toDataURL("image/jpeg", 0.9);
        }

        if (!base64Image) {
            alert("Vui lòng Bật Camera hoặc tải ảnh trước khi soi vi mô!");
            return;
        }

        if (laser) laser.style.display = "block";
        if (microBtn) microBtn.disabled = true;
        if (statusHud) statusHud.innerHTML = `🔬 Đang soi vi mô Kính hiển vi ngữ nghĩa...`;

        // Tính toán tọa độ vòng đỏ chuẩn hóa
        const rxRadiusNorm = reticleRadius / canvasElement.width;
        const ryRadiusNorm = reticleRadius / canvasElement.height;
        const reticleRoi = [
            Math.max(0, reticleNormPos.x - rxRadiusNorm),
            Math.max(0, reticleNormPos.y - ryRadiusNorm),
            Math.min(1, reticleNormPos.x + rxRadiusNorm),
            Math.min(1, reticleNormPos.y + ryRadiusNorm)
        ];

        const startTime = performance.now();
        const response = await fetch("/api/vision/micro-focus", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: base64Image,
                reticle_roi: reticleRoi,
                parent_category: primaryObject || "cat",
                mode: "all",
                threshold: 0.08,
                max_results: 6
            })
        });

        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        const latencyHud = document.getElementById("latency-hud");
        if (latencyHud) latencyHud.innerText = `⏱️ Vi mô: ${latency} ms`;

        if (data.status === "success") {
            const microDetections = data.micro_detections || [];
            if (microDetections.length > 0) {
                // Đưa các micro detection vào danh sách phát hiện
                microDetections.forEach(md => {
                    md.normalized_box = md.global_normalized_box;
                    md.is_in_reticle = true;
                    const exists = currentDetectedParts.find(p => p.word && p.word.toLowerCase() === md.word.toLowerCase());
                    if (!exists) {
                        currentDetectedParts.unshift(md);
                    } else {
                        Object.assign(exists, md);
                    }
                });

                registerDetectedParts(microDetections, data.parent_entity);
                renderLiveDetectionStrip();

                // Hiển thị AR Subtitle strip tinh tế ở chân camera (hoàn toàn không có khung che trên vòng đỏ)
                const topItem = microDetections[0];
                showArSubtitle(`${topItem.hierarchy_label} ${topItem.display_relation} • ${topItem.cefr}`);

                if (statusHud) {
                    statusHud.innerHTML = `🔬 Soi thấy <b>${microDetections.length}</b> chi tiết vi mô của <b>${data.parent_vn}</b> (${data.inference_time_ms}ms)!`;
                }

                // Vẽ lại Canvas với Bounding Boxes chi tiết vi mô
                if (!isCameraActive && canvasCtx && canvasElement) {
                    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
                    drawDetectedBoundingBoxes();
                }
            } else {
                if (statusHud) {
                    statusHud.innerHTML = `🔍 Vùng vòng đỏ chưa bắt được chi tiết siêu vi. Hãy thử phóng to hoặc di chuyển vòng đỏ!`;
                }
                showArSubtitle(`[TIÊU ĐIỂM] Hãy di chuyển hoặc phóng to vòng đỏ để ngắm rõ hơn`);
            }
        } else {
            alert(`Lỗi soi vi mô: ${data.message}`);
        }
    } catch (err) {
        console.error("Lỗi khi soi vi mô:", err);
    } finally {
        if (laser) laser.style.display = "none";
        if (microBtn) microBtn.disabled = false;
    }
}

/**
 * 5. THỬ NHANH ẢNH MẪU (PRESET SAMPLES - KHÔNG CẦN WEBCAM)
 */
async function loadSamplePreset(type) {
    const scanBtn = document.getElementById("btn-scan-frame");
    const laser = document.getElementById("scan-laser");
    if (laser) laser.style.display = "block";
    document.getElementById("status-hud").innerHTML = `🧪 Đang nạp ảnh mẫu ${type.toUpperCase()}...`;

    // Sinh ảnh mockup trực tiếp bằng HTML5 Canvas
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = 640;
    tempCanvas.height = 480;
    const ctx = tempCanvas.getContext("2d");

    // Nền trung tính
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(0, 0, 640, 480);

    if (type === "backpack") {
        // Thân balo
        ctx.fillStyle = "#1e3a8a";
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 4;
        ctx.fillRect(160, 60, 320, 360);
        ctx.strokeRect(160, 60, 320, 360);

        // Quai đeo
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(180, 80, 40, 300);
        ctx.fillRect(420, 80, 40, 300);

        // Khóa kéo
        ctx.strokeStyle = "#e2e8f0";
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(320, 100);
        ctx.lineTo(320, 340);
        ctx.stroke();

        ctx.fillStyle = "#eab308";
        ctx.fillRect(310, 180, 20, 30);
    } else if (type === "laptop") {
        // Màn hình laptop
        ctx.fillStyle = "#0f172a";
        ctx.strokeStyle = "#94a3b8";
        ctx.lineWidth = 3;
        ctx.fillRect(170, 70, 300, 200);
        ctx.strokeRect(170, 70, 300, 200);

        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(185, 85, 270, 170);

        // Bàn phím & Trackpad
        ctx.fillStyle = "#334155";
        ctx.fillRect(130, 270, 380, 140);

        ctx.fillStyle = "#1e293b";
        ctx.fillRect(180, 285, 280, 60); // Bàn phím
        ctx.fillRect(270, 355, 100, 45); // Trackpad
    } else if (type === "glasses") {
        // Kính mắt
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 5;
        // Tròng kính trái & phải
        ctx.fillStyle = "rgba(56, 189, 248, 0.25)";
        ctx.fillRect(160, 180, 130, 100);
        ctx.strokeRect(160, 180, 130, 100);
        ctx.fillRect(350, 180, 130, 100);
        ctx.strokeRect(350, 180, 130, 100);
        // Cầu nối kính
        ctx.beginPath();
        ctx.moveTo(290, 220);
        ctx.lineTo(350, 220);
        ctx.stroke();
        // Càng kính hai bên
        ctx.beginPath();
        ctx.moveTo(160, 200);
        ctx.lineTo(80, 170);
        ctx.moveTo(480, 200);
        ctx.lineTo(560, 170);
        ctx.stroke();
    } else if (type === "phone") {
        // Điện thoại thông minh
        ctx.fillStyle = "#0f172a";
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 4;
        ctx.fillRect(230, 70, 180, 340);
        ctx.strokeRect(230, 70, 180, 340);
        // Màn hình
        ctx.fillStyle = "#1e3a8a";
        ctx.fillRect(245, 110, 150, 250);
        // Camera tròn
        ctx.fillStyle = "#e2e8f0";
        ctx.beginPath();
        ctx.arc(320, 90, 6, 0, 2 * Math.PI);
        ctx.fill();
    } else {
        // Áo sơ mi
        ctx.fillStyle = "#f8fafc";
        ctx.fillRect(200, 80, 240, 340);

        // Cổ áo
        ctx.fillStyle = "#cbd5e1";
        ctx.beginPath();
        ctx.moveTo(200, 80);
        ctx.lineTo(320, 150);
        ctx.lineTo(440, 80);
        ctx.fill();

        // Cúc áo
        ctx.fillStyle = "#475569";
        for (let y = 170; y <= 370; y += 50) {
            ctx.beginPath();
            ctx.arc(320, y, 7, 0, 2 * Math.PI);
            ctx.fill();
        }
    }

    const base64Image = tempCanvas.toDataURL("image/jpeg", 0.85);

    try {
        const startTime = performance.now();
        const granularity = document.getElementById("granularity-select") ? document.getElementById("granularity-select").value : "all";
        const maxResults = parseInt(document.getElementById("max-objects-slider") ? document.getElementById("max-objects-slider").value : 10) || 10;

        const response = await fetch("/api/vision/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: base64Image,
                target_category: type,
                threshold: 0.08,
                max_results: maxResults,
                granularity: granularity,
                domain: currentOmniDomain
            })
        });

        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        document.getElementById("latency-hud").innerText = `⏱️ Suy luận: ${latency} ms`;

        if (data.status === "success") {
            currentDetectedParts = data.detected_parts || [];
            primaryObject = data.primary_object || type;

            registerDetectedParts(currentDetectedParts, primaryObject);
            updateOmniSceneHud(data.scene_info, data.context_caption, data.domain_breakdown);
            document.getElementById("status-hud").innerHTML = `✅ Phát hiện: <b>${primaryObject.toUpperCase()}</b> (${currentDetectedParts.length} chi tiết)`;

            updateReticleTarget();

            // Nếu camera đang tắt, vẽ ảnh mockup lên canvas
            if (!isCameraActive && canvasCtx && canvasElement) {
                canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
                canvasCtx.drawImage(tempCanvas, 0, 0, canvasElement.width, canvasElement.height);
                drawDetectedBoundingBoxes();
            }
        }
    } catch (e) {
        console.error("Lỗi scan mockup:", e);
    } finally {
        if (laser) laser.style.display = "none";
    }
}

/**
 * 6. VẼ BOUNDING BOX TRÊN CANVAS
 */
function drawDetectedBoundingBoxes() {
    if (!currentDetectedParts || currentDetectedParts.length === 0 || !canvasCtx || !canvasElement) return;

    const w = canvasElement.width;
    const h = canvasElement.height;

    // Nếu camera tắt (đang xem ảnh/video tĩnh), vẽ đè rõ nét
    if (!isCameraActive && activeMediaType !== "camera") {
        canvasCtx.clearRect(0, 0, w, h);
    }

    currentDetectedParts.forEach((part) => {
        const box = part.normalized_box;
        if (!box) return;

        const x1 = box.xmin * w;
        const y1 = box.ymin * h;
        const boxW = (box.xmax - box.xmin) * w;
        const boxH = (box.ymax - box.ymin) * h;

        const isReticleTarget = currentReticleWord && (part.word && currentReticleWord.word && part.word.toLowerCase() === currentReticleWord.word.toLowerCase());
        const isBasic = (part.level_tier === "basic" || ["A1", "A2"].includes((part.cefr || "").toUpperCase()));
        
        let themeColor = "#22d3ee";
        if (part.domain === "creatures") themeColor = "#4ade80";
        else if (part.domain === "scenes") themeColor = "#fbbf24";
        else if (part.domain === "environment") themeColor = "#c084fc";
        else if (!isBasic) themeColor = "#38bdf8";

        let shadowColor = themeColor;
        let lineWidth = 2.5;

        if (isReticleTarget) {
            themeColor = "#f43f5e"; // Đỏ neon ăn khớp đồng bộ với Vòng đỏ
            shadowColor = "rgba(244, 63, 94, 0.95)";
            lineWidth = 3.5;
        }

        canvasCtx.save();
        canvasCtx.lineWidth = lineWidth;
        canvasCtx.strokeStyle = themeColor;
        canvasCtx.fillStyle = isReticleTarget ? "rgba(244, 63, 94, 0.22)" : "rgba(15, 23, 42, 0.25)";
        canvasCtx.shadowBlur = isReticleTarget ? 18 : 10;
        canvasCtx.shadowColor = shadowColor;

        // Vẽ hộp bao quanh vật thể
        canvasCtx.fillRect(x1, y1, boxW, boxH);
        canvasCtx.strokeRect(x1, y1, boxW, boxH);

        // Chuẩn bị nhãn song ngữ: [DOMAIN] EN [CEFR] (conf%) và Tiếng Việt chuẩn xác
        const enWord = (part.word || "").toUpperCase();
        const cefr = part.cefr || "B1";
        const vnMeaning = part.meaning || "";
        const confPercent = Math.round((part.confidence || 0) * 100);
        const domainShort = (part.domain || "obj").slice(0, 3).toUpperCase();

        const line1 = `[${domainShort}] ${enWord} [${cefr}] (${confPercent}%)`;
        const line2 = vnMeaning ? `🇻🇳 ${vnMeaning}` : "";

        canvasCtx.font = "bold 11px Inter, sans-serif";
        const w1 = canvasCtx.measureText(line1).width;
        canvasCtx.font = "normal 11px Inter, sans-serif";
        const w2 = canvasCtx.measureText(line2).width;
        const badgeW = Math.max(w1, w2) + 14;
        const badgeH = line2 ? 34 : 20;
        const badgeY = Math.max(0, y1 - badgeH - 3);

        // Nền nhãn kính mờ Cyberpunk tương phản cao
        canvasCtx.fillStyle = "rgba(2, 6, 23, 0.92)";
        canvasCtx.fillRect(x1, badgeY, badgeW, badgeH);
        canvasCtx.strokeStyle = themeColor;
        canvasCtx.lineWidth = 1;
        canvasCtx.strokeRect(x1, badgeY, badgeW, badgeH);

        // Dòng 1: Miền + Tiếng Anh + Cấp độ CEFR + Độ tin cậy
        canvasCtx.fillStyle = themeColor;
        canvasCtx.font = "bold 11px Inter, sans-serif";
        canvasCtx.fillText(line1, x1 + 6, badgeY + 13);

        // Dòng 2: Bản dịch tiếng Việt chuẩn xác
        if (line2) {
            canvasCtx.fillStyle = "#fef08a"; // Màu vàng hổ phách nổi bật
            canvasCtx.font = "bold 10.5px Inter, sans-serif";
            canvasCtx.fillText(line2, x1 + 6, badgeY + 27);
        }

        canvasCtx.restore();
    });
}

/**
 * 7. QUẢN LÝ KHO TỪ VỰNG THỊ GIÁC, BỘ LỌC ĐỒ VẬT & CẤP ĐỘ CEFR
 */

function registerDetectedParts(parts, objectCategory) {
    if (!parts) return;
    primaryObject = objectCategory || primaryObject || "object";

    // 1. Nạp các từ chi tiết bộ phận vật thể (Loại bỏ trùng lặp)
    parts.forEach(part => {
        const cleanWord = (part.word || "").trim().toLowerCase();
        if (!cleanWord) return;
        const existingIdx = scannedWordRegistry.findIndex(w => w.word.toLowerCase() === cleanWord);
        const cefrUpper = (part.cefr || "B1").toUpperCase();
        const levelTier = part.level_tier || (["A1", "A2"].includes(cefrUpper) ? "basic" : "advanced");

        const item = {
            word: cleanWord,
            ipa: part.ipa || "",
            cefr: cefrUpper,
            meaning: part.meaning || "Chi tiết vật thể",
            tier: part.tier || "functional",
            domain: part.domain || "objects",
            levelTier: levelTier,
            isLearned: !!part.is_learned,
            parentObject: objectCategory || primaryObject,
            isObjectPart: true
        };
        if (existingIdx >= 0) {
            scannedWordRegistry[existingIdx] = item;
        } else {
            scannedWordRegistry.push(item);
        }
    });

    // 2. Nạp các từ nối cơ bản phục vụ đặt câu (Chỉ nạp 1 lần duy nhất)
    const baseConnectors = [
        { word: "the", ipa: "/ðə/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Mạo từ xác định", isLearned: true, isObjectPart: false },
        { word: "is", ipa: "/ɪz/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Thì / là", isLearned: true, isObjectPart: false },
        { word: "a", ipa: "/ə/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Một", isLearned: true, isObjectPart: false },
        { word: "has", ipa: "/hæz/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Có", isLearned: true, isObjectPart: false },
        { word: "my", ipa: "/maɪ/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Của tôi", isLearned: true, isObjectPart: false },
        { word: "of", ipa: "/əv/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Của", isLearned: true, isObjectPart: false },
        { word: "this", ipa: "/ðɪs/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Cái này", isLearned: true, isObjectPart: false },
        { word: "in", ipa: "/ɪn/", cefr: "A1", levelTier: "basic", domain: "connectors", meaning: "Ở trong", isLearned: true, isObjectPart: false },
        { word: "near", ipa: "/nɪər/", cefr: "A2", levelTier: "basic", domain: "connectors", meaning: "Gần", isLearned: true, isObjectPart: false },
        { word: "under", ipa: "/ˈʌndər/", cefr: "A2", levelTier: "basic", domain: "connectors", meaning: "Dưới", isLearned: true, isObjectPart: false },
        { word: "because", ipa: "/bɪˈkɒz/", cefr: "B1", levelTier: "advanced", domain: "connectors", meaning: "Bởi vì", isLearned: true, isObjectPart: false },
        { word: "which", ipa: "/wɪtʃ/", cefr: "B1", levelTier: "advanced", domain: "connectors", meaning: "Mà / cái mà", isLearned: true, isObjectPart: false },
        { word: "peaceful", ipa: "/ˈpiːsfəl/", cefr: "B1", levelTier: "advanced", domain: "connectors", meaning: "Thanh bình", isLearned: true, isObjectPart: false },
        { word: "bright", ipa: "/braɪt/", cefr: "A2", levelTier: "basic", domain: "connectors", meaning: "Tươi sáng", isLearned: true, isObjectPart: false },
        { word: "cozy", ipa: "/ˈkəʊzi/", cefr: "B1", levelTier: "advanced", domain: "connectors", meaning: "Ấm cúng", isLearned: true, isObjectPart: false },
        { word: "beautiful", ipa: "/ˈbjuːtɪfəl/", cefr: "A2", levelTier: "basic", domain: "connectors", meaning: "Đẹp đẽ", isLearned: true, isObjectPart: false }
    ];

    baseConnectors.forEach(conn => {
        if (!scannedWordRegistry.some(w => w.word.toLowerCase() === conn.word.toLowerCase())) {
            scannedWordRegistry.push(conn);
        }
    });

    updateObjectCategoryDropdown();
    renderWordPool();
    renderLiveDetectionStrip();
    updateWorkspaceBadges();
    renderVaultCards();
}

function setWordFilter(filterType) {
    currentWordFilter = filterType;
    ["all", "objects", "creatures", "scenes", "environment", "connectors"].forEach(type => {
        const btn = document.getElementById(`filter-${type}-btn`);
        if (btn) btn.classList.toggle("active", type === filterType);
    });
    renderWordPool();
}

function setWordLevelFilter(levelTier) {
    currentLevelFilter = levelTier;
    ["all", "basic", "advanced"].forEach(lvl => {
        const btn = document.getElementById(`level-${lvl}-btn`);
        if (btn) btn.classList.toggle("active", lvl === levelTier);
    });
    renderWordPool();
}

function filterBySpecificObject(category) {
    selectedObjectCategory = category;
    renderWordPool();
}

function updateObjectCategoryDropdown() {
    const select = document.getElementById("pool-object-select");
    const wrapper = document.getElementById("object-category-filter-wrapper");
    if (!select || !wrapper) return;

    // Lấy danh sách các vật thể cha duy nhất
    const objects = [...new Set(scannedWordRegistry.filter(w => w.isObjectPart && w.parentObject).map(w => w.parentObject))];

    if (objects.length > 0) {
        wrapper.style.display = "flex";
        const currentVal = select.value;
        select.innerHTML = `<option value="all">Mọi vật thể (${objects.length})</option>`;
        objects.forEach(obj => {
            const opt = document.createElement("option");
            opt.value = obj;
            opt.innerText = obj.charAt(0).toUpperCase() + obj.slice(1);
            select.appendChild(opt);
        });
        if (objects.includes(currentVal)) {
            select.value = currentVal;
        }
    } else {
        wrapper.style.display = "none";
    }
}

function clearScannedWordPool() {
    scannedWordRegistry = [];
    currentDetectedParts = [];
    primaryObject = "object";

    renderWordPool();
    updateObjectCategoryDropdown();
    renderLiveDetectionStrip();
    updateWorkspaceBadges();
    renderVaultCards();

    if (canvasCtx && canvasElement) {
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }

    const statusHud = document.getElementById("status-hud");
    if (statusHud) {
        statusHud.innerHTML = "🗑️ Kho từ vựng đã được làm sạch";
    }

    playHapticSound("drop");
}

function renderWordPool() {
    const pool = document.getElementById("word-pool");
    const countBadge = document.getElementById("word-count-badge");
    if (!pool || !countBadge) return;

    pool.innerHTML = "";

    if (scannedWordRegistry.length === 0) {
        pool.innerHTML = `<div style="color: #64748b; font-style: italic; font-size: 13px; margin: auto;">Kho từ đang trống. Bấm "Bật Camera", click vào một "Ảnh mẫu", hoặc tải ảnh/video để nạp từ vựng...</div>`;
        countBadge.innerText = "0 từ vựng";
        return;
    }

    // Lọc đồng thời theo:
    // 1. Phân loại (Tất cả / Đồ vật / Sinh vật / Khung cảnh / Môi trường / Chỉ từ nối)
    // 2. Vật thể cha cụ thể
    // 3. Cấp độ học tập (Tất cả / Cơ bản A1-A2 / Chuyên sâu B1-C1)
    const filteredList = scannedWordRegistry.filter(item => {
        if (currentWordFilter === "objects" && (item.domain !== "objects" || !item.isObjectPart)) return false;
        if (currentWordFilter === "creatures" && (item.domain !== "creatures" || !item.isObjectPart)) return false;
        if (currentWordFilter === "scenes" && (item.domain !== "scenes" || !item.isObjectPart)) return false;
        if (currentWordFilter === "environment" && (item.domain !== "environment" || !item.isObjectPart)) return false;
        if (currentWordFilter === "connectors" && item.isObjectPart) return false;
        if (selectedObjectCategory !== "all" && item.isObjectPart) {
            if (item.parentObject !== selectedObjectCategory) return false;
        }
        if (currentLevelFilter === "basic" && item.levelTier !== "basic") return false;
        if (currentLevelFilter === "advanced" && item.levelTier !== "advanced") return false;
        return true;
    });

    if (filteredList.length === 0) {
        pool.innerHTML = `<div style="color: #64748b; font-style: italic; font-size: 13px; margin: auto;">Không có từ nào thỏa mãn bộ lọc hiện tại. Hãy bấm chọn "🌟 Mọi Cấp Độ" hoặc quét thêm vật thể!</div>`;
        countBadge.innerText = `${scannedWordRegistry.filter(w => w.isObjectPart).length} từ (đang ẩn)`;
        return;
    }

    const objectPartsCount = scannedWordRegistry.filter(w => w.isObjectPart).length;
    countBadge.innerText = `${objectPartsCount} từ thực thể (${filteredList.length} hiển thị)`;

    filteredList.forEach(item => {
        const token = createWordTokenElement(
            item.word,
            item.ipa,
            item.cefr,
            item.meaning,
            item.isLearned,
            item.isObjectPart,
            item.levelTier,
            item.domain || "objects"
        );
        pool.appendChild(token);
    });
}

function createWordTokenElement(word, ipa, cefr, meaning, isLearned, isObjectPart = true, levelTier = 'basic', domain = 'objects') {
    const token = document.createElement("div");
    token.className = "word-token token-domain-" + (domain || 'objects');
    token.setAttribute("draggable", "true");
    token.setAttribute("data-word", word);
    token.setAttribute("title", meaning ? `${word}: ${meaning}` : word);

    let badgeStyle = "";
    if (!isObjectPart) {
        badgeStyle = 'background: rgba(148, 163, 184, 0.2); color: #cbd5e1;';
    } else if (levelTier === "advanced" || ["B1", "B2", "C1"].includes((cefr || "").toUpperCase())) {
        badgeStyle = 'background: rgba(168, 85, 247, 0.25); color: #c084fc; border: 1px solid #c084fc;';
    } else {
        badgeStyle = 'background: rgba(34, 211, 238, 0.25); color: #67e8f9; border: 1px solid #67e8f9;';
    }

    const domainBadge = (isObjectPart && domain) ? `<span class="domain-tag ${domain}">${domain.toUpperCase()}</span>` : '';

    token.innerHTML = `
        ${domainBadge}
        <span class="cefr-badge" style="${badgeStyle}">${cefr || 'A1'}</span>
        <span style="font-weight: 700; color: #fff;">${word}</span>
        ${ipa ? `<span class="word-ipa">${ipa}</span>` : ''}
        ${meaning && isObjectPart ? `<span style="font-size: 11px; color: #fef08a; margin-left: 2px;">(${meaning})</span>` : ''}
        <button type="button" style="background: none; border: none; cursor: pointer; color: #38bdf8; padding: 0 4px; display: inline-flex; align-items: center;" onclick="speakWord('${word}', event)" title="Nghe phát âm">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        </button>
        ${(isObjectPart && !isLearned) ? `<button type="button" class="btn-add-vocab" onclick="collectVocab('${word}', event)" title="Lưu vào kho ôn tập SRS">+ Thu thập</button>` : ''}
    `;

    // Hỗ trợ click chuột để chuyển nhanh qua lại giữa Kho từ và Khay ghép câu
    token.addEventListener("click", (e) => {
        if (e.target.closest("button")) return; // Bỏ qua nếu click nút nghe phát âm hoặc thu thập
        const dropZone = document.getElementById("assembly-drop-zone");
        const pool = document.getElementById("word-pool");
        if (token.parentElement === dropZone) {
            pool.appendChild(token);
        } else {
            dropZone.appendChild(token);
        }
        playHapticSound("drop");
        updateSentenceSubmitButton();
    });

    // Sự kiện kéo thả chuột truyền thống HTML5
    token.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", word);
        token.classList.add("is-grabbed");
    });

    token.addEventListener("dragend", () => {
        token.classList.remove("is-grabbed");
    });

    return token;
}

/**
 * 8. CÔNG CỤ HỖ TRỢ ĐẶT CÂU & GHÉP CÂU MẪU TỰ ĐỘNG
 */
function autoAssembleSentence() {
    const dropZone = document.getElementById("assembly-drop-zone");
    if (!dropZone) return;

    const objectParts = scannedWordRegistry.filter(w => w.isObjectPart);
    if (objectParts.length === 0) {
        alert("Kho từ chưa có từ vựng vật thể nào để ghép câu! Hãy bấm nạp ảnh mẫu hoặc bật camera trước.");
        return;
    }

    const targetPart = objectParts[0].word;
    const parentObj = (primaryObject && primaryObject !== "object") ? primaryObject : (objectParts[0].parentObject || "item");

    let sentenceWords = [];
    if (objectParts.length >= 2) {
        sentenceWords = ["my", parentObj, "has", "a", targetPart, "and", "a", objectParts[1].word];
    } else {
        sentenceWords = ["the", targetPart, "of", "my", parentObj, "is", "broken"];
    }

    dropZone.innerHTML = "";
    sentenceWords.forEach(w => {
        const token = createWordTokenElement(w, "", "A1", "", true, false);
        dropZone.appendChild(token);
    });

    playHapticSound("drop");
    updateSentenceSubmitButton();

    const statusHud = document.getElementById("status-hud");
    if (statusHud) {
        statusHud.innerHTML = `Đã tự động ghép câu: "<b>${sentenceWords.join(" ")}</b>"`;
    }
}

function applySentenceTemplate(templateKey) {
    if (!templateKey) return;
    const dropZone = document.getElementById("assembly-drop-zone");
    const select = document.getElementById("sentence-template-select");

    const objectParts = scannedWordRegistry.filter(w => w.isObjectPart && (w.domain === "objects" || !w.domain));
    const creatures = scannedWordRegistry.filter(w => w.isObjectPart && w.domain === "creatures");
    const scenes = scannedWordRegistry.filter(w => w.isObjectPart && w.domain === "scenes");
    const environments = scannedWordRegistry.filter(w => w.isObjectPart && w.domain === "environment");

    const targetPart = objectParts.length > 0 ? objectParts[0].word : "part";
    const parentObj = (primaryObject && primaryObject !== "object") ? primaryObject : (objectParts.length > 0 ? (objectParts[0].parentObject || "object") : "object");
    const creatureWord = creatures.length > 0 ? creatures[0].word : "cat";
    const sceneWord = scenes.length > 0 ? scenes[0].word : "room";
    const envWord = environments.length > 0 ? environments[0].word : "sunlight";

    let words = [];
    switch (templateKey) {
        case "scene_atmosphere":
            words = ["the", "atmosphere", "in", "this", sceneWord, "is", "remarkably", "peaceful"];
            break;
        case "creature_object":
            words = ["a", creatureWord, "is", "resting", "near", "the", parentObj, "in", "the", sceneWord];
            break;
        case "weather_environment":
            words = ["because", "it", "is", "bright", "today", "the", sceneWord, "looks", "beautiful"];
            break;
        case "complex_relative":
            words = ["the", parentObj, "which", "is", "situated", "inside", "the", sceneWord, "is", "very", "cozy"];
            break;
        case "part_is_adj":
            words = ["the", targetPart, "of", "my", parentObj, "is", "broken"];
            break;
        case "obj_has_part":
            words = ["this", parentObj, "has", "a", targetPart];
            break;
        case "my_obj_part":
            words = ["my", parentObj, "has", "a", "good", targetPart];
            break;
        case "i_need_obj":
            words = ["i", "use", "the", parentObj, "with", "the", targetPart];
            break;
        default:
            words = ["the", targetPart, "is", "clean"];
    }

    dropZone.innerHTML = "";
    words.forEach(w => {
        const token = createWordTokenElement(w, "", "A1", "", true, false);
        dropZone.appendChild(token);
    });

    playHapticSound("drop");
    updateSentenceSubmitButton();
    if (select) select.value = "";
}

function insertQuickWord(word) {
    const dropZone = document.getElementById("assembly-drop-zone");
    if (!dropZone) return;
    const token = createWordTokenElement(word, "", "A1", "", true, false);
    dropZone.appendChild(token);
    playHapticSound("drop");
    updateSentenceSubmitButton();
}

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

    const token = document.querySelector(`.word-token[data-word="${word}"]`);
    if (token) {
        dropZone.appendChild(token);
        playHapticSound("drop");
        updateSentenceSubmitButton();
    }
}

/**
 * 8. THU THẬP TỪ VỰNG VÀO KHO ÔN TẬP SRS
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
            if (event && event.target) {
                event.target.outerHTML = `<span style="font-size: 10px; color: #4ade80;">✓ Đã lưu</span>`;
            }
            const item = scannedWordRegistry.find(w => w.word.toLowerCase() === word.toLowerCase());
            if (item) item.isLearned = true;
            updateWorkspaceBadges();
            renderVaultCards();
        } else {
            alert(`Thông báo: ${data.message}`);
        }
    } catch (e) {
        console.error("Lỗi khi lưu từ vựng:", e);
        alert("Lỗi kết nối tới kho dữ liệu từ vựng!");
    }
}

/**
 * 9. CHẤM ĐIỂM CÂU VĂN GHÉP ĐƯỢC (GEC ENGINE & CRITIQUE SYNTHESIZER)
 */
function updateSentenceSubmitButton() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const words = dropZone ? dropZone.querySelectorAll(".word-token") : [];
    const submitBtn = document.getElementById("btn-submit-sentence");
    if (submitBtn) {
        submitBtn.disabled = (words.length === 0);
    }
    updateWorkspaceBadges();

    // Đồng bộ hiển thị phụ đề AR nổi nhẹ trong lòng camera (không có khung viền hộp)
    const subStrip = document.getElementById("camera-ar-subtitle-strip");
    if (subStrip) {
        if (words.length > 0) {
            const sentenceText = Array.from(words).map(t => t.getAttribute("data-word")).join(" ");
            subStrip.innerText = sentenceText;
            subStrip.style.display = "block";
        } else {
            subStrip.innerText = "";
            subStrip.style.display = "none";
        }
    }
}

function clearSentence() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const pool = document.getElementById("word-pool");
    const tokens = Array.from(dropZone ? dropZone.querySelectorAll(".word-token") : []);
    tokens.forEach(t => {
        if (pool) pool.appendChild(t);
        else t.remove();
    });
    updateSentenceSubmitButton();

    const subStrip = document.getElementById("camera-ar-subtitle-strip");
    if (subStrip) {
        subStrip.innerText = "";
        subStrip.style.display = "none";
    }

    const fbDeck = document.getElementById("feedback-deck");
    if (fbDeck) fbDeck.style.display = "none";
    const arModal = document.getElementById("ar-feedback-modal");
    if (arModal) arModal.style.display = "none";
}

function addCustomWordPrompt() {
    const customWord = prompt("Nhập từ tiếng Anh bạn muốn thêm vào khay (ví dụ: 'broken', 'clean', 'old'):");
    if (customWord && customWord.trim()) {
        const pool = document.getElementById("word-pool");
        const token = createWordTokenElement(customWord.trim().toLowerCase(), "", "A2", "Tự bổ sung", true);
        if (pool) pool.appendChild(token);
    }
}

async function submitSentence() {
    const dropZone = document.getElementById("assembly-drop-zone");
    const tokens = dropZone ? dropZone.querySelectorAll(".word-token") : [];
    if (tokens.length === 0) return;

    const words = Array.from(tokens).map(t => t.getAttribute("data-word"));
    const sentence = words.join(" ");

    const submitBtn = document.getElementById("btn-submit-sentence");
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> <span>Đang chấm điểm...</span>`;
    }

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
            // Hiển thị AR Modal nếu cần
            const arModal = document.getElementById("ar-feedback-modal");
            if (arModal) {
                arModal.style.display = "block";
            }

            // Đồng thời hiển thị feedback deck bên dưới khay ghép câu
            const feedbackDeck = document.getElementById("feedback-deck");
            if (feedbackDeck) {
                feedbackDeck.style.display = "block";
                feedbackDeck.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }

            // Đồng bộ dữ liệu hiển thị vào tất cả các phần tử kết quả tương ứng
            document.querySelectorAll("#score-badge, #score-badge-deck").forEach(el => {
                el.innerText = `Điểm: ${data.score}/100`;
            });
            document.querySelectorAll("#result-original, #deck-result-original").forEach(el => {
                el.innerText = data.original_sentence || sentence;
            });
            document.querySelectorAll("#result-corrected, #deck-result-corrected").forEach(el => {
                el.innerText = data.corrected_sentence || sentence;
            });
            document.querySelectorAll("#result-critique, #deck-result-critique").forEach(el => {
                el.innerText = data.feedback || "Cấu trúc câu rất tốt!";
            });
            document.querySelectorAll("#result-exp, #deck-result-exp").forEach(el => {
                el.innerHTML = `<span style="display: inline-flex; align-items: center; gap: 4px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="#fbbf24" stroke="#f59e0b" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> +${data.exp_awarded || 50} EXP đã được cộng vào tài khoản!</span>`;
            });

            playHapticSound("grab");
        } else {
            alert(`Lỗi khi chấm câu: ${data.message}`);
        }
    } catch (e) {
        console.error("Lỗi submit câu:", e);
        alert("Lỗi khi kết nối tới engine chấm câu!");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg> <span>Chấm Điểm & Phân Tích Ngữ Pháp</span>`;
        }
    }
}

function speakWord(word, event) {
    if (event) event.stopPropagation();
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel(); // Triệt tiêu lỗi nghẽn TTS của Chrome
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.lang = "en-US";
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }
}

let sharedAudioCtx = null;
function getAudioContext() {
    if (!sharedAudioCtx) {
        const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
        if (AudioCtxClass) {
            sharedAudioCtx = new AudioCtxClass();
        }
    }
    if (sharedAudioCtx && sharedAudioCtx.state === 'suspended') {
        sharedAudioCtx.resume().catch(() => {});
    }
    return sharedAudioCtx;
}

function playHapticSound(type) {
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === "grab") {
            osc.frequency.setValueAtTime(440, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.08);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
            osc.start();
            osc.stop(ctx.currentTime + 0.08);
        } else {
            osc.frequency.setValueAtTime(660, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(330, ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.09, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
            osc.start();
            osc.stop(ctx.currentTime + 0.1);
        }
    } catch (e) {
        // Audio context bị chặn bởi browser policy khi chưa click
    }
}

function resetArena() {
    clearScannedWordPool();
    clearSentence();
}
