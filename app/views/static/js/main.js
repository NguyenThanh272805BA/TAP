/* app/static/js/main.js */

// Giả định User ID hiện tại để test luồng (Khi có Auth Portal sẽ lấy từ Session/LocalStorage)
const CURRENT_USER_ID = localStorage.getItem("user_id") || 1;
const CURRENT_USERNAME = localStorage.getItem("username") || "Explorer";
document.addEventListener("DOMContentLoaded", () => {
    // Khởi tạo trạng thái giao diện ban đầu
    const nameSpan = document.querySelector("#status-card .pixel-text span");
    if(nameSpan) nameSpan.textContent = CURRENT_USERNAME;

    loadVocabQuests();
    loadPlayerStatus();
    loadVocabQuests();
    // Bổ sung sự kiện lắng nghe phím Enter trong ô Textarea để bấm gửi lệnh nhanh
    const userInput = document.getElementById("userInput");
    if (userInput) {
        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitChallenge();
            }
        });
    }
});

/**
 * 1. Tải trạng thái người chơi (PLAYER_STATUS) từ Backend
 */
function loadPlayerStatus() {
    // Gửi yêu cầu lấy thông tin tổng quan của User (Tạm thời map thông qua Game Controller hoặc mock data dựa theo DB)
    // Để đồng bộ chính xác với giao diện HTML hiện tại của bạn:
    const streakElement = document.querySelector(".pulse-neon");

    // Đoạn này cấu trúc sẵn sàng để Fetch thông tin User từ Route tương lai
    console.log("Initializing Player Status for User ID:", CURRENT_USER_ID);
}

/**
 * 2. Tải danh sách từ vựng thời gian thực (VOCAB_QUESTS)
 * Áp dụng Gamification: Từ khóa sẽ hiển thị, từ chưa mở khóa xử lý render thuần không chèn icon văn bản bừa bãi
 */
function loadVocabQuests() {
    const vocabContainer = document.querySelector(".card-tall .pixel-text");
    if (!vocabContainer) return;

    fetch('/api/game/vocabularies', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Không thể tải danh sách từ vựng.");
        return response.json();
    })
    .then(data => {
        if (!data || data.length === 0) {
            vocabContainer.innerHTML = "Kho từ vựng trống. Hãy chạy file seed để nạp dữ liệu!";
            return;
        }

        // Tạo khung thẻ danh sách HTML thuần
        let htmlContent = '<ul style="list-style: none; padding: 0; margin: 0;">';

        data.forEach(item => {
            htmlContent += `
                <li style="margin-bottom: 12px; padding: 8px; border-bottom: 1px solid var(--pixel-border); display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <strong style="color: var(--neon-cyan);">${item.word}</strong> 
                        <span style="font-size: 14px; color: #aaa; display: block;">${item.meaning}</span>
                    </div>
                    <div>
                        ${item.is_unlocked 
                            ? `<span class="status-tag unlocked" style="color: var(--pixel-green); font-family: var(--text-pixel); font-size: 10px;">OPEN</span>` 
                            : `<span class="status-tag locked" style="color: var(--neon-pink); font-family: var(--text-pixel); font-size: 10px;">LOCK</span>`
                        }
                    </div>
                </li>
            `;
        });

        htmlContent += '</ul>';
        vocabContainer.innerHTML = htmlContent;
    })
    .catch(error => {
        console.error("Lỗi hệ thống từ vựng:", error);
        vocabContainer.innerHTML = "<span style='color: var(--neon-pink);'>Lỗi nạp Quest!</span>";
    });
}

/**
 * 3. Gửi bài làm lên hệ thống AI (BATTLE_ZONE)
 * Nhận chuỗi chửi xéo xắt từ Master G và hiển thị thời gian thực với hiệu ứng rung lắc màn hình nếu bị điểm thấp
 */
function submitChallenge() {
    const userInputField = document.getElementById("userInput");
    const aiResponseBox = document.getElementById("aiResponseBox");
    const aiFeedbackDiv = document.getElementById("aiFeedback");

    if (!userInputField || !aiResponseBox || !aiFeedbackDiv) return;

    const textValue = userInputField.value.trim();

    if (!textValue) {
        triggerCardShake();
        alert("Vui lòng nhập câu trả lời trước khi gửi lệnh!");
        return;
    }

    // Hiển thị trạng thái đang xử lý (Loading) đậm chất terminal cổ điển
    aiResponseBox.style.display = "block";
    aiFeedbackDiv.innerHTML = "<span class='loading-text' style='color: var(--neon-amber);'>MASTER_G ĐANG SOI MÓI...</span>";

    // Gửi dữ liệu qua Fetch API đến AI Controller
    fetch('/api/ai/evaluate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: CURRENT_USER_ID,
            text: textValue
        })
    })
    .then(response => {
        if (!response.ok) throw new Error("Kết nối API chấm điểm thất bại.");
        return response.json();
    })
    .then(data => {
        // Cấu trúc dữ liệu nhận về từ ai_controller.py sau khi bóc tách JSON từ Gemini 2.5 Flash
        const feedback = data.feedback || data.ai_feedback || "Hệ thống không trả về nhận xét.";
        const score = data.score !== undefined ? data.score : 0;

        // Cập nhật giao diện Chatbox của Master G công bằng và bộc trực
        let scoreColor = "var(--pixel-green)";
        if (score < 5.0) {
            scoreColor = "var(--neon-pink)";
            triggerCardShake(); // Điểm thấp (bị chửi) -> Rung lắc card Bento để cảnh cáo người chơi
        } else if (score < 8.0) {
            scoreColor = "var(--neon-amber)";
        }

        aiFeedbackDiv.innerHTML = `
            <div style="margin-bottom: 8px; font-size: 16px; line-height: 1.4; color: #ffffff;">
                ${feedback}
            </div>
            <div style="font-family: var(--text-pixel); font-size: 14px; color: ${scoreColor}; margin-top: 10px;">
                STATUS_SCORE: <span>${score}</span> / 10
            </div>
        `;

        // Làm sạch ô nhập liệu sau khi nộp thành công
        userInputField.value = "";
    })
    .catch(error => {
        console.error("Lỗi xử lý Battle Zone:", error);
        triggerCardShake();
        aiFeedbackDiv.innerHTML = "<span style='color: var(--neon-pink);'>ERROR: SERVER_TIMED_OUT HOẶC API KEY SẬP!</span>";
    });
}

/**
 * 4. Kích hoạt logic Điểm danh thời gian thực (STREAK SYSTEM)
 * Hàm này có thể gán vào nút bấm điểm danh hằng ngày nếu bạn bổ sung trên UI
 */
function triggerCheckin() {
    fetch('/api/game/checkin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: CURRENT_USER_ID })
    })
    .then(response => {
        if (!response.ok) throw new Error("Điểm danh thất bại.");
        return response.json();
    })
    .then(data => {
        // Cập nhật số ngày Streak rực cháy trên màn hình CRT
        const streakElement = document.querySelector(".pulse-neon");
        if (streakElement && data.current_streak) {
            streakElement.textContent = data.current_streak;
        }

        // Hệ thống báo từ vựng mới mở khóa -> Nạp lại bảng VOCAB_QUESTS lập tức
        loadVocabQuests();
    })
    .catch(error => {
        console.error("Lỗi điểm danh:", error);
    });
}

/**
 * Kỹ thuật hiệu ứng thị giác: Rung lắc thẻ Bento khi gặp lỗi hoặc bị AI chê bài làm
 */
function triggerCardShake() {
    const battleCard = document.querySelector(".bento-card.card-large"); // Card chứa Battle Zone
    if (battleCard) {
        battleCard.classList.add("error-shake");
        // Gỡ class sau khi kết thúc chuyển động animation (300ms) để có thể kích hoạt lại lần sau
        setTimeout(() => {
            battleCard.classList.remove("error-shake");
        }, 300);
    }
}