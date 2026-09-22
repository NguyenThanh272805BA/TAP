const CURRENT_USERNAME_DEFAULT = "Explorer";
let activeFeature = "grammar";
let currentTopicId = 1;
let currentStoryMode = 'write'; // 'write' hoặc 'choose'
let globalStoryArchive = [];    // Lưu trữ tạm nhật ký sinh tồn để hiển thị lên Pop-up Modal

// [ PHASE 6 ] HÀM HỖ TRỢ: NHẬN DIỆN THIẾT BỊ DI ĐỘNG
function isMobileDevice() {
    return (window.innerWidth <= 768) || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// [ PHASE 6 ] HÀM HỖ TRỢ: CHẾ ĐỘ CLEAN MODE
function toggleCleanMode() {
    const isClean = document.body.classList.toggle('clean-mode');
    localStorage.setItem('clean_mode', isClean);
    const modeBtn = document.getElementById('btn-clean-mode');
    if (modeBtn) {
        modeBtn.innerHTML = isClean
        ? '<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg> <span style="font-family: var(--text-pixel); font-size: 11px;">CHẾ ĐỘ TĨNH LẶNG</span>'
        : '<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg> <span style="font-family: var(--text-pixel); font-size: 11px;">CHẾ ĐỘ TĨNH LẶNG</span>';
    }
}

// [ PHASE 6 ] HÀM HỖ TRỢ: GIẢ LẬP STREAMING TYPING CHO DỮ LIỆU TĨNH (Dự phòng)
function typeEffectSSE(elementId, text, speed = 15, callback = null) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = '';
    let i = 0;
    function type() {
        if (i < text.length) {
            let char = text.charAt(i);
            el.innerHTML += char === '\n' ? '<br>' : char;
            i++;
            el.scrollTop = el.scrollHeight;
            setTimeout(type, speed);
        } else if (callback) {
            callback();
        }
    }
    type();
}

// [ TAPIcons ] BỘ VẼ ICON BẰNG CODE (SVG VECTOR) THAY THẾ EMOJI THÔ SƠ
window.TAPIcons = {
    icons: {
        tech: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
        science: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><line x1="8.5" y1="2" x2="15.5" y2="2"/><line x1="7.5" y1="15" x2="16.5" y2="15"/></svg>',
        business: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        animal: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10Z"/></svg>',
        food: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>',
        health: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
        travel: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
        arts: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>',
        education: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
        mind: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04z"/></svg>',
        dice: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8" cy="8" r="1.5"/><circle cx="16" cy="8" r="1.5"/><circle cx="8" cy="16" r="1.5"/><circle cx="16" cy="16" r="1.5"/><circle cx="12" cy="12" r="1.5"/></svg>',
        shield: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        potion: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
        hourglass: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></svg>',
        chest: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
        quest: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
        book: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
        star: '<svg class="tap-icon-svg" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    },

    get(name, size = 22, className = "") {
        const svgContent = this.icons[name] || this.icons.book;
        return `<span class="tap-icon ${className}" style="width: ${size}px; height: ${size}px;">${svgContent}</span>`;
    },

    getTopicIcon(theme, size = 26) {
        const t = (theme || '').toUpperCase();
        if (t.includes('TECH') || t.includes('AI') || t.includes('CÔNG NGHỆ') || t.includes('ROBOT') || t.includes('QUANTUM') || t.includes('CYBER'))
            return this.get('tech', size, 'tap-icon-glow-cyan');
        if (t.includes('SCIENCE') || t.includes('KHOA HỌC') || t.includes('ASTRONOMY') || t.includes('PHYSIC') || t.includes('BIO'))
            return this.get('science', size, 'tap-icon-glow-cyan');
        if (t.includes('BUSINESS') || t.includes('KINH DOANH') || t.includes('MARKETING') || t.includes('FINANCE') || t.includes('LOGISTICS'))
            return this.get('business', size, 'tap-icon-glow-amber');
        if (t.includes('ANIMAL') || t.includes('ĐỘNG VẬT') || t.includes('MARINE') || t.includes('WILD'))
            return this.get('animal', size, 'tap-icon-glow-green');
        if (t.includes('FOOD') || t.includes('CULINARY') || t.includes('ẨM THỰC') || t.includes('DINH DƯỠNG'))
            return this.get('food', size, 'tap-icon-glow-amber');
        if (t.includes('HEALTH') || t.includes('Y TẾ') || t.includes('NEURO') || t.includes('MEDIC') || t.includes('EPIDEMI'))
            return this.get('health', size, 'tap-icon-glow-pink');
        if (t.includes('TRAVEL') || t.includes('DU LỊCH') || t.includes('DIPLOMACY') || t.includes('GLOBAL') || t.includes('CLIMATE'))
            return this.get('travel', size, 'tap-icon-glow-cyan');
        if (t.includes('ART') || t.includes('CINEMA') || t.includes('MUSIC') || t.includes('NGHỆ THUẬT') || t.includes('WRITING'))
            return this.get('arts', size, 'tap-icon-glow-pink');
        if (t.includes('MIND') || t.includes('PSYCHOLOGY') || t.includes('PHILOSOPHY') || t.includes('TÂM LÝ'))
            return this.get('mind', size, 'tap-icon-glow-pink');
        if (t.includes('SCHOOL') || t.includes('TRƯỜNG') || t.includes('GIÁO DỤC') || t.includes('EDUCATION'))
            return this.get('education', size, 'tap-icon-glow-cyan');
        return this.get('book', size, 'tap-icon-glow-cyan');
    }
};

document.addEventListener("DOMContentLoaded", () => {

    // Khôi phục trạng thái Clean Mode
    if (localStorage.getItem('clean_mode') === 'true') {
        document.body.classList.add('clean-mode');
        const modeBtn = document.getElementById('btn-clean-mode');
        if(modeBtn) modeBtn.innerHTML = '<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg> <span style="font-family: var(--text-pixel); font-size: 11px;">CHẾ ĐỘ TĨNH LẶNG</span>';
    }

    const currentPath = window.location.pathname;

    // Cập nhật Active Link trên Sidebar Navigation
    document.querySelectorAll('#main-sidebar-nav .nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href) {
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        }
    });

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
                    const sidebarTitle = document.getElementById("sidebar-title");
                    const sidebarAvatarContainer = document.getElementById("sidebar-avatar-container");
                    const sidebarAvatarImg = document.getElementById("sidebar-avatar-img");

                    if (sidebarUser) sidebarUser.innerText = data.username;
                    if (sidebarRank) sidebarRank.innerText = data.level;
                    if (sidebarStreak) sidebarStreak.innerText = data.streak;
                    if (sidebarCoins) sidebarCoins.innerText = data.coins;
                    if (sidebarTitle && data.equipped_title) sidebarTitle.innerText = data.equipped_title;
                    if (sidebarAvatarContainer && data.equipped_frame) {
                        sidebarAvatarContainer.className = `avatar-container ${data.equipped_frame}`;
                    }
                    if (sidebarAvatarImg && data.avatar) {
                        sidebarAvatarImg.src = `/static/uploads/avatars/${data.avatar}`;
                    }

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
    const container = document.getElementById("daily-quests-container");
    if(!container) return;

    fetch('/api/game/quests/today')
    .then(res => {
        if (!res.ok) throw new Error("HTTP error " + res.status);
        return res.json();
    })
    .then(data => {
        let html = '';
        if (!data.quests || data.quests.length === 0) {
            container.innerHTML = '<div style="color: var(--pixel-green); font-size: 14px;">Bạn đã hoàn thành mọi nhiệm vụ hôm nay!</div>';
            return;
        }

        data.quests.forEach((q, idx) => {
            const statusColor = q.is_completed ? "var(--pixel-green)" : "var(--glass-border)";
            const statusText = q.is_completed ? "[ ĐÃ XONG ]" : "[ ĐANG CHỜ ]";
            const cefrBadge = q.cefr_level ? `<span style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(34,211,238,0.15); color: var(--neon-cyan); font-weight: bold; margin-left: 6px;">${q.cefr_level}</span>` : '';
            const questDesc = q.type === 'NEW' ? `Học từ mới: <strong style="color: var(--neon-cyan);">${q.word}</strong>${cefrBadge}` : `Ôn tập từ: <strong style="color: var(--neon-amber);">${q.word}</strong>${cefrBadge}`;
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
    .catch(err => {
        console.error("Lỗi tải Daily Quests:", err);
        container.innerHTML = '<div style="color: #94a3b8; font-size: 13px;">Chưa thể đồng bộ nhiệm vụ lúc này.</div>';
    });
}

function loadDashboardLeaderboard() {
    const lbContainer = document.getElementById("dashboard-leaderboard");
    if (!lbContainer) return;
    fetch('/api/leaderboard?category=overall&limit=3')
    .then(res => {
        if (!res.ok) throw new Error("HTTP error " + res.status);
        return res.json();
    })
    .then(data => {
        const list = data.leaderboard || [];
        if (list.length === 0) {
            lbContainer.innerHTML = '<span style="color: #94a3b8; font-size: 12px;">Chưa có dữ liệu cao thủ.</span>';
            return;
        }
        let html = '';
        list.forEach((u, idx) => {
            let color = idx === 0 ? "var(--neon-amber)" : (idx === 1 ? "#cbd5e1" : "#d97706");
            const avatarSrc = u.avatar ? `/static/uploads/avatars/${u.avatar}` : `/static/uploads/avatars/default_avatar.png`;
            const frameClass = u.equipped_frame || 'frame-default';
            const titleText = u.equipped_title || 'Tân Binh Ngơ Ngác';

            html += `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-family: var(--text-mono); border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                    <span style="color: ${color}; font-weight: bold; font-size: 13px; width: 22px;">#${idx+1}</span>
                    <div class="avatar-container ${frameClass}" style="width: 32px; height: 32px; flex-shrink: 0; padding: 2px;">
                        <img src="${avatarSrc}" class="avatar-img" onerror="this.src='/static/uploads/covers/default_cover.jpg'">
                    </div>
                    <div style="min-width: 0; overflow: hidden;">
                        <div style="color: #fff; font-size: 13px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${u.username}</div>
                        <div style="font-size: 9.5px; color: var(--neon-pink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">« ${titleText} »</div>
                    </div>
                </div>
                <div style="text-align: right; flex-shrink: 0;">
                    <div style="color: var(--pixel-green); font-size: 12px; font-weight: bold;">${u.primary_value} ${u.unit}</div>
                    <div style="font-size: 9px; color: #64748b;">${u.current_band} • Lv.${u.arena_stage}</div>
                </div>
            </div>`;
        });
        lbContainer.innerHTML = html;
    })
    .catch(err => {
        console.error("Lỗi tải Leaderboard:", err);
        lbContainer.innerHTML = '<span style="color: #94a3b8; font-size: 12px;">Đang đồng bộ bảng xếp hạng...</span>';
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

// ==============================================================
// [ PHASE 6 ] KIẾN TRÚC STREAMING THỜI GIAN THỰC (SSE) & FORMATTER SẠCH SẼ
// ==============================================================

function renderStructuredFeedback(rawText) {
    if (!rawText) return "";
    let clean = rawText;
    // 1. Xóa toàn bộ ký tự markdown thừa (**bold**, *italic*, > quotes, leftover asterisks)
    clean = clean.replace(/\*\*(.*?)\*\*/g, '$1');
    clean = clean.replace(/\*(.*?)\*/g, '$1');
    clean = clean.replace(/^>\s*/gm, '');
    clean = clean.replace(/\*\*/g, '');

    // 2. Định dạng các đề mục sư phạm rõ ràng, màu sắc chuyên nghiệp
    clean = clean.replace(/\[ĐÁNH GIÁ TỔNG QUAN\]/g, '<div style="color: var(--neon-cyan); font-weight: 700; margin-top: 10px; margin-bottom: 4px; font-size: 13px; letter-spacing: 0.5px;">[ ĐÁNH GIÁ TỔNG QUAN ]</div>');
    clean = clean.replace(/\[CHI TIẾT LỖI SAI & PHÂN TÍCH\]/g, '<div style="color: var(--neon-pink); font-weight: 700; margin-top: 12px; margin-bottom: 4px; font-size: 13px; letter-spacing: 0.5px;">[ CHI TIẾT LỖI SAI & PHÂN TÍCH ]</div>');
    clean = clean.replace(/\[CÂU CHUẨN ĐỀ XUẤT\]/g, '<div style="color: var(--pixel-green); font-weight: 700; margin-top: 12px; margin-bottom: 4px; font-size: 13px; letter-spacing: 0.5px;">[ CÂU CHUẨN ĐỀ XUẤT ]</div>');
    clean = clean.replace(/\[GÓP Ý & HƯỚNG DẪN HOÀN THIỆN\]/g, '<div style="color: var(--neon-amber); font-weight: 700; margin-top: 12px; margin-bottom: 4px; font-size: 13px; letter-spacing: 0.5px;">[ GÓP Ý & HƯỚNG DẪN HOÀN THIỆN ]</div>');
    clean = clean.replace(/\[NĂNG LỰC TỪ VỰNG & CEFR\]/g, '<div style="color: var(--neon-purple); font-weight: 700; margin-top: 12px; margin-bottom: 4px; font-size: 13px; letter-spacing: 0.5px;">[ NĂNG LỰC TỪ VỰNG & CEFR ]</div>');

    return clean.replace(/\n/g, '<br>');
}

function submitChallenge(modeParam) {
    const userInputField = document.getElementById("userInput");
    const aiResponseBox = document.getElementById("aiResponseBox");
    const aiFeedbackDiv = document.getElementById("aiFeedback");

    if (!userInputField || !aiResponseBox || !aiFeedbackDiv) return;

    const textValue = userInputField.value.trim();
    if (!textValue) {
        triggerCardShake();
        return;
    }

    const currentMode = modeParam || activeFeature || 'grammar';

    userInputField.disabled = true; // Khóa an toàn chống spam click
    aiResponseBox.style.display = "block";
    aiFeedbackDiv.innerHTML = `
        <div id="aiFeedbackLoading" class="pulse-neon" style="color: var(--neon-cyan); font-size: 14px; margin-bottom: 10px;">
            <span class="typing-effect">🤖 Master G đang chấm điểm & phân tích câu ngữ pháp...</span>
        </div>
        <div id="aiFeedbackScore" style="display:none; font-family: var(--text-pixel); margin-bottom: 10px;"></div>
        <div id="aiFeedbackText" style="line-height: 1.6; color: inherit; font-family: var(--text-main); font-size:16px;"></div>
    `;
    const loadingBox = document.getElementById('aiFeedbackLoading');
    const scoreBox = document.getElementById('aiFeedbackScore');
    const textBox = document.getElementById('aiFeedbackText');
    let accumulatedText = "";

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textValue, mode: currentMode })
    })
    .then(async response => {
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || `Lỗi phản hồi từ máy chủ (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = ""; // BỘ ĐỆM

        while(true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {stream: true});
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for(let part of parts) {
                if (part.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(part.substring(6));

                        if (loadingBox && loadingBox.style.display !== 'none') {
                            loadingBox.style.display = 'none';
                        }

                        if (data.type === 'meta') {
                            scoreBox.innerHTML = `RATING_SCORE: ${data.score}/10`;
                            scoreBox.style.display = 'block';
                            scoreBox.style.color = data.score >= 5.0 ? 'var(--pixel-green)' : 'var(--neon-pink)';
                            updateChibeEmotion(data.score);
                            if (data.quest_notification) {
                                scoreBox.innerHTML += `<br><span style="color: var(--pixel-green);">[+] ${data.quest_notification}</span>`;
                            }
                        }
                        else if (data.type === 'chunk') {
                            accumulatedText += data.text;
                            textBox.innerHTML = renderStructuredFeedback(accumulatedText);
                            textBox.parentNode.scrollTop = textBox.parentNode.scrollHeight;
                        }
                        else if (data.type === 'levelup') {
                            triggerFireworksEffect();
                            alert(`ĐẲNG CẤP MỚI: BẠN VỪA THĂNG CẤP LÊN '${data.rank}'!`);
                        }
                        else if (data.type === 'error') {
                            textBox.innerHTML = `<span style="color: var(--neon-pink);">[ERROR] ${data.message}</span>`;
                        }
                    } catch (e) {
                        console.error("Parse Error:", e);
                    }
                }
            }
        }
        if (loadingBox) loadingBox.style.display = 'none';
        userInputField.disabled = false;
        userInputField.value = "";
        userInputField.focus();
    })
    .catch(error => {
        triggerCardShake();
        if (loadingBox) loadingBox.style.display = 'none';
        aiFeedbackDiv.innerHTML = `<span style='color: var(--neon-pink); font-family: var(--text-mono);'>[LỖI]: ${error.message || 'Mất kết nối tới Server.'}</span>`;
        userInputField.disabled = false;
        userInputField.focus();
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
                <strong style="color: inherit; font-size: 14px; display: block; margin-bottom: 5px;">[${s.status.toUpperCase()}] ${s.topic}</strong>
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
    const speakBtn = document.getElementById('btn-speak-modal-story');

    const statusColor = story.status === 'Survived' ? 'var(--pixel-green)' : 'var(--neon-pink)';

    title.innerHTML = `[ <span style="color:${statusColor}">${story.status.toUpperCase()}</span> ] ${story.topic.toUpperCase()}`;
    enBox.innerHTML = story.summary_en ? story.summary_en.replace(/\n/g, '<br>') : "<span style='color: #94a3b8;'>Không có dữ liệu văn bản.</span>";
    vnBox.innerHTML = story.summary_vn ? story.summary_vn.replace(/\n/g, '<br>') : "<span style='color: #94a3b8;'>Không có dữ liệu văn bản.</span>";

    if (speakBtn) {
        speakBtn.setAttribute('data-speak', story.summary_en || '');
    }

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
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px;">
                <div style="color: inherit; font-family: var(--text-main); font-size: 16px; line-height: 1.6; font-weight:600;">${data.scene_en}</div>
                <button class="btn-speak-audio" data-speak="${data.scene_en.replace(/"/g, '&quot;')}" title="Nghe đọc đoạn văn này" style="flex-shrink: 0; padding: 4px 8px;">
                    <span class="speaker-icon">🔊</span>
                    <span class="wave-container"><span class="wave-bar"></span><span class="wave-bar"></span><span class="wave-bar"></span></span>
                </button>
            </div>
            <div style="color: #94a3b8; font-family: var(--text-main); font-size: 14px; font-style: italic; line-height: 1.5;">${data.scene_vn}</div>
        </div>
    `;
    terminal.scrollTop = terminal.scrollHeight;

    const storyInput = document.getElementById("storyInput");
    const btnExecute = document.getElementById("btn-story-execute");

    if (data.is_end === "true" || data.is_end === true) {
        hintBox.innerHTML = `
            <div style="color: var(--pixel-green); font-family: var(--text-pixel); font-size: 14px; text-align: center; margin-bottom: 15px; letter-spacing:1px;">MISSION ACCOMPLISHED!</div>
            <div style="color: inherit; font-family: var(--text-main); font-size: 15px; text-align: center; line-height:1.6;">Hành trình sinh tồn hoàn tất. Nhật ký đã được lưu lại!</div>
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

    // 1. In hành động của người chơi
    terminal.insertAdjacentHTML('beforeend', `
        <div style="text-align: right; margin: 15px 0;">
            <span style="background: var(--neon-cyan); color: #000; padding: 10px 18px; border-radius: 12px; font-weight: 700; font-family: var(--text-mono); font-size:15px; display:inline-block; box-shadow:0 4px 15px rgba(103,232,249,0.3);">> ${actionText}</span>
        </div>
    `);
    terminal.scrollTop = terminal.scrollHeight;

    if (currentStoryMode === 'choose') {
        const choicesBox = document.getElementById('story-choices-box');
        if(choicesBox) choicesBox.innerHTML = "<div class='pulse-neon' style='font-size:13px; font-family:var(--text-pixel); text-align: center;'>[SYSTEM] ĐANG CHUẨN BỊ KỊCH BẢN...</div>";
    } else {
        if(inputEle) inputEle.disabled = true;
    }

    // 2. Tạo hiệu ứng AI Đang phân tích và Box chứa truyện
    const loadId = "loading-" + Date.now();
    const gmResponseId = "gm-" + Date.now();

    terminal.insertAdjacentHTML('beforeend', `
        <div id="${loadId}" class="pulse-neon" style="margin-bottom: 15px; font-family:var(--text-main); font-size:14px; color:var(--neon-purple);">
            <span class="typing-effect">[LOCAL AI] Đang chấm điểm ngữ pháp & trích xuất ý định...</span>
        </div>
        <div id="${gmResponseId}" style="color: inherit; font-family: var(--text-main); font-size: 15px; line-height: 1.6; margin-bottom: 15px; padding: 16px; background: rgba(30, 41, 75, 0.7); border-left: 3px solid var(--neon-purple); border-radius: 8px; display: none;"></div>
    `);
    terminal.scrollTop = terminal.scrollHeight;

    const loadEl = document.getElementById(loadId);
    const gmDiv = document.getElementById(gmResponseId);
    let fullResponse = "";

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: actionText, mode: currentStoryMode === 'choose' ? 'story_choose' : 'story' })
    })
    .then(async response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while(true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for(let part of parts) {
                if (part.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(part.substring(6));

                        if (data.type === 'meta') {
                            // Cập nhật trạng thái loading thành "Hoàn tất"
                            if (loadEl) {
                                loadEl.innerHTML = `<span style="color: var(--pixel-green);">[LOCAL AI] Đã phân tích xong! Chuyển giao Game Master...</span>`;
                                setTimeout(() => loadEl.remove(), 1200);
                            }

                            const scoreColor = data.score >= 5.0 ? "var(--pixel-green)" : "var(--neon-pink)";
                            // Chèn điểm số an toàn không làm vỡ DOM
                            gmDiv.insertAdjacentHTML('beforebegin', `
                                <div style="font-size: 12px; color: ${scoreColor}; font-family: var(--text-pixel); margin-bottom: 10px; text-align: right; letter-spacing:0.5px;">
                                    [LOCAL GEC RATING: ${data.score}/10]
                                </div>
                            `);
                            gmDiv.style.display = "block";
                        }
                        else if (data.type === 'chunk') {
                            // Stream dữ liệu text
                            fullResponse += data.text;
                            // Regex mở rộng để bắt các tag có hoặc không có dấu hai chấm ":"
                            let formatted = fullResponse
                                .replace(/\[EN\]:?/g, '<strong style="color: var(--neon-cyan); font-size: 16px;">[EN]</strong>')
                                .replace(/\[VN\]:?/g, '<br><br><strong style="color: #94a3b8;">[VN]</strong>')
                                .replace(/\[CHOICES\]:?/g, '<br><br><strong style="color: var(--neon-amber);">[CHOICES]</strong>')
                                .replace(/\[HINT\]:?/g, '<br><br><strong style="color: var(--neon-amber);">[HINT]</strong>');
                            gmDiv.innerHTML = formatted;
                            terminal.scrollTop = terminal.scrollHeight;
                        }
                        else if (data.type === 'done') {
                            // Render nút bấm khi Stream xong
                            if (currentStoryMode === 'choose') {
                                let choicesMatch = fullResponse.match(/\[CHOICES\]:?\s*(.*)/);
                                if (choicesMatch && choicesMatch[1]) {
                                    let choices = choicesMatch[1].split('|').map(s => s.trim());
                                    let choicesHtml = '';
                                    choices.forEach(c => {
                                        if(c) choicesHtml += `<button class="pixel-btn" style="background: rgba(0,0,0,0.5); border: 1px solid var(--pixel-green); padding: 12px; text-transform: none; text-align: left; font-family: var(--text-mono); font-size: 14px; margin-bottom: 5px; display: block; width: 100%; transition: 0.3s;" onmouseover="this.style.background='rgba(110, 231, 183, 0.2)'" onmouseout="this.style.background='rgba(0,0,0,0.5)'" onclick="executeStoryAction('${c.replace(/'/g, "\\'")}')">${c}</button>`;
                                    });
                                    const choicesBox = document.getElementById('story-choices-box');
                                    if(choicesBox) choicesBox.innerHTML = choicesHtml;
                                }
                            } else {
                                if(inputEle) { inputEle.disabled = false; inputEle.value = ""; inputEle.focus(); }
                            }

                            if (data.turn) {
                                const turnCounter = document.getElementById("story-turn-counter");
                                if(turnCounter) turnCounter.innerText = `${data.turn}/10`;
                            }
                        }
                        else if (data.type === 'error') {
                            gmDiv.style.display = "block";
                            gmDiv.innerHTML += `<br><span style='color: var(--neon-pink);'>[SYSTEM ERROR] ${data.message}</span>`;
                            if(inputEle) { inputEle.disabled = false; inputEle.focus(); }
                        }
                    } catch (e) {
                        console.error("Lỗi parse SSE:", e, part);
                    }
                }
            }
        }
    })
    .catch(err => {
        const loadEl = document.getElementById(loadId);
        if(loadEl) loadEl.remove();
        gmDiv.style.display = "block";
        gmDiv.innerHTML += "<br><span style='color: var(--neon-pink);'>[ERROR] Mất kết nối tới Hệ thống Lõi!</span>";
        if(inputEle) { inputEle.disabled = false; inputEle.focus(); }
    });
}

function submitQuickQuest() {
    const inputEl = document.getElementById('quickQuestInput');
    const feedbackBox = document.getElementById('quickQuestFeedback');
    const textValue = inputEl.value.trim();
    if (!textValue) return;

    inputEl.disabled = true;
    feedbackBox.style.display = "block";
    feedbackBox.innerHTML = `
        <div id="quickQuestLoading" class="pulse-neon" style="color: var(--neon-purple); font-size: 13px; margin-bottom: 5px;">
            <span class="typing-effect">🤖 Master G đang chấm câu nhiệm vụ...</span>
        </div>
        <div id="quickQuestScore" style="display:none; font-family: var(--text-pixel); margin-bottom: 5px;"></div>
        <div id="quickQuestText" style="color: inherit; line-height:1.5;"></div>
    `;
    const loadingDiv = document.getElementById('quickQuestLoading');
    const scoreDiv = document.getElementById('quickQuestScore');
    const textDiv = document.getElementById('quickQuestText');
    let accumulatedText = "";

    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textValue, mode: 'free' })
    })
    .then(async res => {
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `Lỗi máy chủ (${res.status})`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = ""; // BỘ ĐỆM

        while(true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {stream: true});
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for(let part of parts) {
                if (part.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(part.substring(6));

                        if (loadingDiv && loadingDiv.style.display !== 'none') {
                            loadingDiv.style.display = 'none';
                        }

                        if (data.type === 'meta') {
                            scoreDiv.style.display = 'block';
                            scoreDiv.style.color = data.score >= 5.0 ? 'var(--pixel-green)' : 'var(--neon-pink)';
                            scoreDiv.innerHTML = `[ ĐIỂM: ${data.score}/10 ]`;
                            if(data.quest_notification) alert(data.quest_notification);
                        }
                        else if (data.type === 'chunk') {
                            accumulatedText += data.text;
                            textDiv.innerHTML = renderStructuredFeedback(accumulatedText);
                        }
                    } catch (e) {
                        console.error("Parse Error:", e);
                    }
                }
            }
        }
        if (loadingDiv) loadingDiv.style.display = 'none';
        inputEl.disabled = false;
        inputEl.value = "";
        loadDailyQuests();
    })
    .catch(err => {
        if (loadingDiv) loadingDiv.style.display = 'none';
        feedbackBox.innerHTML = `<span style='color: var(--neon-pink); font-family: var(--text-mono); font-size:12px;'>[LỖI]: ${err.message || 'Sự cố kết nối máy chủ!'}</span>`;
        inputEl.disabled = false;
    });
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
            
            <div class="pixel-text" style="font-size: 16px; margin-bottom: 20px; color: inherit; line-height: 1.6;">
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
                        <div style="color: inherit; font-size: 13px; line-height: 1.5; font-family: var(--text-main);">${n.message}</div>
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
                // Kiểm tra Mobile để thả notification ra giữa thay vì bị lệch
                if (isMobileDevice()) {
                    dropdown.style.top = "10vh";
                    dropdown.style.left = "5vw";
                    dropdown.style.width = "90vw";
                } else {
                    dropdown.style.top = (bell.offsetTop + 60) + "px";
                    let dropLeft = bell.offsetLeft - 280;
                    if (dropLeft < 10) dropLeft = 10;
                    dropdown.style.left = dropLeft + "px";
                }
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

// [ PHASE 6 ] VÔ HIỆU HÓA DRAG DROP TRÊN MOBILE TRÁNH LỖI SCROLL
function makeDraggable(elmnt, header) {
    if (isMobileDevice()) {
        if (elmnt.id === 'notification-bell') {
            elmnt.style.position = 'fixed';
            elmnt.style.bottom = '20px';
            elmnt.style.right = '20px';
            elmnt.style.top = 'auto';
            elmnt.style.left = 'auto';
        }
        return; // Hủy hoàn toàn script drag/drop trên Mobile
    }

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

/* =========================================================================
   [ AUDIO PRONUNCIATION ENGINE (WEB SPEECH API) ]
   Hỗ trợ phát âm từ vựng, câu ví dụ và đoạn văn với SpeechSynthesis.
   ========================================================================= */
const TAPAudio = {
    synth: ('speechSynthesis' in window) ? window.speechSynthesis : null,
    currentUtterance: null,
    currentButton: null,
    rate: 1.0,
    voice: null,

    init() {
        if (!this.synth) {
            console.warn("[TAP Audio] Web Speech API không được hỗ trợ trên trình duyệt này.");
            return;
        }

        const pickVoice = () => {
            const voices = this.synth.getVoices();
            if (!voices || voices.length === 0) return;
            const preferredVoices = ['Google US English', 'Samantha', 'Microsoft David', 'Microsoft Zira', 'Daniel', 'Karen'];
            let foundVoice = null;
            for (let name of preferredVoices) {
                foundVoice = voices.find(v => v.name && v.name.includes(name));
                if (foundVoice) break;
            }
            if (!foundVoice) {
                foundVoice = voices.find(v => v.lang && (v.lang.startsWith('en-US') || v.lang.startsWith('en-GB') || v.lang.startsWith('en')));
            }
            this.voice = foundVoice || voices[0];
        };

        pickVoice();
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = pickVoice;
        }

        // Global Event Delegation cho tất cả các nút có class .btn-speak-audio
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-speak-audio');
            if (btn) {
                e.stopPropagation();
                const text = btn.getAttribute('data-speak') || btn.innerText;
                if (btn.classList.contains('audio-playing')) {
                    this.stop();
                } else {
                    this.speak(text, btn);
                }
            }
        });
    },

    speak(text, buttonEl = null, customRate = null) {
        if (!this.synth) {
            alert("Trình duyệt không hỗ trợ Web Speech API!");
            return;
        }

        this.stop();

        if (!text || !text.trim()) return;

        // Xóa các thẻ HTML nếu có trong chuỗi
        const cleanText = text.replace(/<[^>]*>?/gm, '').trim();
        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-US';
        utterance.rate = customRate || this.rate;
        utterance.pitch = 1.0;
        if (this.voice) {
            utterance.voice = this.voice;
        }

        if (buttonEl) {
            this.currentButton = buttonEl;
            buttonEl.classList.add('audio-playing');
        }

        utterance.onend = () => {
            this.resetActiveState();
        };

        utterance.onerror = (e) => {
            console.error("[TAP Audio Error]", e);
            this.resetActiveState();
        };

        this.currentUtterance = utterance;
        this.synth.speak(utterance);
    },

    stop() {
        if (this.synth) {
            this.synth.cancel();
        }
        this.resetActiveState();
    },

    resetActiveState() {
        if (this.currentButton) {
            this.currentButton.classList.remove('audio-playing');
            this.currentButton = null;
        }
        document.querySelectorAll('.btn-speak-audio.audio-playing').forEach(b => b.classList.remove('audio-playing'));
    },

    toggleSpeed(badgeEl = null) {
        this.rate = (this.rate === 1.0) ? 0.75 : 1.0;
        const text = this.rate === 1.0 ? '1.0x' : '0.75x';
        if (badgeEl) {
            badgeEl.innerText = text;
        }
        return this.rate;
    }
};

// Tự động khởi chạy
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TAPAudio.init());
} else {
    TAPAudio.init();
}