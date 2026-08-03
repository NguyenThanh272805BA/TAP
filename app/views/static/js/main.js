const CURRENT_USERNAME_DEFAULT = "Explorer";
let activeFeature = "grammar";
let currentTopicId = 1;
let currentStoryMode = 'write'; // 'write' hoặc 'choose'
let globalStoryArchive = [];    // Lưu trữ tạm nhật ký sinh tồn để hiển thị lên Pop-up Modal

document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;

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
                        loadDailyQuests();
                        loadDashboardLeaderboard();
                        checkAndRunTutorial(data);
                    }

                    const gachaStreak = document.getElementById("gacha-streak");
                    if (gachaStreak) gachaStreak.innerText = data.streak;
                }
            })
            .catch(err => console.log("Đang tải hoặc trục trặc đồng bộ Session:", err));

        loadNotifications();
        setInterval(loadNotifications, 45000);
    }

    loadVocabQuests();
    initKeyboardShortcuts();
    initLottieLibrary();

    if (currentPath === '/story') {
        loadStoryLobby();
    }
});

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
            html += `<div style="color: ${color}; margin-bottom: 8px; font-family: var(--text-mono); border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">#${idx+1} ${u.username} - <span style="color:#fff;">${u.score} Combo</span></div>`;
        });
        lbContainer.innerHTML = html;
    });
}

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
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <textarea id="userInput" style="flex-grow: 1; min-height: 80px; max-height: 150px; overflow-y: auto; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 15px; border-radius: 12px; resize: none; box-sizing: border-box;" placeholder="Master G đang đợi câu từ vựng của bạn..."></textarea>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 12px; align-items: center;">
                    <button class="pixel-btn" onclick="submitChallenge()" style="flex: 1;">SEND_VOCAB</button>
                    <button class="pixel-btn" onclick="requestAIHint('${featureName}')" style="background: rgba(0,0,0,0.5); border: 1px solid var(--neon-amber); color: var(--neon-amber); padding: 12px; font-size: 11px;">💡 GỢI Ý</button>
                </div>
                <div id="ai-hint-box" style="display: none; margin-top: 12px; font-size: 13px; color: var(--neon-cyan); font-style: italic; background: rgba(34, 211, 238, 0.1); padding: 10px; border-radius: 6px; border-left: 3px solid var(--neon-cyan); line-height: 1.5;"></div>
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
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <textarea id="userInput" style="flex-grow: 1; min-height: 80px; max-height: 150px; overflow-y: auto; background: rgba(0,0,0,0.6); border: 2px solid var(--glass-border); color: #fff; padding: 12px; font-family: var(--text-mono); font-size: 15px; border-radius: 12px; resize: none; box-sizing: border-box;" placeholder="Nhập câu ngữ pháp tại đây..."></textarea>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 12px; align-items: center;">
                    <button class="pixel-btn" onclick="submitChallenge()" style="flex: 1;">SEND_COMMAND</button>
                    <button class="pixel-btn" onclick="requestAIHint('${featureName}')" style="background: rgba(0,0,0,0.5); border: 1px solid var(--neon-amber); color: var(--neon-amber); padding: 12px; font-size: 11px;">💡 GỢI Ý</button>
                </div>
                <div id="ai-hint-box" style="display: none; margin-top: 12px; font-size: 13px; color: var(--neon-cyan); font-style: italic; background: rgba(34, 211, 238, 0.1); padding: 10px; border-radius: 6px; border-left: 3px solid var(--neon-cyan); line-height: 1.5;"></div>
            `;
            break;
    }
    initKeyboardShortcuts();
}

function requestAIHint(mode) {
    const hintBox = document.getElementById("ai-hint-box");
    if (!hintBox) return;

    hintBox.style.display = "block";
    hintBox.innerHTML = "<span class='pulse-neon'>Đang kết nối Neural Network lấy gợi ý...</span>";

    fetch('/api/ai/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
    })
    .then(res => res.json())
    .then(data => {
        hintBox.innerHTML = data.hint;
        setTimeout(() => {
            hintBox.style.display = "none";
        }, 12000);
    })
    .catch(() => {
        hintBox.innerHTML = "<span style='color: var(--neon-pink);'>Lỗi truy xuất hệ thống Gợi ý!</span>";
    });
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
                        <button onclick="toggleVocabMark(${item.id}, this)" class="pixel-btn" style="background: rgba(0,0,0,0.4); border: 1px solid ${checkColor}; color: ${checkColor}; font-size: 10px; cursor: pointer; padding: 6px 10px; box-shadow: none; transition: 0.3s;">
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

function toggleVocabMark(vocabId, btnElement) {
    const originalHtml = btnElement.innerHTML;
    btnElement.innerHTML = "...";
    btnElement.style.opacity = "0.7";

    fetch('/api/game/vocab/toggle_memorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vocab_id: vocabId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            btnElement.innerHTML = originalHtml;
            btnElement.style.opacity = "1";
            return;
        }

        const isMemorized = data.is_memorized;
        const checkSign = isMemorized ? "[ X ]" : "[ _ ]";
        const checkColor = isMemorized ? "var(--pixel-green)" : "#64748b";

        btnElement.innerHTML = checkSign;
        btnElement.style.color = checkColor;
        btnElement.style.borderColor = checkColor;
        btnElement.style.opacity = "1";

        if (data.level_upgraded) {
            triggerFireworksEffect();
            alert(`🎉 CHÚC MỪNG! Bạn đã hoàn thành xuất sắc ải từ vựng.\nĐẲNG CẤP MỚI: ${data.current_level}`);
            const sidebarRank = document.getElementById("sidebar-rank");
            if (sidebarRank) sidebarRank.innerText = data.current_level;
            updateChibeEmotion(10.0);
        }
    }).catch(() => {
        btnElement.innerHTML = originalHtml;
        btnElement.style.opacity = "1";
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
        script.src = "[https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js](https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js)";
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
        path: '[https://assets5.lottiefiles.com/packages/lf20_obh5c7sh.json](https://assets5.lottiefiles.com/packages/lf20_obh5c7sh.json)'
    });

    animation.addEventListener('complete', () => {
        lottieContainer.remove();
    });
}

function loadStoryLobby() {
    fetch('/api/game/story/archive').then(res => res.json()).then(data => {
        const archiveContainer = document.getElementById("archive-container");
        if(!archiveContainer) return;

        globalStoryArchive = data.archive || [];

        if (globalStoryArchive.length === 0) {
            archiveContainer.innerHTML = '<div style="color: #94a3b8; font-size: 14px; font-style: italic;">Chưa có dữ liệu hành trình.</div>';
            return;
        }

        let html = '';
        globalStoryArchive.forEach(s => {
            const statusColor = s.status === 'Survived' ? 'var(--pixel-green)' : 'var(--neon-pink)';
            html += `
            <div style="background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; border-left: 3px solid ${statusColor}; margin-bottom: 10px; position: relative;">
                <strong style="color: #fff; font-size: 14px; display: block; margin-bottom: 5px;">[${s.status.toUpperCase()}] ${s.topic}</strong>
                <span style="color: #94a3b8; font-size: 11px; display: block; margin-bottom: 12px;">TIME_LOG: ${s.date}</span>
                <button class="pixel-btn" onclick="openStoryModal(${s.id})" style="background: rgba(34, 211, 238, 0.1); border: 1px solid var(--neon-cyan); color: var(--neon-cyan); padding: 8px 12px; font-size: 10px; width: 100%; box-shadow: none; transition: 0.3s;" onmouseover="this.style.background='var(--neon-cyan)'; this.style.color='#000';" onmouseout="this.style.background='rgba(34, 211, 238, 0.1)'; this.style.color='var(--neon-cyan)';">
                    📖 ĐỌC LẠI NHẬT KÝ
                </button>
            </div>`;
        });
        archiveContainer.innerHTML = html;
    });

    fetch('/api/game/story/topics').then(res => res.json()).then(topics => {
        const topicsContainer = document.getElementById("topics-container");
        if (!topicsContainer) return;

        if (!topics || topics.length === 0) {
            topicsContainer.innerHTML = '<div style="color: #94a3b8; font-size: 14px;">Admin chưa thiết lập bối cảnh nào.</div>';
            return;
        }

        const isAdmin = document.getElementById("nav-admin") && document.getElementById("nav-admin").style.display !== 'none';
        let html = '';

        topics.forEach(t => {
            const coverUrl = `/static/uploads/covers/${t.cover_image}`;
            const deleteBtn = isAdmin ? `<button onclick="deleteStoryTopic(event, ${t.id})" class="pixel-btn" style="position: absolute; top: 10px; right: 10px; background: rgba(239, 68, 68, 0.9); padding: 5px 8px; font-size: 10px; z-index: 10; box-shadow: none;">XÓA</button>` : '';

            const mode = t.play_mode || 'both';
            let buttonsHtml = '';

            if (mode === 'write' || mode === 'both') {
                buttonsHtml += `<button class="pixel-btn" style="flex: 1; font-size: 10px; padding: 10px;" onclick="startStoryWithTopic(${t.id}, '${t.title}', 'write')">📝 TỰ GÕ</button>`;
            }
            if (mode === 'choose' || mode === 'both') {
                buttonsHtml += `<button class="pixel-btn" style="flex: 1; font-size: 10px; padding: 10px; background: var(--pixel-green); color: #000;" onclick="startStoryWithTopic(${t.id}, '${t.title}', 'choose')">🎯 CHỌN ĐÁP ÁN</button>`;
            }

            html += `
            <div class="bento-card" style="padding: 15px; background: rgba(0,0,0,0.5); border: 2px solid var(--glass-border); position: relative; height: max-content;">
                ${deleteBtn}
                <img src="${coverUrl}" onerror="this.src='/static/uploads/covers/default_cover.jpg'" style="width: 100%; height: 140px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;">
                <div class="pixel-title" style="font-size: 14px; margin-bottom: 5px;">${t.title}</div>
                <div style="font-size: 11px; color: var(--neon-purple); border: 1px solid var(--neon-purple); display: inline-block; padding: 3px 8px; border-radius: 4px; margin-bottom: 15px;">${t.genre}</div>
                
                <div style="display: flex; gap: 8px;">
                    ${buttonsHtml}
                </div>
            </div>`;
        });
        topicsContainer.innerHTML = html;
    });
}

function openStoryModal(storyId) {
    const story = globalStoryArchive.find(s => s.id === storyId);
    if (!story) return;

    const modal = document.getElementById('story-modal');
    const title = document.getElementById('modal-story-title');
    const enBox = document.getElementById('modal-story-en');
    const vnBox = document.getElementById('modal-story-vn');

    const statusColor = story.status === 'Survived' ? 'var(--pixel-green)' : 'var(--neon-pink)';

    title.innerHTML = `[ <span style="color:${statusColor}">${story.status.toUpperCase()}</span> ] ${story.topic.toUpperCase()}`;
    enBox.innerHTML = story.summary_en ? story.summary_en.replace(/\n/g, '<br>') : "<span style='color: #94a3b8;'>Không có dữ liệu văn bản.</span>";
    vnBox.innerHTML = story.summary_vn ? story.summary_vn.replace(/\n/g, '<br>') : "<span style='color: #94a3b8;'>Không có dữ liệu văn bản.</span>";
    modal.style.display = 'flex';
}

function closeStoryModal() {
    const modal = document.getElementById('story-modal');
    if (modal) modal.style.display = 'none';
}

function deleteStoryTopic(event, topicId) {
    event.stopPropagation();
    if(!confirm("CẢNH BÁO TỐI CAO: Bạn có chắc muốn XÓA VĨNH VIỄN cốt truyện này? Mọi liên kết sẽ biến mất!")) return;

    fetch(`/api/admin/topics/${topicId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if(data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            loadStoryLobby();
        }
    });
}

function startStoryWithTopic(topicId, topicName, mode) {
    currentTopicId = topicId;
    currentStoryMode = mode;

    document.getElementById("story-lobby").style.display = "none";
    document.getElementById("story-battle-zone").style.display = "grid";

    const modeTag = mode === 'choose' ? '[ CHOOSE_MODE ]' : '[ HARD_MODE ]';
    document.getElementById("current-topic-name").innerText = `${topicName.toUpperCase()} ${modeTag}`;

    const writeContainer = document.getElementById('write-mode-container');
    const chooseContainer = document.getElementById('choose-mode-container');

    if (writeContainer && chooseContainer) {
        if (mode === 'choose') {
            writeContainer.style.display = 'none';
            chooseContainer.style.display = 'flex';
        } else {
            writeContainer.style.display = 'block';
            chooseContainer.style.display = 'none';
        }
    }

    initRPGStory();
}

function exitToLobby() {
    document.getElementById("story-battle-zone").style.display = "none";
    document.getElementById("story-lobby").style.display = "flex";
}

function initRPGStory() {
    const turnCounter = document.getElementById("story-turn-counter");
    if(turnCounter) turnCounter.innerText = "1/10";

    const terminal = document.getElementById("story-terminal");
    if(!terminal) return;

    terminal.innerHTML = `<div class="typing-effect" style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 14px;">[SYSTEM] Đang nạp bối cảnh và kết nối Game Master...</div>`;

    fetch('/api/ai/story/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_id: currentTopicId, mode: currentStoryMode })
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
    if(!terminal || !hintBox) return;

    terminal.innerHTML += `
        <div style="background: rgba(30, 41, 75, 0.7); border-left: 3px solid var(--neon-purple); padding: 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <div style="color: #fff; font-family: var(--text-main); font-size: 16px; margin-bottom: 10px; line-height: 1.6; font-weight:600;">${data.scene_en}</div>
            <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">${data.scene_vn}</div>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    const storyInput = document.getElementById("storyInput");
    const btnExecute = document.getElementById("btn-story-execute");

    if (data.is_end === "true" || data.is_end === true) {
        hintBox.innerHTML = `
            <div style="color: var(--pixel-green); font-family: var(--text-pixel); font-size: 14px; text-align: center; margin-bottom: 15px; letter-spacing:1px;">MISSION ACCOMPLISHED!</div>
            <div style="color: #cbd5e1; font-family: var(--text-main); font-size: 15px; text-align: center; line-height:1.6;">Hành trình sinh tồn hoàn tất. Nhật ký đã được lưu lại!</div>
            <button class="pixel-btn" style="background: var(--neon-amber); width: 100%; margin-top: 15px; padding:15px; font-size:12px;" onclick="exitToLobby()">TRỞ VỀ LOBBY</button>
        `;

        const writeMode = document.getElementById("write-mode-container");
        const chooseMode = document.getElementById("choose-mode-container");
        if(writeMode) writeMode.style.display = 'none';
        if(chooseMode) chooseMode.style.display = 'none';

        if (typeof triggerFireworksEffect === 'function') triggerFireworksEffect();
    }
    else {
        if (currentStoryMode === 'choose' && data.choices) {
            hintBox.innerHTML = `<div style="color: #94a3b8; font-family: var(--text-main); font-style: italic; font-size: 14px;">Lựa chọn quyết định sinh tử. Hãy cẩn thận.</div>`;

            let choicesHtml = '';
            data.choices.forEach(choice => {
                const safeChoice = choice.replace(/'/g, "\\'");
                choicesHtml += `<button class="pixel-btn" style="background: rgba(0,0,0,0.5); border: 1px solid var(--pixel-green); padding: 12px; text-transform: none; text-align: left; font-family: var(--text-mono); font-size: 14px;" onclick="executeStoryChoice('${safeChoice}')">${choice}</button>`;
            });

            const storyChoicesBox = document.getElementById('story-choices-box');
            if (storyChoicesBox) storyChoicesBox.innerHTML = choicesHtml;
        }
        else {
            hintBox.innerHTML = `
                <div style="color: var(--neon-cyan); font-family: var(--text-mono); font-size: 16px; font-weight: 700; line-height: 1.5; margin-bottom: 10px; letter-spacing: 0.5px;">${data.hint_en || "I need to ___ carefully."}</div>
                <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">Ý nghĩa gợi mở: ${data.hint_vn || "Tôi cần hành động cẩn trọng"}</div>
            `;
            if(storyInput) {
                storyInput.value = "";
                storyInput.disabled = false;
                storyInput.focus();
            }
            if(btnExecute) btnExecute.disabled = false;
        }
    }
}

function executeStoryChoice(choiceText) {
    executeStoryAction(choiceText);
}

function executeStoryAction(overrideText = null) {
    const inputEle = document.getElementById("storyInput");
    const actionText = overrideText || (inputEle ? inputEle.value.trim() : "");
    if (!actionText) return;

    const terminal = document.getElementById("story-terminal");
    if(!terminal) return;

    terminal.innerHTML += `
        <div style="text-align: right; margin: 15px 0;">
            <span style="background: var(--neon-cyan); color: #000; padding: 10px 18px; border-radius: 12px; font-weight: 700; font-family: var(--text-mono); font-size:15px; display:inline-block; box-shadow:0 4px 15px rgba(103,232,249,0.3);">> ${actionText}</span>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    if (currentStoryMode === 'choose') {
        const choicesBox = document.getElementById('story-choices-box');
        if(choicesBox) choicesBox.innerHTML = "<div class='pulse-neon' style='font-size:13px; font-family:var(--text-pixel); text-align: center; letter-spacing:0.5px;'>MASTER_G ĐANG SOẠN KỊCH BẢN...</div>";
    } else {
        if(inputEle) inputEle.disabled = true;
    }

    const loadId = "loading-" + Date.now();
    terminal.innerHTML += `<div id="${loadId}" class="pulse-neon" style="margin-bottom: 15px; font-family:var(--text-main); font-size:15px; color:var(--neon-purple);">[GM] Đang phân tích ngữ pháp và dắt cốt truyện...</div>`;
    terminal.scrollTop = terminal.scrollHeight;

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: actionText,
            mode: currentStoryMode === 'choose' ? 'story_choose' : 'story'
        })
    })
    .then(res => res.json())
    .then(data => {
        const loadEl = document.getElementById(loadId);
        if(loadEl) loadEl.remove();

        const result = data.result || data;

        // Cập nhật giao diện Turn đếm dựa vào phản hồi từ Backend
        const currentTurn = result.turn || 1;
        const turnCounter = document.getElementById("story-turn-counter");
        if(turnCounter) turnCounter.innerText = `${currentTurn}/10`;

        if (result.level_up_notification) {
            alert(result.level_up_notification);
            if (typeof triggerFireworksEffect === 'function') triggerFireworksEffect();
        }

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
        if(loadEl) loadEl.remove();

        const hintBox = document.getElementById("story-hint-box");
        if(hintBox) hintBox.innerHTML = "<span style='color: var(--neon-pink); font-family: var(--text-main); font-size:15px;'>[ERROR] Lỗi kết nối Game Master! Đứt cáp mạng không gian!</span>";
    });
}

function submitQuickQuest() {
    const inputEl = document.getElementById('quickQuestInput');
    const feedbackBox = document.getElementById('quickQuestFeedback');
    const textValue = inputEl.value.trim();

    if (!textValue) return;

    feedbackBox.style.display = "block";
    feedbackBox.innerHTML = "<span style='color: var(--neon-amber);' class='pulse-neon'>MASTER_G ĐANG KIỂM TRA CÂU...</span>";

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: textValue,
            mode: 'free'
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

        inputEl.value = "";

        loadDailyQuests();

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

function checkAndRunTutorial(userData) {
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

    setTimeout(() => {
        const btnCheckin = document.getElementById("btn-checkin");
        if(btnCheckin && !btnCheckin.disabled) {
            btnCheckin.classList.add('error-shake');
            btnCheckin.style.boxShadow = "0 0 20px var(--neon-amber)";
        }
    }, 500);
}

function toggleMasterG(e) {
    if(e) e.stopPropagation();
    const container = document.getElementById('master-g-container');
    const chibi = document.querySelector('.character');

    if(!container || !chibi) return;

    const isHidden = container.style.opacity === '0';

    if(isHidden) {
        container.style.width = '80px';
        container.style.transform = 'scale(1.3)';
        container.style.opacity = '1';
        chibi.classList.add('master-g-proud');
        setTimeout(() => chibi.classList.remove('master-g-proud'), 2000);
    } else {
        chibi.classList.add('master-g-mad');
        setTimeout(() => {
            container.style.transform = 'scale(0)';
            container.style.opacity = '0';
            setTimeout(() => {
                container.style.width = '0px';
                chibi.classList.remove('master-g-mad');
            }, 400);
        }, 600);
    }
}

function loadNotifications() {
    fetch('/api/game/notifications')
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('notif-badge');
            if(badge) {
                if(data.unread_count > 0) {
                    badge.innerText = data.unread_count > 9 ? '9+' : data.unread_count;
                    badge.style.display = 'block';
                    badge.classList.add('pulse-neon');
                } else {
                    badge.style.display = 'none';
                    badge.classList.remove('pulse-neon');
                }
            }

            const list = document.getElementById('notification-list');
            if(list && data.notifications) {
                if(data.notifications.length === 0) {
                    list.innerHTML = '<div style="color: #64748b; font-size: 13px; text-align: center; font-style: italic;">Hộp thư trống trơn. Đi chiến đấu đi!</div>';
                    return;
                }

                let html = '';
                data.notifications.forEach(n => {
                    const unreadStyle = n.is_read
                        ? 'opacity: 0.6; border: 1px solid rgba(255,255,255,0.05);'
                        : 'border-left: 3px solid var(--neon-pink); background: rgba(244, 114, 182, 0.05); border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);';

                    let icon = "💬";
                    if (n.type === 'LEVEL_UP') icon = "⭐";
                    if (n.type === 'ACHIEVEMENT') icon = "🏆";

                    html += `
                    <div style="background: rgba(0,0,0,0.4); padding: 14px; border-radius: 8px; transition: 0.3s; ${unreadStyle}">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; align-items: center;">
                            <strong style="color: var(--neon-cyan); font-size: 13px; font-family: var(--text-mono);">${icon} ${n.title}</strong>
                            <span style="color: #64748b; font-size: 10px; font-family: var(--text-pixel);">${n.created_at}</span>
                        </div>
                        <div style="color: #cbd5e1; font-size: 13px; line-height: 1.5; font-family: var(--text-main);">${n.message}</div>
                    </div>
                    `;
                });
                list.innerHTML = html;
            }
        })
        .catch(err => console.error("Lỗi đồng bộ Notification", err));
}

function toggleNotifications() {
    const bell = document.getElementById('notification-bell');

    if (bell && bell.getAttribute('data-is-dragging') === 'true') {
        return;
    }

    const dropdown = document.getElementById('notification-dropdown');
    if(dropdown) {
        if (dropdown.style.display === 'none') {
            if (bell) {
                dropdown.style.right = 'auto';
                dropdown.style.top = (bell.offsetTop + 60) + "px";

                let dropLeft = bell.offsetLeft - 280;
                if (dropLeft < 10) dropLeft = 10;
                dropdown.style.left = dropLeft + "px";
            }
            dropdown.style.display = 'block';
            loadNotifications();
        } else {
            dropdown.style.display = 'none';
        }
    }
}

function markAllNotificationsRead() {
    fetch('/api/game/notifications/read', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                loadNotifications();
            }
        });
}

function makeDraggable(elmnt, header) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;

    if (header) {
        header.onmousedown = dragMouseDown;
    } else {
        elmnt.onmousedown = dragMouseDown;
    }

    function dragMouseDown(e) {
        e = e || window.event;
        if (['BUTTON', 'INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;

        elmnt.style.transition = 'none';

        const startLeft = elmnt.offsetLeft;
        const startTop = elmnt.offsetTop;

        elmnt.style.left = startLeft + "px";
        elmnt.style.top = startTop + "px";
        elmnt.style.right = 'auto';
        elmnt.style.bottom = 'auto';

        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();

        elmnt.setAttribute('data-is-dragging', 'true');

        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;

        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";

        if (elmnt.id === 'notification-bell') {
            const dropdown = document.getElementById('notification-dropdown');
            if (dropdown && dropdown.style.display === 'block') {
                dropdown.style.transition = 'none';
                dropdown.style.top = (elmnt.offsetTop - pos2 + 60) + "px";

                let dropLeft = elmnt.offsetLeft - pos1 - 280;
                if (dropLeft < 10) dropLeft = 10;
                dropdown.style.left = dropLeft + "px";
                dropdown.style.right = 'auto';
            }
        }
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;

        elmnt.style.transition = '0.3s';
        if (elmnt.id === 'notification-bell') {
             const dropdown = document.getElementById('notification-dropdown');
             if (dropdown) dropdown.style.transition = '0.3s';
        }

        setTimeout(() => {
            elmnt.removeAttribute('data-is-dragging');
        }, 50);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const notifDropdown = document.getElementById("notification-dropdown");
    const notifHeader = document.getElementById("notif-header");
    const notifBell = document.getElementById("notification-bell");

    if (notifDropdown && notifHeader) {
        makeDraggable(notifDropdown, notifHeader);
    }

    if (notifBell) {
        makeDraggable(notifBell, null);
    }
});

document.addEventListener('click', function(event) {
    const bell = document.getElementById('notification-bell');
    const dropdown = document.getElementById('notification-dropdown');

    if (bell && dropdown) {
        if (dropdown.style.display === 'block' && !bell.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    }
});