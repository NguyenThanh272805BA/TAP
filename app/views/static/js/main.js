const CURRENT_USERNAME_DEFAULT = "Explorer";
let activeFeature = "grammar"; // Lưu trữ tính năng hiện tại người dùng chọn trong Battle Zone

document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;

    // Xác thực và đồng bộ dữ liệu thực tế từ DB lên UI (Sử dụng API Endpoint /me bảo mật)
    if (currentPath !== '/auth' && currentPath !== '/') {
        fetch('/api/auth/user/me')
            .then(res => {
                if (res.status === 401) {
                    // Nếu Backend báo chưa đăng nhập hoặc hết hạn session, đá văng ra Portal
                    if (currentPath !== '/auth' && currentPath !== '/') {
                        alert("CẢNH BÁO TRUY CẬP: Phiên làm việc hết hạn! Đang quay lại Portal...");
                        window.location.href = '/auth';
                    }
                    throw new Error("Unauthorized");
                }
                return res.json();
            })
            .then(data => {
                if (data && !data.error) {
                    // Đổ data lên Sidebar (UI Mới)
                    const sidebarUser = document.getElementById("sidebar-user");
                    const sidebarRank = document.getElementById("sidebar-rank");
                    const sidebarStreak = document.getElementById("sidebar-streak");
                    const sidebarCoins = document.getElementById("sidebar-coins");

                    if (sidebarUser) sidebarUser.innerText = data.username;
                    if (sidebarRank) sidebarRank.innerText = data.level;
                    if (sidebarStreak) sidebarStreak.innerText = data.streak;
                    if (sidebarCoins) sidebarCoins.innerText = data.coins;

                    // Phân quyền Admin: Hiển thị nút God Mode nếu role là admin
                    if (data.role === 'admin') {
                        const adminNav = document.getElementById('nav-admin');
                        if (adminNav) adminNav.style.display = 'flex';
                    }

                    // Xử lý UI Check-in 7 ngày ở Dashboard
                    if (currentPath === '/dashboard') {
                        renderStreakUI(data.streak);
                        if (data.is_checked_in) {
                            lockCheckinButton();
                        }
                    }

                    // Cập nhật riêng cho màn Gacha
                    const gachaStreak = document.getElementById("gacha-streak");
                    if (gachaStreak) gachaStreak.innerText = data.streak;
                }
            })
            .catch(err => console.log("Đang tải hoặc trục trặc đồng bộ Session:", err));
    }

    // 2. Tải trước danh sách nhiệm vụ từ vựng ở cột trái (nếu tồn tại component)
    loadVocabQuests();

    // 3. Lắng nghe sự kiện gõ phím nhanh trong ô nhập lệnh (Enter kích hoạt)
    initKeyboardShortcuts();

    // 4. Tải thư viện Lottie động để chuẩn bị hiệu ứng nổ pháo hoa pixel
    initLottieLibrary();

    // 5. Nếu đang ở không gian Story Terminal, tự động kích hoạt cốt truyện sinh tồn
    if (currentPath === '/story') {
        initRPGStory();
    }
});

/**
 * =======================================================
 * CÁC HÀM XỬ LÝ GIAO DIỆN MỚI (STREAK, ĐIỂM DANH, SHOP)
 * =======================================================
 */

function renderStreakUI(streakCount) {
    const activeDays = streakCount % 7 === 0 && streakCount > 0 ? 7 : streakCount % 7;
    for (let i = 1; i <= 7; i++) {
        const block = document.getElementById(`day-${i}`);
        if(block) {
            if (i <= activeDays) block.classList.add('active');
            else block.classList.remove('active');
        }
    }
}

function lockCheckinButton() {
    const btn = document.getElementById("btn-checkin");
    const timerText = document.getElementById("checkin-timer");
    if(btn && timerText) {
        btn.disabled = true;
        btn.innerText = "ĐÃ ĐIỂM DANH HÔM NAY";
        timerText.style.display = "block";

        // Tính toán đếm ngược đến 00:00 ngày mai
        setInterval(() => {
            const now = new Date();
            const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
            const diff = tomorrow - now;

            const h = Math.floor((diff % 86400000) / 3600000).toString().padStart(2, '0');
            const m = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
            const s = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');
            timerText.innerText = `Lượt tiếp theo: ${h}:${m}:${s}`;
        }, 1000);
    }
}

function triggerCheckin() {
    fetch('/api/game/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        alert(data.message);
        const sidebarStreak = document.getElementById("sidebar-streak");
        const sidebarCoins = document.getElementById("sidebar-coins");

        if(sidebarStreak) sidebarStreak.innerText = data.current_streak;
        if(sidebarCoins) sidebarCoins.innerText = data.new_coins;

        renderStreakUI(data.current_streak);
        lockCheckinButton();
        triggerFireworksEffect();
        loadVocabQuests();
    });
}

function buyItem(itemId, price) {
    fetch('/api/game/shop/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, price: price })
    })
    .then(res => res.json())
    .then(data => {
        if(data.error) { alert(data.error); }
        else {
            alert(data.message);
            const sidebarCoins = document.getElementById("sidebar-coins");
            if(sidebarCoins) sidebarCoins.innerText = data.new_coins;
        }
    });
}

/**
 * =======================================================
 * CÁC HÀM XỬ LÝ LÕI GAME (BATTLE ZONE, AI, LOTTIE)
 * =======================================================
 */

function switchFeature(featureName) {
    const currentPath = window.location.pathname;

    // 1. KIỂM TRA VÀ ĐIỀU HƯỚNG TRANG CHUYÊN BIỆT
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

    // 2. RENDER GIAO DIỆN KHÔNG GIAN BATTLE ZONE (Cho Dashboard / Learn nội bộ)
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
            if (vocabTitle) {
                vocabTitle.textContent = "BATTLE_ZONE // MASTER_G";
                vocabTitle.style.color = "var(--neon-pink)";
            }
            workspace.innerHTML = `
                <div class="pixel-text" style="font-size: 15px; margin-bottom: 12px; line-height: 1.6;">
                    NHIỆM VỤ TỪ VỰNG: Đặt một câu có nghĩa chứa từ lóng / từ vựng hệ thống yêu cầu dưới đây.
                </div>
                <textarea id="userInput" style="width: 100%; height: 75px; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 15px; border-radius: 12px; resize: none; box-sizing: border-box;" placeholder="Master G đang đợi câu từ vựng của bạn..."></textarea>
                <div style="margin-top: 10px; display: flex; gap: 12px;">
                    <button class="pixel-btn" onclick="submitChallenge()">SEND_VOCAB</button>
                </div>
            `;
            break;

        case 'grammar':
            const grammarTitle = document.querySelector("#battle-card .pixel-title");
            if (grammarTitle) {
                grammarTitle.textContent = "BATTLE_ZONE // MASTER_G";
                grammarTitle.style.color = "var(--neon-pink)";
            }
            workspace.innerHTML = `
                <div class="pixel-text" style="font-size: 15px; margin-bottom: 12px; line-height: 1.6;">
                    NHIỆM VỤ NGỮ PHÁP: Sử dụng đúng cấu trúc ngữ pháp quy định để vượt ải thành công.
                </div>
                <textarea id="userInput" style="width: 100%; height: 75px; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 15px; border-radius: 12px; resize: none; box-sizing: border-box;" placeholder="Nhập câu ngữ pháp tại đây..."></textarea>
                <div style="margin-top: 10px; display: flex; gap: 12px;">
                    <button class="pixel-btn" onclick="submitChallenge()">SEND_COMMAND</button>
                </div>
            `;
            break;
    }

    initKeyboardShortcuts();
}

function updateChibeEmotion(score) {
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
    aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-amber); font-family: var(--text-main); font-size:15px;' class='pulse-neon'>MASTER_G ĐANG SOI MÓI BÀI LÀM...</span>";

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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

        updateChibeEmotion(score);

        aiFeedbackDiv.innerHTML = `
            <div style="margin-bottom: 10px; line-height: 1.6; color: #fff; font-family: var(--text-main); font-size:16px;">${feedback}</div>
            <div style="font-family: var(--text-pixel); font-size: 12px; color: ${scoreColor}; margin-top: 10px; letter-spacing: 0.5px;">
                RATING_SCORE: ${score}/10
            </div>
        `;
        userInputField.value = "";
    })
    .catch(error => {
        triggerCardShake();
        aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-pink); font-family: var(--text-main); font-size:15px;'>ERROR: KHÔNG THỂ KẾT NỐI VỚI NÃO BỘ AI!</span>";
    });
}

function loadVocabQuests() {
    const container = document.querySelector("#vocab-card .pixel-text");
    if (!container) return;

    fetch('/api/game/vocabularies')
    .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
    })
    .then(data => {
        const list = data.vocabularies;
        if (!list || list.length === 0) {
            container.innerHTML = "<div style='font-family:var(--text-main); font-size:14px; color:#94a3b8;'>Chưa có Quest từ vựng trong hệ thống.</div>";
            return;
        }

        const themes = {};
        list.forEach(item => {
            const themeName = item.theme || "General";
            if (!themes[themeName]) themes[themeName] = [];
            themes[themeName].push(item);
        });

        let html = '<div style="max-height: 380px; overflow-y: auto; padding-right: 8px;">';

        for (const [theme, words] of Object.entries(themes)) {
            html += `
                <div style="margin-bottom: 16px;">
                    <div class="pixel-title" style="color: var(--neon-amber); font-size: 11px; border-left: 3px solid var(--neon-amber); padding-left: 8px; margin-bottom: 10px; letter-spacing: 0.5px;">
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
                    <li style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; opacity: ${opacity}; pointer-events: ${pointerEvents};">
                        <div style="flex-grow: 1; padding-right: 10px;">
                            <strong style="color: var(--neon-cyan); font-family: var(--text-main); font-size: 16px; font-weight:600;">${item.word}</strong>
                            <span style="font-size: 13px; color: #94a3b8; display: block; margin-top: 3px; font-family: var(--text-main); line-height: 1.4;">${item.meaning}</span>
                        </div>
                        <button onclick="toggleVocabMark(${item.id})" class="pixel-btn" style="background: rgba(0,0,0,0.4); border: 1px solid ${checkColor}; color: ${checkColor}; font-size: 10px; cursor: pointer; padding: 6px 10px; box-shadow: none;">
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
        container.innerHTML = "<span style='color:var(--neon-pink); font-family: var(--text-main); font-size:14px;'>Mất kết nối dữ liệu Quest!</span>";
    });
}

function toggleVocabMark(vocabId) {
    fetch('/api/game/vocab/toggle_memorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vocab_id: vocabId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return;
        loadVocabQuests();

        if (data.level_upgraded) {
            triggerFireworksEffect();
            alert(`🎉 CHÚC MỪNG! Bạn đã hoàn thành xuất sắc ải từ vựng.\nĐẲNG CẤP MỚI: ${data.current_level}`);
            const sidebarRank = document.getElementById("sidebar-rank");
            if (sidebarRank) sidebarRank.innerText = data.current_level;
            updateChibeEmotion(10.0);
        }
    });
}

function triggerCardShake() {
    const battleCard = document.getElementById("battle-card");
    if (battleCard) {
        battleCard.classList.add("error-shake");
        setTimeout(() => battleCard.classList.remove("error-shake"), 400);
    }
}

function initKeyboardShortcuts() {
    ['userInput', 'storyInput'].forEach(inputId => {
        const el = document.getElementById(inputId);
        if (el) {
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

/**
 * =======================================================
 * LOGIC RPG STORY (CÓ TRÍ NHỚ, BỘ ĐẾM LƯỢT + GỢI Ý ĐIỀN TỪ)
 * =======================================================
 */
let currentStoryTurn = 1;
let storyHistory = "";

function initRPGStory() {
    currentStoryTurn = 1;
    storyHistory = "";

    const turnCounter = document.getElementById("story-turn-counter");
    if (turnCounter) turnCounter.innerText = "1/10";

    const terminal = document.getElementById("story-terminal");
    if (!terminal) return;

    terminal.innerHTML = `<div class="typing-effect" style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 14px;">[SYSTEM] Đang thiết lập bối cảnh sinh tồn hậu tận thế...</div>`;

    fetch('/api/ai/story/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        terminal.innerHTML = "";
        appendStoryScene(data, true);
    })
    .catch(err => {
        terminal.innerHTML = "<span style='color: var(--neon-pink); font-family: var(--text-main); font-size:15px;'>[ERROR] Lỗi khởi tạo thế giới từ Game Master! Hãy reload trang.</span>";
    });
}

function appendStoryScene(data, isInit = false) {
    const terminal = document.getElementById("story-terminal");
    const hintBox = document.getElementById("story-hint-box");

    if (!terminal || !hintBox) return;

    // Phun in nội dung bối cảnh ra màn hình Terminal song song EN - VN
    terminal.innerHTML += `
        <div style="background: rgba(30, 41, 75, 0.7); border-left: 3px solid var(--neon-purple); padding: 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <div style="color: #fff; font-family: var(--text-main); font-size: 16px; margin-bottom: 10px; line-height: 1.6; font-weight:600;">${data.scene_en}</div>
            <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">${data.scene_vn}</div>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    // Cập nhật chuỗi bộ nhớ đệm (Trí nhớ cốt truyện của AI)
    storyHistory += `\n[GM]: ${data.scene_en}`;

    const storyInput = document.getElementById("storyInput");
    const btnExecute = document.getElementById("btn-story-execute");

    // Kiểm tra xem đã cán mốc lượt thứ 10 (Hạ màn game) hay chưa
    if (data.is_end === "true" || data.is_end === true) {
        hintBox.innerHTML = `
            <div style="color: var(--pixel-green); font-family: var(--text-pixel); font-size: 14px; text-align: center; margin-bottom: 15px; letter-spacing:1px;">MISSION ACCOMPLISHED!</div>
            <div style="color: #cbd5e1; font-family: var(--text-main); font-size: 15px; text-align: center; line-height:1.6;">Hành trình sinh tồn hoàn tất. Bạn xuất sắc vượt qua 10 lượt cân não!</div>
            <button class="pixel-btn" style="background: var(--neon-amber); width: 100%; margin-top: 15px; padding:15px; font-size:12px;" onclick="initRPGStory()">CHƠI LẠI MÀN MỚI</button>
        `;
        if (storyInput) storyInput.disabled = true;
        if (btnExecute) btnExecute.disabled = true;

        triggerFireworksEffect();
    } else {
        // Render ma trận gợi ý điền từ vào chỗ trống (Fill-in-the-blanks)
        hintBox.innerHTML = `
            <div style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 16px; font-weight: 700; line-height: 1.5; margin-bottom: 10px; letter-spacing: 0.5px;">${data.hint_en || "I need to ___ carefully."}</div>
            <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">Ý nghĩa gợi mở: ${data.hint_vn || "Tôi cần hành động cẩn trọng"}</div>
        `;
        if (storyInput) {
            storyInput.disabled = false;
            storyInput.focus();
        }
        if (btnExecute) btnExecute.disabled = false;
    }
}

function executeStoryAction() {
    const inputEle = document.getElementById("storyInput");
    const terminal = document.getElementById("story-terminal");
    const hintBox = document.getElementById("story-hint-box");
    const turnCounter = document.getElementById("story-turn-counter");

    if (!inputEle || !terminal || !hintBox) return;

    const actionText = inputEle.value.trim();
    if (!actionText) {
        triggerCardShake(); // Rung lắc bento card nếu gửi chuỗi rỗng
        return;
    }

    // Ghi nhận trực tiếp hành động của player vào lịch sử chuỗi
    storyHistory += `\n[Player]: ${actionText}`;

    // Tăng tiến trình đếm lượt và cập nhật UI bộ đếm
    currentStoryTurn++;
    if (turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;

    // Hiển thị trạng thái giải mã kịch bản trong Action Box
    hintBox.innerHTML = "<div class='pulse-neon' style='font-size:13px; font-family:var(--text-pixel); text-align: center; letter-spacing:0.5px;'>MASTER_G ĐANG SOẠN KỊCH BẢN...</div>";

    // Đẩy hành động người dùng lên màn hình Terminal
    terminal.innerHTML += `
        <div style="text-align: right; margin: 15px 0;">
            <span style="background: var(--neon-cyan); color: #000; padding: 10px 18px; border-radius: 12px; font-weight: 700; font-family: var(--text-mono); font-size:15px; display:inline-block; box-shadow:0 4px 15px rgba(103,232,249,0.3);">> ${actionText}</span>
        </div>
    `;
    inputEle.value = "";
    terminal.scrollTop = terminal.scrollHeight;

    // Kích hoạt dòng trạng thái Loading thời gian thực của Game Master
    const loadId = "loading-" + Date.now();
    terminal.innerHTML += `<div id="${loadId}" class="pulse-neon" style="margin-bottom: 15px; font-family:var(--text-main); font-size:15px; color:var(--neon-purple);">[GM] Đang phân tích ngữ pháp và dắt cốt truyện...</div>`;
    terminal.scrollTop = terminal.scrollHeight;

    // Thực hiện Fetch đẩy hành động + Trí nhớ ngữ cảnh câu chuyện lên cho AI
    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: actionText,
            mode: 'story',
            turn: currentStoryTurn,
            history: storyHistory
        })
    })
    .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
    })
    .then(data => {
        const loadEl = document.getElementById(loadId);
        if (loadEl) loadEl.remove();

        const result = data.result || data;
        const score = result.score !== undefined ? result.score : 0;

        // Render bảng điểm kiểm duyệt ngữ pháp của Master G xéo xắt lên góc phải Terminal
        const scoreColor = score >= 5.0 ? "var(--pixel-green)" : "var(--neon-pink)";
        terminal.innerHTML += `
            <div style="font-size: 12px; color: ${scoreColor}; font-family: var(--text-pixel); margin-bottom: 18px; text-align: right; letter-spacing:0.5px;">
                [GM RATING: ${score}/10] - <span style="font-family:var(--text-main); font-size:14px; font-weight:normal; color:#fff;">${result.feedback || "Cú pháp chấp nhận được."}</span>
            </div>
        `;

        updateChibeEmotion(score);
        appendStoryScene(result);
    })
    .catch(err => {
        const loadEl = document.getElementById(loadId);
        if (loadEl) loadEl.remove();
        hintBox.innerHTML = "<span style='color: var(--neon-pink); font-family: var(--text-main); font-size:15px;'>[ERROR] Lỗi kết nối Game Master! Đứt cáp mạng không gian!</span>";

        // Rollback hoàn tác bộ đếm lượt nếu tiến trình gọi API đổ bể
        currentStoryTurn--;
        if (turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;
    });
}