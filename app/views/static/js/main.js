// main.js

// Khép kín hệ thống Auth Portal: Chặn quyền truy cập Dashboard trái phép từ đầu
if (!localStorage.getItem("user_id") || !localStorage.getItem("username")) {
    // Tránh bị lặp vòng lặp nếu đang ở trang auth hoặc index
    if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
        alert("CẢNH BÁO TRUY CẬP: Bạn chưa đăng nhập hệ thống! Đang quay lại Portal...");
        window.location.href = '/auth';
    }
}

// Quản lý trạng thái phiên làm việc động từ LocalStorage
const CURRENT_USER_ID = localStorage.getItem("user_id") || 1;
const CURRENT_USERNAME = localStorage.getItem("username") || "Explorer";

// Biến toàn cục lưu trữ tính năng hiện tại người dùng đang chọn
let activeFeature = "grammar";

document.addEventListener("DOMContentLoaded", () => {
    // 1. Đồng bộ dữ liệu thực tế từ DB lên Dashboard
    const currentPath = window.location.pathname;
    if (currentPath === '/dashboard') {
        fetch(`/api/auth/user/${CURRENT_USER_ID}`)
            .then(res => res.json())
            .then(data => {
                if (!data.error) {
                    const dashUsername = document.getElementById("dash-username");
                    const dashRank = document.getElementById("dash-rank");
                    const dashStreak = document.getElementById("dash-streak");

                    if(dashUsername) dashUsername.innerText = data.username;
                    if(dashRank) dashRank.innerText = data.level;
                    if(dashStreak) dashStreak.innerText = data.streak;
                }
            })
            .catch(err => console.error("Lỗi đồng bộ dữ liệu User:", err));
    }

    // 2. Tải trước danh sách nhiệm vụ từ vựng ở cột trái (nếu đang ở trang có cột này)
    loadVocabQuests();

    // 3. Lắng nghe sự kiện gõ phím nhanh trong ô nhập lệnh
    initKeyboardShortcuts();

    // 4. Tải thư viện Lottie động để chuẩn bị hiệu ứng nổ pháo hoa pixel
    initLottieLibrary();

    // 5. Nếu đang ở trang Story, tự động kích hoạt truyện
    if (currentPath === '/story') {
        initRPGStory();
    }
});

function switchFeature(featureName) {
    const currentPath = window.location.pathname;

    // 1. KIỂM TRA ĐIỀU HƯỚNG GIỮA CÁC TRANG
    if ((featureName === 'grammar' || featureName === 'vocab') && currentPath !== '/learn') {
        localStorage.setItem("selected_learning_mode", featureName);
        window.location.href = '/learn';
        return;
    }

    if (featureName === 'game' && currentPath !== '/test') {
        window.location.href = '/test';
        return;
    }

    if (featureName === 'story' && currentPath !== '/story') {
        window.location.href = '/story';
        return;
    }

    // 2. RENDER GIAO DIỆN KHÔNG GIAN BATTLE ZONE (Cho Dashboard/Learn)
    activeFeature = featureName;
    const workspace = document.getElementById("dynamic-workspace");
    const aiResponseBox = document.getElementById("aiResponseBox");

    // Xóa hiệu ứng chọn cũ trên Bento Grid
    document.querySelectorAll(".bento-card").forEach(card => card.style.borderColor = "var(--glass-border)");
    const activeCard = document.getElementById(`${featureName}-card`);
    if (activeCard) activeCard.style.borderColor = "var(--neon-cyan)";

    if (!workspace) return;
    if (aiResponseBox) aiResponseBox.style.display = "none";

    switch (featureName) {
        case 'vocab':
            const vocabTitle = document.querySelector("#battle-card .pixel-title");
            if(vocabTitle) {
                vocabTitle.textContent = "BATTLE_ZONE // MASTER_G";
                vocabTitle.style.color = "var(--neon-pink)";
            }
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
            const grammarTitle = document.querySelector("#battle-card .pixel-title");
            if(grammarTitle) {
                grammarTitle.textContent = "BATTLE_ZONE // MASTER_G";
                grammarTitle.style.color = "var(--neon-pink)";
            }
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
    }

    initKeyboardShortcuts();
}

function updateChibiEmotion(score) {
    const chibiCharacter = document.querySelector(".character");
    if (!chibiCharacter) return;

    chibiCharacter.classList.remove("master-g-mad", "master-g-proud");

    if (score < 5.0) {
        chibiCharacter.classList.add("master-g-mad");
    } else if (score >= 8.0) {
        chibiCharacter.classList.add("master-g-proud");
        triggerFireworksEffect();
    }

    setTimeout(() => {
        chibiCharacter.classList.remove("master-g-mad", "master-g-proud");
    }, 5000);
}

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

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: CURRENT_USER_ID,
            text: textValue,
            mode: activeFeature
        })
    })
    .then(response => {
        if (!response.ok) throw new Error("API sập.");
        return response.json();
    })
    .then(data => {
        const result = data.result || data;
        const feedback = result.feedback || "Không có nhận xét.";
        const score = result.score !== undefined ? result.score : 0;

        let scoreColor = "var(--pixel-green)";
        if (score < 5.0) {
            scoreColor = "var(--neon-pink)";
            triggerCardShake();
        } else if (score < 8.0) {
            scoreColor = "var(--neon-amber)";
        }

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
        triggerCardShake();
        aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-pink);'>ERROR: KHÔNG THỂ KẾT NỐI VỚI NÃO BỘ AI!</span>";
    });
}

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

        if (data.level_upgraded) {
            triggerFireworksEffect();
            alert(`🎉 CHÚC MỪNG! Bạn đã hoàn thành ải từ vựng. ĐẲNG CẤP MỚI: ${data.current_level}`);
            const dashRank = document.getElementById("dash-rank");
            if (dashRank) dashRank.innerText = data.current_level;
            updateChibiEmotion(10.0);
        }
    });
}

function triggerCheckin() {
    fetch('/api/game/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: CURRENT_USER_ID })
    })
    .then(res => res.json())
    .then(data => {
        if(data.error) return;
        const streakText = document.getElementById("dash-streak") || document.querySelector(".pulse-neon");
        if (streakText && data.current_streak) {
            streakText.textContent = data.current_streak;
            triggerFireworksEffect();
        }
        loadVocabQuests();
    });
}

function triggerCardShake() {
    const battleCard = document.getElementById("battle-card");
    if (battleCard) {
        battleCard.classList.add("error-shake");
        setTimeout(() => battleCard.classList.remove("error-shake"), 300);
    }
}

function initKeyboardShortcuts() {
    // Hỗ trợ sự kiện gõ Enter cho cả input thường và input của story
    ['userInput', 'storyInput'].forEach(inputId => {
        const el = document.getElementById(inputId);
        if (el) {
            // Reset listener cũ
            const newField = el.cloneNode(true);
            el.parentNode.replaceChild(newField, el);

            newField.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (inputId === 'storyInput') {
                        executeStoryAction();
                    } else {
                        submitChallenge();
                    }
                }
            });
        }
    });
}

function initLottieLibrary() {
    if (!window.lottie) {
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js";
        script.id = "lottie-cdn";
        document.head.appendChild(script);
    }
}

function triggerFireworksEffect() {
    if (!window.lottie) return;

    const lottieContainer = document.createElement("div");
    lottieContainer.style.position = "fixed";
    lottieContainer.style.top = "0";
    lottieContainer.style.left = "0";
    lottieContainer.style.width = "100vw";
    lottieContainer.style.height = "100vh";
    lottieContainer.style.zIndex = "99999";
    lottieContainer.style.pointerEvents = "none";
    document.body.appendChild(lottieContainer);

    const animation = lottie.loadAnimation({
        container: lottieContainer,
        renderer: 'svg',
        loop: false,
        autoplay: true,
        path: 'https://assets5.lottiefiles.com/packages/lf20_obh5c7sh.json'
    });

    animation.addEventListener('complete', () => {
        lottieContainer.remove();
    });
}

// =======================================================
// LOGIC RPG STORY (CÓ TRÍ NHỚ, LƯỢT ĐÁNH + GỢI Ý ĐIỀN TỪ)
// =======================================================
let currentStoryTurn = 1;
let storyHistory = "";

function initRPGStory() {
    currentStoryTurn = 1;
    storyHistory = "";

    const turnCounter = document.getElementById("story-turn-counter");
    if(turnCounter) turnCounter.innerText = "1/10";

    const terminal = document.getElementById("story-terminal");
    if (!terminal) return;

    terminal.innerHTML = `<div class="typing-effect" style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 14px;">[SYSTEM] Đang thiết lập bối cảnh sinh tồn...</div>`;

    fetch('/api/ai/story/init', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: CURRENT_USER_ID })
    })
    .then(res => res.json())
    .then(data => {
        terminal.innerHTML = "";
        appendStoryScene(data, true);
    })
    .catch(err => {
        terminal.innerHTML = "<span style='color: var(--neon-pink);'>Lỗi khởi tạo thế giới! Hãy tải lại trang.</span>";
    });
}

function appendStoryScene(data, isInit = false) {
    const terminal = document.getElementById("story-terminal");
    const hintBox = document.getElementById("story-hint-box");

    // 1. In cảnh truyện ra Terminal
    terminal.innerHTML += `
        <div style="background: rgba(26, 16, 60, 0.5); border-left: 3px solid var(--neon-purple); padding: 12px; border-radius: 4px; margin-bottom: 10px;">
            <div style="color: #fff; font-size: 16px; margin-bottom: 8px; line-height: 1.5;">${data.scene_en}</div>
            <div style="color: #94a3b8; font-size: 14px; font-style: italic; line-height: 1.4;">${data.scene_vn}</div>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    // Cập nhật trí nhớ cốt truyện cho AI
    storyHistory += `\n[GM]: ${data.scene_en}`;

    // 2. Xử lý màn hình kết thúc hoặc render hộp Gợi ý
    const storyInput = document.getElementById("storyInput");
    const btnExecute = document.getElementById("btn-story-execute");

    if (data.is_end === "true" || data.is_end === true) {
        hintBox.innerHTML = `
            <div style="color: var(--pixel-green); font-size: 16px; font-weight: bold; text-align: center; margin-bottom: 10px;">MISSION ACCOMPLISHED!</div>
            <div style="color: #cbd5e1; font-size: 13px; text-align: center;">Hành trình kết thúc. Bạn đã sống sót qua 10 lượt!</div>
            <button class="pixel-btn" style="background: var(--neon-amber); width: 100%; margin-top: 15px;" onclick="initRPGStory()">CHƠI LẠI TỪ ĐẦU</button>
        `;
        if(storyInput) storyInput.disabled = true;
        if(btnExecute) btnExecute.disabled = true;

        triggerFireworksEffect();
    } else {
        hintBox.innerHTML = `
            <div style="color: var(--neon-cyan); font-size: 16px; font-weight: bold; font-family: var(--text-mono); line-height: 1.5; margin-bottom: 10px;">${data.hint_en || "Gợi ý đang bị nhiễu..."}</div>
            <div style="color: #94a3b8; font-size: 13px; font-style: italic;">Ý nghĩa: ${data.hint_vn || "Vui lòng tự do hành động"}</div>
        `;
        if(storyInput) {
            storyInput.disabled = false;
            storyInput.focus();
        }
        if(btnExecute) btnExecute.disabled = false;
    }
}

function executeStoryAction() {
    const inputEle = document.getElementById("storyInput");
    const terminal = document.getElementById("story-terminal");
    const hintBox = document.getElementById("story-hint-box");
    const turnCounter = document.getElementById("story-turn-counter");

    const actionText = inputEle.value.trim();
    if(!actionText) {
        triggerCardShake(); // Rung lắc nếu submit rỗng
        return;
    }

    // Ghi nhận hành động vào lịch sử AI
    storyHistory += `\n[Player]: ${actionText}`;

    // Tăng lượt và cập nhật UI
    currentStoryTurn++;
    if(turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;

    // Trạng thái Loading
    hintBox.innerHTML = "<div class='pulse-neon' style='font-size:13px; text-align: center;'>MASTER_G ĐANG SOẠN KỊCH BẢN...</div>";

    // In câu gõ của người dùng lên terminal
    terminal.innerHTML += `
        <div style="text-align: right; margin: 10px 0;">
            <span style="background: var(--neon-cyan); color: #000; padding: 6px 12px; border-radius: 8px; font-weight: bold; font-family: var(--text-mono);">> ${actionText}</span>
        </div>
    `;
    inputEle.value = "";
    terminal.scrollTop = terminal.scrollHeight;

    // Loading indicator của Game Master
    const loadId = "loading-" + Date.now();
    terminal.innerHTML += `<div id="${loadId}" class="pulse-neon" style="margin-bottom: 10px;">[GM] Đang chấm điểm và viết tiếp truyện...</div>`;
    terminal.scrollTop = terminal.scrollHeight;

    // Gửi data lên Server kèm Trí nhớ và Số lượt
    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: CURRENT_USER_ID,
            text: actionText,
            mode: 'story',
            turn: currentStoryTurn,
            history: storyHistory
        })
    })
    .then(res => res.json())
    .then(data => {
        const loadEl = document.getElementById(loadId);
        if(loadEl) loadEl.remove();

        const result = data.result || data;
        const score = result.score !== undefined ? result.score : 0;

        // Cập nhật trạng thái chấm điểm ngữ pháp
        const scoreColor = score >= 5.0 ? "var(--pixel-green)" : "var(--neon-pink)";
        terminal.innerHTML += `
            <div style="font-size: 13px; color: ${scoreColor}; font-family: var(--text-pixel); margin-bottom: 15px; text-align: right;">
                [GM RATING: ${score}/10] - ${result.feedback || "Không có nhận xét"}
            </div>
        `;

        updateChibiEmotion(score);
        appendStoryScene(result);
    })
    .catch(err => {
        const loadEl = document.getElementById(loadId);
        if(loadEl) loadEl.remove();
        hintBox.innerHTML = "<span style='color: var(--neon-pink);'>Lỗi kết nối Game Master! Đứt cáp không gian!</span>";

        // Hoàn tác lượt nếu gọi API lỗi
        currentStoryTurn--;
        if(turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;
    });
}