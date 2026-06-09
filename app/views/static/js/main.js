// Khép kín hệ thống Auth Portal: Chặn quyền truy cập Dashboard trái phép từ đầu
if (!localStorage.getItem("user_id") || !localStorage.getItem("username")) {
    alert("CẢNH BÁO TRUY CẬP: Bạn chưa đăng nhập hệ thống! Đang quay lại Portal...");
    window.location.href = '/auth';
}

// Quản lý trạng thái phiên làm việc động từ LocalStorage
const CURRENT_USER_ID = localStorage.getItem("user_id") || 1;
const CURRENT_USERNAME = localStorage.getItem("username") || "Explorer";

// Biến toàn cục lưu trữ tính năng hiện tại người dùng đang chọn
let activeFeature = "grammar";

document.addEventListener("DOMContentLoaded", () => {
    // Cập nhật tên người chơi thực tế lên giao diện chính
    const nameSpan = document.querySelector("#status-card .pixel-text span");
    if (nameSpan) nameSpan.textContent = CURRENT_USERNAME;

    // Tải trước danh sách nhiệm vụ từ vựng ở cột trái
    loadVocabQuests();

    // Lắng nghe sự kiện gõ phím nhanh trong ô nhập lệnh
    initKeyboardShortcuts();

    // Tải thư viện Lottie động để chuẩn bị hiệu ứng nổ pháo hoa pixel
    initLottieLibrary();
});

function switchFeature(featureName) {
    const currentPath = window.location.pathname;

    // 1. KIỂM TRA ĐIỀU HƯỚNG TỪ DASHBOARD
    // Nếu đang không ở trang học (/learn) mà click vào grammar/vocab -> Chuyển trang
    if ((featureName === 'grammar' || featureName === 'vocab') && currentPath !== '/learn') {
        localStorage.setItem("selected_learning_mode", featureName);
        window.location.href = '/learn';
        return; // Dừng lại để trình duyệt load trang mới
    }

    // Nếu click vào mini-game mà chưa ở trang /test -> Chuyển trang
    if (featureName === 'game' && currentPath !== '/test') {
        window.location.href = '/test';
        return;
    }

    // 2. RENDER GIAO DIỆN (Chỉ chạy khi ĐÃ Ở ĐÚNG TRANG hoặc dùng cho tính năng Story tại Dashboard)
    activeFeature = featureName;
    const workspace = document.getElementById("dynamic-workspace");
    const aiResponseBox = document.getElementById("aiResponseBox");

    // Xóa hiệu ứng chọn cũ trên Bento Grid (Chỉ có tác dụng nếu đang ở Dashboard)
    document.querySelectorAll(".bento-card").forEach(card => card.style.borderColor = "var(--glass-border)");
    const activeCard = document.getElementById(`${featureName}-card`);
    if (activeCard) activeCard.style.borderColor = "var(--neon-cyan)";

    // Nếu không tìm thấy không gian làm việc thì thoát luôn (tránh lỗi)
    if (!workspace) return;

    // Ẩn hộp thoại AI khi mới đổi chế độ
    if (aiResponseBox) aiResponseBox.style.display = "none";

    // Bắt đầu vẽ khung nhập liệu tùy theo chế độ
    switch (featureName) {
        case 'vocab':
            workspace.innerHTML = `
                <div class="pixel-text" style="font-size: 15px; margin-bottom: 12px;">
                    NHIỆM VỤ TỪ VỰNG: Đặt một câu có nghĩa chứa từ lóng/từ vựng hệ thống yêu cầu.
                </div>
                <textarea id="userInput" style="width: 100%; height: 75px; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 17px; border-radius: 8px; resize: none; box-sizing: border-box;" placeholder="Master G đang đợi câu từ vựng của bạn..."></textarea>
                <div style="margin-top: 10px; display: flex; gap: 12px;">
                    <button class="pixel-btn" onclick="submitChallenge()">SEND_VOCAB</button>
                </div>
            `;
            break;

        case 'grammar':
            workspace.innerHTML = `
                <div class="pixel-text" style="font-size: 15px; margin-bottom: 12px;">
                    NHIỆM VỤ NGỮ PHÁP: Sử dụng đúng cấu trúc ngữ pháp để vượt ải.
                </div>
                <textarea id="userInput" style="width: 100%; height: 75px; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 17px; border-radius: 8px; resize: none; box-sizing: border-box;" placeholder="Nhập câu ngữ pháp tại đây..."></textarea>
                <div style="margin-top: 10px; display: flex; gap: 12px;">
                    <button class="pixel-btn" onclick="submitChallenge()">SEND_COMMAND</button>
                </div>
            `;
            break;

        case 'story':
            // Tính năng nhập vai RPG ngay tại màn hình Dashboard
            const battleTitle = document.querySelector("#battle-card .pixel-title");
            if(battleTitle) battleTitle.textContent = "BATTLE_ZONE // RPG_STORY_INTERACT";

            workspace.innerHTML = `
                <div class="pixel-text" style="font-size: 14px; margin-bottom: 10px; max-height: 80px; overflow-y: auto; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                    <span style="color: var(--neon-purple);">[CHƯƠNG 1]</span> Bạn lạc vào vùng đất hoang tàn, trước mặt là một NPC đang hấp hối. Bạn sẽ nói gì bằng tiếng Anh để hỏi đường hoặc cứu giúp?
                </div>
                <textarea id="userInput" style="width: 100%; height: 60px; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 10px; font-family: var(--text-mono); font-size: 16px; border-radius: 8px; resize: none; box-sizing: border-box;" placeholder="Viết phản ứng/lời thoại của nhân vật của bạn..."></textarea>
                <div style="margin-top: 8px; display: flex; gap: 12px;">
                    <button class="pixel-btn" style="background: var(--neon-purple);" onclick="submitChallenge()">CHOICE_ACTION</button>
                </div>
            `;
            break;
    }

    // Tái cấu hình phím tắt Enter để gửi bài nhanh
    initKeyboardShortcuts();
}

/**
 * TƯƠNG TÁC THỊ GIÁC: Điều khiển biểu cảm biến hình thời gian thực của Nhân vật Chibi
 */
function updateChibiEmotion(score) {
    const chibiCharacter = document.querySelector(".character");
    if (!chibiCharacter) return;

    // Gỡ bỏ các lớp cảm xúc cũ
    chibiCharacter.classList.remove("master-g-mad", "master-g-proud");

    // Ép trạng thái hình thể dựa trên điểm số thực tế
    if (score < 5.0) {
        chibiCharacter.classList.add("master-g-mad"); // Mặt đỏ rực, rung giật dữ dội khi sai
    } else if (score >= 8.0) {
        chibiCharacter.classList.add("master-g-proud"); // Miệng cười to, nhún nhảy tốc độ cao khi đúng
        triggerFireworksEffect(); // Điểm cao rực rỡ kích nổ pháo hoa Lottie
    }

    // Sau 5 giây, cho nhân vật tự động bình tĩnh trở lại nhịp thở sinh học
    setTimeout(() => {
        chibiCharacter.classList.remove("master-g-mad", "master-g-proud");
    }, 5000);
}

/**
 * 2. GỬI LỆNH LÀM BÀI ĐỒNG BỘ QUA AI CONTROLLER
 */
function submitChallenge() {
    const userInputField = document.getElementById("userInput");
    const aiResponseBox = document.getElementById("aiResponseBox");
    const aiFeedbackDiv = document.getElementById("aiFeedback");

    if (!userInputField || !aiResponseBox || !aiFeedbackDiv) return;

    const textValue = userInputField.value.trim();

    if (!textValue) {
        triggerCardShake();
        return;
    }

    aiResponseBox.style.display = "block";
    aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-amber);'>MASTER_G ĐANG SOI MÓI BÀI LÀM...</span>";

    // Đẩy payload lên API tùy thuộc vào chế độ đang chọn
    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: CURRENT_USER_ID,
            text: textValue,
            mode: activeFeature // Truyền mode để AI biết lối xử lý ngữ cảnh
        })
    })
    .then(response => {
        if (!response.ok) throw new Error("API sập.");
        return response.json();
    })
    .then(data => {
        // Render kết quả bóc tách sạch từ Gemini 2.5 Flash
        const result = data.result || data;
        const feedback = result.feedback || "Không có nhận xét.";
        const score = result.score !== undefined ? result.score : 0;

        let scoreColor = "var(--pixel-green)";
        if (score < 5.0) {
            scoreColor = "var(--neon-pink)";
            triggerCardShake(); // Rung giật màn hình CRT khi bị chê bài
        } else if (score < 8.0) {
            scoreColor = "var(--neon-amber)";
        }

        // Kích hoạt biến hình cảm xúc Chibi thời gian thực
        updateChibiEmotion(score);

        aiFeedbackDiv.innerHTML = `
            <div style="margin-bottom: 8px; line-height: 1.4; color: #fff;">${feedback}</div>
            <div style="font-family: var(--text-pixel); font-size: 12px; color: ${scoreColor}; margin-top: 8px;">
                RATING_SCORE: ${score}/10
            </div>
        `;
        userInputField.value = "";
    })
    .catch(error => {
        console.error(error);
        triggerCardShake();
        aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-pink);'>ERROR: KHÔNG THỂ KẾT NỐI VỚI NÃO BỘ AI!</span>";
    });
}

/**
 * 3. TẢI DANH SÁCH TỪ VỰNG TỪ MYSQL RENDER LÊN CARD TALL
 */
function loadVocabQuests() {
    const container = document.querySelector("#vocab-card .pixel-text");
    if (!container) return;

    fetch('/api/game/vocabularies')
    .then(res => res.json())
    .then(data => {
        const list = data.vocabularies;
        if (!list || list.length === 0) {
            container.innerHTML = "Chưa có Quest từ vựng.";
            return;
        }

        // Tạo cấu trúc phân nhóm từ vựng theo chủ đề (Theme)
        const themes = {};
        list.forEach(item => {
            const themeName = item.theme || "General";
            if (!themes[themeName]) themes[themeName] = [];
            themes[themeName].push(item);
        });

        let html = '<div style="max-height: 380px; overflow-y: auto; padding-right: 4px;">';

        for (const [theme, words] of Object.entries(themes)) {
            html += `
                <div style="margin-bottom: 16px;">
                    <div class="pixel-title" style="color: var(--neon-amber); font-size: 11px; border-left: 3px solid var(--neon-amber); padding-left: 6px; margin-bottom: 8px;">
                        ${theme.toUpperCase()}
                    </div>
                    <ul style="list-style: none; padding:0; margin:0;">
            `;

            words.forEach(item => {
                const opacity = item.is_unlocked ? "1" : "0.4";
                const pointerEvents = item.is_unlocked ? "auto" : "none";
                const checkSign = item.is_memorized ? "[ X ]" : "[ _ ]";
                const checkColor = item.is_memorized ? "var(--pixel-green)" : "#64748b";

                html += `
                    <li style="margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center; opacity: ${opacity}; pointer-events: ${pointerEvents};">
                        <div style="flex-grow: 1; padding-right: 10px;">
                            <strong style="color: var(--neon-cyan); font-size: 16px;">${item.word}</strong>
                            <span style="font-size: 13px; color: #94a3b8; display: block; margin-top: 2px;">${item.meaning}</span>
                        </div>
                        <button onclick="toggleVocabMark(${item.id})" style="background: transparent; border: none; color: ${checkColor}; font-family: var(--text-pixel); font-size: 10px; cursor: pointer; padding: 4px;">
                            ${checkSign}
                        </button>
                    </li>
                `;
            });

            html += '</ul></div>';
        }

        html += '</div>';
        container.innerHTML = html;
    })
    .catch(() => {
        container.innerHTML = "<span style='color:var(--neon-pink)'>Lỗi nạp Quest từ vựng!</span>";
    });
}

/**
 * Gửi lệnh đánh dấu X đã ghi nhớ từ vựng lên hệ thống
 */
function toggleVocabMark(vocabId) {
    fetch('/api/game/vocab/toggle_memorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vocab_id: vocabId, user_id: CURRENT_USER_ID })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return;
        loadVocabQuests();

        // Kích hoạt nổ pháo hoa và nâng cấp hiển thị nếu hoàn thành ải thăng Level
        if (data.level_upgraded) {
            triggerFireworksEffect();
            alert(` CHÚC MỪNG! Bạn đã hoàn thành ải từ vựng. ĐẲNG CẤP MỚI: ${data.current_level}`);
            const rankText = document.querySelector("#status-card .pixel-text");
            if (rankText) {
                rankText.innerHTML = `USER: <span style="color: var(--neon-cyan);">${CURRENT_USERNAME}</span> <br>RANK: <span style="color: var(--pixel-green);">${data.current_level}</span>`;
            }
            updateChibiEmotion(10.0);
        }
    });
}

/**
 * 4. ĐIỂM DANH HÀNG NGÀY TĂNG CHUỖI STREAK THỜI GIAN THỰC
 */
function triggerCheckin() {
    fetch('/api/game/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: CURRENT_USER_ID })
    })
    .then(res => res.json())
    .then(data => {
        if(data.error) return;
        const streakText = document.querySelector(".pulse-neon");
        if (streakText && data.current_streak) {
            streakText.textContent = data.current_streak;
            triggerFireworksEffect(); // Điểm danh thành công -> Thưởng nổ pháo hoa rực rỡ
        }
        loadVocabQuests();
    });
}

function startMiniGame() {
    alert("Đấu trường Gacha phản xạ đang được Master G thiết lập trận đấu!");
}

function triggerCardShake() {
    const battleCard = document.getElementById("battle-card");
    if (battleCard) {
        battleCard.classList.add("error-shake");
        setTimeout(() => battleCard.classList.remove("error-shake"), 300);
    }
}

function initKeyboardShortcuts() {
    const userInput = document.getElementById("userInput");
    if (userInput) {
        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitChallenge();
            }
        });
    }
}

/**
 * TÍNH NĂNG NÂNG CAO: Tự động tải thư viện Lottie không làm chậm trang
 */
function initLottieLibrary() {
    if (!window.lottie) {
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js";
        script.id = "lottie-cdn";
        document.head.appendChild(script);
    }
}

/**
 * Tạo hiệu ứng nổ pháo hoa Pixel rực rỡ tràn màn hình khi đạt thành tích cao
 */
function triggerFireworksEffect() {
    if (!window.lottie) return;

    // Tạo nhanh một vùng chứa hiệu ứng tạm thời
    const lottieContainer = document.createElement("div");
    lottieContainer.style.position = "fixed";
    lottieContainer.style.top = "0";
    lottieContainer.style.left = "0";
    lottieContainer.style.width = "100vw";
    lottieContainer.style.height = "100vh";
    lottieContainer.style.zIndex = "99999";
    lottieContainer.style.pointerEvents = "none";
    document.body.appendChild(lottieContainer);

    // Triển khai pháo hoa từ tệp JSON động có sẵn mã nguồn Pixel
    const animation = lottie.loadAnimation({
        container: lottieContainer,
        renderer: 'svg',
        loop: false,
        autoplay: true,
        path: 'https://assets5.lottiefiles.com/packages/lf20_obh5c7sh.json' // Tệp hiệu ứng pháo hoa 8-bit mẫu mực
    });

    // Tự động dọn dẹp bộ nhớ xóa khối div khi pháo hoa nổ xong
    animation.addEventListener('complete', () => {
        lottieContainer.remove();
    });
}