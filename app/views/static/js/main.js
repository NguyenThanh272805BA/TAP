const CURRENT_USERNAME_DEFAULT = "Explorer";
let activeFeature = "grammar"; // Lưu trữ tính năng hiện tại người dùng chọn trong Battle Zone
let currentTopicId = 1; // [ PHASE 2 ] Lưu Chủ đề Truyện đang chọn

document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;

    // 1. Xác thực và đồng bộ dữ liệu thực tế từ DB lên UI (Sử dụng API Endpoint /me bảo mật)
    if (currentPath !== '/auth' && currentPath !== '/') {
        fetch('/api/auth/user/me')
            .then(res => {
                if (res.status === 401) {
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
                    const sidebarUser = document.getElementById("sidebar-user");
                    const sidebarRank = document.getElementById("sidebar-rank");
                    const sidebarStreak = document.getElementById("sidebar-streak");
                    const sidebarCoins = document.getElementById("sidebar-coins");

                    if (sidebarUser) sidebarUser.innerText = data.username;
                    if (sidebarRank) sidebarRank.innerText = data.level;
                    if (sidebarStreak) sidebarStreak.innerText = data.streak;
                    if (sidebarCoins) sidebarCoins.innerText = data.coins;

                    if (data.role === 'admin') {
                        const adminNav = document.getElementById('nav-admin');
                        if (adminNav) adminNav.style.display = 'flex';
                    }

                    if (currentPath === '/dashboard') {
                        renderStreakUI(data.streak);
                        if (data.is_checked_in) {
                            lockCheckinButton();
                        }
                        // [ PHASE 2 ] Tải Quest hàng ngày
                        loadDailyQuests();

                        // Kích hoạt hướng dẫn Tân thủ
                        checkAndRunTutorial(data);
                    }

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

    // 5. Nếu đang ở không gian Story Terminal, kích hoạt Lobby (Giai đoạn 2)
    if (currentPath === '/story') {
        loadStoryLobby();
    }
});

/**
 * =======================================================
 * DAILY QUESTS (PHASE 2)
 * =======================================================
 */
function loadDailyQuests() {
    fetch('/api/game/quests/today')
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById("daily-quests-container");
        if(!container) return;

        let html = '';
        if (!data.quests || data.quests.length === 0) {
            container.innerHTML = '<div style="color: var(--pixel-green); font-size: 14px;">Bạn đã hoàn thành mọi nhiệm vụ hôm nay!</div>';
            return;
        }

        data.quests.forEach((q, idx) => {
            const statusColor = q.is_completed ? "var(--pixel-green)" : "var(--glass-border)";
            const statusText = q.is_completed ? "[ ĐÃ XONG ]" : "[ ĐANG CHỜ ]";
            const questDesc = q.type === 'NEW' ? `Học từ mới: <strong style="color: var(--neon-cyan);">${q.word}</strong>` : `Ôn tập từ: <strong style="color: var(--neon-amber);">${q.word}</strong>`;
            const opacity = q.is_completed ? "0.6" : "1";

            html += `
            <div style="background: rgba(0,0,0,0.4); border-left: 3px solid ${statusColor}; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; opacity: ${opacity}; transition: 0.3s;">
                <div>
                    <div style="color: #fff; font-size: 15px; font-family: var(--text-main); margin-bottom: 5px;">Nhiệm vụ ${idx + 1}: ${questDesc}</div>
                    <div style="color: #94a3b8; font-size: 13px;">Gợi ý nghĩa: ${q.meaning}</div>
                </div>
                <div style="color: ${statusColor}; font-family: var(--text-pixel); font-size: 12px; font-weight: bold;">
                    ${statusText}
                </div>
            </div>`;
        });
        container.innerHTML = html;
    })
    .catch(err => console.error("Lỗi tải Daily Quests:", err));
}

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

    activeFeature = featureName;
    const workspace = document.getElementById("dynamic-workspace");
    const aiResponseBox = document.getElementById("aiResponseBox");

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
            mode: 'free'
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

        // Tự động refresh UI nếu hoàn thành Quest
        if (result.quest_notification) {
            triggerFireworksEffect();
            if (typeof loadDailyQuests === 'function') loadDailyQuests();
            fetch('/api/auth/user/me')
                .then(r => r.json())
                .then(ud => {
                    const sidebarCoins = document.getElementById("sidebar-coins");
                    if (sidebarCoins) sidebarCoins.innerText = ud.coins;
                });
        }

        aiFeedbackDiv.innerHTML = `
            <div style="margin-bottom: 10px; line-height: 1.6; color: #fff; font-family: var(--text-main); font-size:16px;">${feedback}</div>
            <div style="font-family: var(--text-pixel); font-size: 12px; color: ${scoreColor}; margin-top: 10px; letter-spacing: 0.5px;">
                RATING_SCORE: ${score}/10
                ${result.quest_notification ? `<br><span style="color: var(--pixel-green);">[+] ${result.quest_notification}</span>` : ''}
            </div>
        `;
        userInputField.value = "";
    })
    .catch(error => {
        triggerCardShake();
        aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-pink); font-family: var(--text-main); font-size:15px;'>ERROR: KHÔNG THỂ KẾT NỐI VỚI NÃO BỘ AI!</span>";
    });
}
function loadDashboardLeaderboard() {
    const lbContainer = document.getElementById("dashboard-leaderboard");
    if (!lbContainer) return;
    fetch('/api/game/gacha/leaderboard')
    .then(res => res.json())
    .then(data => {
        if (!data.leaderboard || data.leaderboard.length === 0) {
            lbContainer.innerHTML = '<span style="color: #94a3b8;">Chưa có cao thủ nào.</span>';
            return;
        }
        let html = '';
        data.leaderboard.forEach((u, idx) => {
            let color = idx === 0 ? "var(--neon-amber)" : (idx === 1 ? "#cbd5e1" : "#d97706");
            if(idx > 2) color = "#94a3b8";
            html += `<div style="color: ${color}; margin-bottom: 8px; font-family: var(--text-mono); border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">#${idx+1} ${u.username} - <span style="color:#fff;">${u.score} pts</span></div>`;
        });
        lbContainer.innerHTML = html;
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
 * LOGIC RPG STORY (PHASE 2 - LOBBY, ARCHIVES & GAMEPLAY)
 * =======================================================
 */
let currentStoryTurn = 1;
let storyHistory = "";

function loadStoryLobby() {
    // 1. Fetch Archive (Lịch sử sinh tồn)
    fetch('/api/game/story/archive')
    .then(res => res.json())
    .then(data => {
        const archiveContainer = document.getElementById("archive-container");
        if(!archiveContainer) return;
        if(!data.archive || data.archive.length === 0) {
            archiveContainer.innerHTML = '<div style="color: #94a3b8; font-size: 14px; font-style: italic;">Chưa có dữ liệu hành trình.</div>';
            return;
        }
        let html = '';
        data.archive.forEach(s => {
            const statusColor = s.status === 'Survived' ? 'var(--pixel-green)' : 'var(--neon-pink)';
            html += `
            <div style="background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; border-left: 3px solid ${statusColor}; margin-bottom: 10px;">
                <strong style="color: #fff; display: block; font-size: 14px;">[${s.status}] ${s.topic}</strong>
                <span style="color: #94a3b8; font-size: 12px; display: block; margin-bottom: 8px;">Ngày: ${s.date}</span>
                <div style="color: #cbd5e1; font-size: 13px; font-style: italic; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px;">
                    "${s.summary_vn}"
                </div>
            </div>`;
        });
        archiveContainer.innerHTML = html;
    });

    // 2. Fetch Topics (Các bối cảnh để chọn)
    fetch('/api/game/story/topics')
    .then(res => res.json())
    .then(topics => {
        const topicsContainer = document.getElementById("topics-container");
        if (!topicsContainer) return;

        if (!topics || topics.length === 0) {
            topicsContainer.innerHTML = '<div style="color: #94a3b8; font-size: 14px;">Admin chưa thiết lập bối cảnh nào.</div>';
            return;
        }

        let html = '';
        topics.forEach(t => {
            const coverUrl = `/static/uploads/covers/${t.cover_image}`;
            html += `
            <div class="bento-card" style="padding: 15px; cursor: pointer; background: rgba(0,0,0,0.5); border: 2px solid var(--glass-border); transition: 0.3s;" 
                 onmouseover="this.style.borderColor='var(--neon-cyan)'; this.style.transform='scale(1.02)';" 
                 onmouseout="this.style.borderColor='var(--glass-border)'; this.style.transform='scale(1)';" 
                 onclick="startStoryWithTopic(${t.id}, '${t.title}')">
                <img src="${coverUrl}" onerror="this.src='/static/uploads/covers/default_cover.jpg'" style="width: 100%; height: 140px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;">
                <div class="pixel-title" style="font-size: 14px; margin-bottom: 5px;">${t.title}</div>
                <div style="font-size: 11px; color: var(--neon-purple); border: 1px solid var(--neon-purple); display: inline-block; padding: 3px 8px; border-radius: 4px;">${t.genre}</div>
            </div>`;
        });
        topicsContainer.innerHTML = html;
    });
}

function startStoryWithTopic(topicId, topicName) {
    currentTopicId = topicId;
    document.getElementById("story-lobby").style.display = "none";
    document.getElementById("story-battle-zone").style.display = "grid";
    document.getElementById("current-topic-name").innerText = topicName.toUpperCase();

    initRPGStory();
}

function exitToLobby() {
    document.getElementById("story-battle-zone").style.display = "none";
    document.getElementById("story-lobby").style.display = "flex";
}

function initRPGStory() {
    currentStoryTurn = 1;
    storyHistory = "";

    const turnCounter = document.getElementById("story-turn-counter");
    if (turnCounter) turnCounter.innerText = "1/10";

    const terminal = document.getElementById("story-terminal");
    if (!terminal) return;

    terminal.innerHTML = `<div class="typing-effect" style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 14px;">[SYSTEM] Đang nạp bối cảnh và kết nối Game Master...</div>`;

    fetch('/api/ai/story/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_id: currentTopicId })
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

    terminal.innerHTML += `
        <div style="background: rgba(30, 41, 75, 0.7); border-left: 3px solid var(--neon-purple); padding: 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <div style="color: #fff; font-family: var(--text-main); font-size: 16px; margin-bottom: 10px; line-height: 1.6; font-weight:600;">${data.scene_en}</div>
            <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">${data.scene_vn}</div>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    storyHistory += `\n[GM]: ${data.scene_en}`;

    const storyInput = document.getElementById("storyInput");
    const btnExecute = document.getElementById("btn-story-execute");

    if (data.is_end === "true" || data.is_end === true) {
        hintBox.innerHTML = `
            <div style="color: var(--pixel-green); font-family: var(--text-pixel); font-size: 14px; text-align: center; margin-bottom: 15px; letter-spacing:1px;">MISSION ACCOMPLISHED!</div>
            <div style="color: #cbd5e1; font-family: var(--text-main); font-size: 15px; text-align: center; line-height:1.6;">Hành trình sinh tồn hoàn tất. Nhật ký đã được lưu lại!</div>
            <button class="pixel-btn" style="background: var(--neon-amber); width: 100%; margin-top: 15px; padding:15px; font-size:12px;" onclick="exitToLobby()">TRỞ VỀ LOBBY</button>
        `;
        if (storyInput) storyInput.disabled = true;
        if (btnExecute) btnExecute.disabled = true;

        triggerFireworksEffect();
    } else {
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
        triggerCardShake();
        return;
    }

    storyHistory += `\n[Player]: ${actionText}`;

    currentStoryTurn++;
    if (turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;

    hintBox.innerHTML = "<div class='pulse-neon' style='font-size:13px; font-family:var(--text-pixel); text-align: center; letter-spacing:0.5px;'>MASTER_G ĐANG SOẠN KỊCH BẢN...</div>";

    terminal.innerHTML += `
        <div style="text-align: right; margin: 15px 0;">
            <span style="background: var(--neon-cyan); color: #000; padding: 10px 18px; border-radius: 12px; font-weight: 700; font-family: var(--text-mono); font-size:15px; display:inline-block; box-shadow:0 4px 15px rgba(103,232,249,0.3);">> ${actionText}</span>
        </div>
    `;
    inputEle.value = "";
    terminal.scrollTop = terminal.scrollHeight;

    const loadId = "loading-" + Date.now();
    terminal.innerHTML += `<div id="${loadId}" class="pulse-neon" style="margin-bottom: 15px; font-family:var(--text-main); font-size:15px; color:var(--neon-purple);">[GM] Đang phân tích ngữ pháp và dắt cốt truyện...</div>`;
    terminal.scrollTop = terminal.scrollHeight;

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: actionText,
            mode: 'story',
            turn: currentStoryTurn,
            history: storyHistory,
            topic_id: currentTopicId // Truyền Topic ID
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

        currentStoryTurn--;
        if (turnCounter) turnCounter.innerText = `${currentStoryTurn}/10`;
    });
}

function submitQuickQuest() {
    const inputEl = document.getElementById('quickQuestInput');
    const feedbackBox = document.getElementById('quickQuestFeedback');
    const textValue = inputEl.value.trim();

    if (!textValue) return;

    feedbackBox.style.display = "block";
    feedbackBox.innerHTML = "<span style='color: var(--neon-amber);' class='pulse-neon'>MASTER_G ĐANG KIỂM TRA CÂU...</span>";

    // Mượn tạm API evaluate với mode 'vocab' để xử lý
    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: textValue,
            mode: 'vocab'
        })
    })
    .then(res => res.json())
    .then(data => {
        const result = data.result || data;
        const score = result.score || 0;
        const color = score >= 5.0 ? 'var(--pixel-green)' : 'var(--neon-pink)';

        feedbackBox.innerHTML = `
            <div style="color: ${color}; font-family: var(--text-pixel); margin-bottom: 5px;">[ ĐIỂM: ${score}/10 ]</div>
            <div style="color: #fff;">${result.feedback}</div>
        `;

        inputEl.value = ""; // Xóa text input sau khi phản hồi thành công

        // Load lại quest để xem nó đã chuyển trạng thái chưa
        loadDailyQuests();

        // Reload xu trên UI
        fetch('/api/auth/user/me')
            .then(r => r.json())
            .then(ud => {
                const sidebarCoins = document.getElementById("sidebar-coins");
                if (sidebarCoins) sidebarCoins.innerText = ud.coins;
            });
    })
    .catch(err => {
        feedbackBox.innerHTML = "<span style='color: var(--neon-pink);'>Lỗi AI. Hãy thử lại.</span>";
    });
}

// Bắt phím Enter cho ô Quick Quest
document.addEventListener("DOMContentLoaded", () => {
    const quickInput = document.getElementById('quickQuestInput');
    if (quickInput) {
        quickInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                submitQuickQuest();
            }
        });
    }
});

/**
 * =======================================================
 * TUTORIAL MODE TÂN THỦ (MASTER G HƯỚNG DẪN)
 * =======================================================
 */
function checkAndRunTutorial(userData) {
    // Kích hoạt nếu là người mới, chưa có streak/xu và chưa bypass qua Tutorial
    if (userData.level === 'Beginner' && userData.streak === 0 && userData.coins === 0) {
        if (!localStorage.getItem('tutorial_completed')) {
            showMasterGTutorial();
        }
    }
}

function showMasterGTutorial() {
    const overlay = document.createElement("div");
    overlay.id = "tutorial-overlay";
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.85); z-index: 999999; display: flex; 
        justify-content: center; align-items: center; flex-direction: column;
    `;

    overlay.innerHTML = `
        <div style="max-width: 500px; background: rgba(15, 23, 42, 0.95); border: 3px solid var(--neon-cyan); border-radius: 16px; padding: 30px; box-shadow: 0 0 30px rgba(103, 232, 249, 0.2); position: relative; text-align: center;">
            <div class="pixel-title" style="color: var(--neon-cyan); margin-bottom: 20px; font-size: 20px;">[ SYSTEM_ALERT ] MASTER G XUẤT HIỆN!</div>
            
            <div class="pixel-text" style="font-size: 16px; margin-bottom: 20px; color: #fff; line-height: 1.6;">
                "Chà chà, một kẻ sinh tồn mới bước chân vào Global Fluent? Nghe đây tân binh:
                <br><br>
                1. <b>Góc trái</b> là bảng Nhiệm Vụ Hàng Ngày. Làm để lấy xu, không làm thì đói.
                <br>2. Ở mục <b>Lò Đúc & Học Tập</b>, ngươi phải gõ tiếng Anh để ta đánh giá. Sai là ta chê không thương tiếc!
                <br>3. Điểm danh đều đặn. Mất chuỗi thì đừng khóc lóc."
            </div>

            <button class="pixel-btn" onclick="closeTutorial()" style="background: var(--neon-purple); width: 100%; font-size: 14px; padding: 15px;">
                ĐÃ HIỂU! (BẮT ĐẦU CHƠI)
            </button>
        </div>
    `;
    document.body.appendChild(overlay);
}

function closeTutorial() {
    const overlay = document.getElementById("tutorial-overlay");
    if (overlay) overlay.remove();
    localStorage.setItem('tutorial_completed', 'true');

    // Gợi ý cho người dùng làm nhiệm vụ điểm danh luôn bằng CSS class nhấp nháy
    setTimeout(() => {
        const btnCheckin = document.getElementById("btn-checkin");
        if(btnCheckin && !btnCheckin.disabled) {
            btnCheckin.classList.add('error-shake');
            btnCheckin.style.boxShadow = "0 0 20px var(--neon-amber)";
        }
    }, 500);
}