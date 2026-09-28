/**
 * ==============================================================================
 * GLOBAL FLUENT - TAP SPEECH ENGINE (Web Speech API Native Module)
 * Hỗ trợ 100% Native Trình duyệt, Zero chi phí Server, Hoạt động cả Offline:
 * 1. Text-to-Speech (TTS): Phát âm chuẩn bản xứ US/UK cho từ vựng & câu văn.
 * 2. Speech-to-Text (STT): Luyện nói / Shadowing và chấm điểm độ khớp ngữ âm.
 * ==============================================================================
 */

window.TAPSpeech = (function () {
    'use strict';

    let currentUtterance = null;
    let activeRecognition = null;
    let preferredVoice = null;

    // Tự động tìm kiếm Voice tự nhiên khi danh sách giọng của trình duyệt sẵn sàng
    function loadVoices() {
        if (!('speechSynthesis' in window)) return;
        const voices = window.speechSynthesis.getVoices();
        if (!voices || voices.length === 0) return;

        // Ưu tiên các giọng tiếng Anh chuẩn chất lượng cao
        preferredVoice = voices.find(v => (v.lang === 'en-US' || v.lang.startsWith('en')) && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('David')))
            || voices.find(v => v.lang === 'en-US')
            || voices.find(v => v.lang.startsWith('en'))
            || voices[0];
    }

    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
        loadVoices();
    }

    /**
     * Dọn dẹp văn bản trước khi phát âm (loại bỏ ký hiệu chỗ trống, dấu ngoặc kỹ thuật)
     */
    function sanitizeForSpeech(text) {
        if (!text) return '';
        return text
            .replace(/\[\s*_{3,}\s*\]/g, 'blank')
            .replace(/_{3,}/g, 'blank')
            .replace(/->/g, 'changes to')
            .replace(/[\(\)\[\]\{\}]/g, ' ')
            .trim();
    }

    /**
     * PHÁT ÂM VĂN BẢN (Text-to-Speech)
     * @param {string} text - Nội dung tiếng Anh cần đọc
     * @param {Object} options - { rate: 0.9, pitch: 1.0, element: btnElement, onEnd: callback }
     */
    function speak(text, options = {}) {
        if (!('speechSynthesis' in window)) {
            console.warn('[TAPSpeech] Trình duyệt không hỗ trợ Web Speech Synthesis.');
            alert('Trình duyệt của bạn chưa hỗ trợ tính năng phát âm Web Speech API.');
            return;
        }

        const cleanText = sanitizeForSpeech(text);
        if (!cleanText) return;

        // Dừng âm thanh đang phát trước đó để tránh nói đè
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = options.lang || 'en-US';
        utterance.rate = options.rate !== undefined ? options.rate : 0.92; // Tốc độ vừa phải cho người học
        utterance.pitch = options.pitch || 1.0;

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        // Hiệu ứng Visual Pulse trên nút bấm
        const el = options.element;
        if (el) {
            el.classList.add('is-speaking');
        }

        utterance.onstart = function () {
            if (options.onStart) options.onStart();
        };

        utterance.onend = function () {
            if (el) el.classList.remove('is-speaking');
            if (options.onEnd) options.onEnd();
        };

        utterance.onerror = function (e) {
            if (el) el.classList.remove('is-speaking');
            if (options.onError) options.onError(e);
        };

        currentUtterance = utterance;
        window.speechSynthesis.speak(utterance);
    }

    /**
     * DỪNG PHÁT ÂM NGAY LẬP TỨC
     */
    function stopSpeaking() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        document.querySelectorAll('.is-speaking').forEach(el => el.classList.remove('is-speaking'));
    }

    /**
     * KHỞI ĐỘNG THU ÂM & NHẬN DIỆN GIỌNG NÓI (Speech-to-Text / Shadowing)
     * @param {Object} callbacks - { onStart, onResult, onError, onEnd }
     */
    function startListening(callbacks = {}) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Trình duyệt của bạn chưa hỗ trợ Web Speech Recognition (Khuyên dùng Chrome/Edge).');
            if (callbacks.onError) callbacks.onError({ error: 'not_supported' });
            return null;
        }

        // Dừng phiên đang chạy nếu có
        if (activeRecognition) {
            try { activeRecognition.stop(); } catch (e) {}
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = function () {
            if (callbacks.onStart) callbacks.onStart();
        };

        recognition.onresult = function (event) {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }
            const isFinal = event.results[event.results.length - 1].isFinal;
            if (callbacks.onResult) {
                callbacks.onResult(transcript.trim(), isFinal);
            }
        };

        recognition.onerror = function (event) {
            console.warn('[TAPSpeech] Speech Recognition error:', event.error);
            if (callbacks.onError) callbacks.onError(event);
        };

        recognition.onend = function () {
            activeRecognition = null;
            if (callbacks.onEnd) callbacks.onEnd();
        };

        activeRecognition = recognition;
        try {
            recognition.start();
        } catch (e) {
            console.error('[TAPSpeech] Không thể khởi động thu âm:', e);
            if (callbacks.onError) callbacks.onError(e);
        }
        return recognition;
    }

    /**
     * DỪNG THU ÂM
     */
    function stopListening() {
        if (activeRecognition) {
            try {
                activeRecognition.stop();
            } catch (e) {}
            activeRecognition = null;
        }
    }

    /**
     * ĐO ĐỘ KHỚP PHÁT ÂM (Pronunciation Match Calculator)
     * So sánh xâu ký tự giữa câu chuẩn và giọng đọc người dùng.
     */
    function evaluatePronunciation(targetText, spokenText) {
        if (!targetText || !spokenText) {
            return { score: 0, tier: 'retry', label: 'Chưa phát hiện giọng nói', badgeColor: '#ef4444' };
        }

        const cleanTarget = targetText.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().split(/\s+/);
        const cleanSpoken = spokenText.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().split(/\s+/);

        if (cleanTarget.length === 0 || cleanSpoken.length === 0) {
            return { score: 0, tier: 'retry', label: 'Cần thử lại', badgeColor: '#ef4444' };
        }

        // 1. Đếm số từ đúng vị trí hoặc xuất hiện trong target
        let matchedWords = 0;
        const targetSet = new Set(cleanTarget);
        cleanSpoken.forEach(w => {
            if (targetSet.has(w)) matchedWords++;
        });

        // 2. Tính tỷ lệ khớp từ
        const wordAccuracy = Math.min(1.0, matchedWords / cleanTarget.length);

        // 3. Tính độ tương đồng xâu ký tự (Levenshtein ratio đơn giản hóa)
        const s1 = cleanTarget.join(' ');
        const s2 = cleanSpoken.join(' ');
        const charSimilarity = calculateStringSimilarity(s1, s2);

        // Điểm số tổng hợp thang 100
        const finalScore = Math.round((wordAccuracy * 0.6 + charSimilarity * 0.4) * 100);

        if (finalScore >= 88) {
            return { score: finalScore, tier: 'excellent', label: 'Phát Âm Tuyệt Vời (Chuẩn Bản Xứ)', badgeColor: '#22c55e' };
        } else if (finalScore >= 70) {
            return { score: finalScore, tier: 'good', label: 'Rất Tốt (Rõ Ràng & Chuẩn)', badgeColor: '#06b6d4' };
        } else if (finalScore >= 50) {
            return { score: finalScore, tier: 'average', label: 'Khá Ổn (Cần Chỉnh Một Số Âm)', badgeColor: '#f59e0b' };
        } else {
            return { score: Math.max(15, finalScore), tier: 'retry', label: 'Cần Luyện Thêm (Thử Lại Nhé)', badgeColor: '#ec4899' };
        }
    }

    function calculateStringSimilarity(s1, s2) {
        if (s1 === s2) return 1.0;
        const longer = s1.length > s2.length ? s1 : s2;
        const shorter = s1.length > s2.length ? s2 : s1;
        if (longer.length === 0) return 1.0;

        let costs = [];
        for (let i = 0; i <= longer.length; i++) {
            let lastValue = i;
            for (let j = 0; j <= shorter.length; j++) {
                if (i === 0) costs[j] = j;
                else {
                    if (j > 0) {
                        let newValue = costs[j - 1];
                        if (longer.charAt(i - 1) !== shorter.charAt(j - 1)) {
                            newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                        }
                        costs[j - 1] = lastValue;
                        lastValue = newValue;
                    }
                }
            }
            if (i > 0) costs[shorter.length] = lastValue;
        }
        return (longer.length - costs[shorter.length]) / longer.length;
    }

    /**
     * Tự động gán sự kiện cho các nút phát âm `data-speech-text`, `data-speak`, `.tap-audio-btn`
     */
    function autoBindTTS() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('[data-speech-text], [data-speak], .tap-audio-btn');
            if (btn && !btn.classList.contains('btn-speak-audio')) {
                e.preventDefault();
                e.stopPropagation();
                const text = btn.getAttribute('data-speech-text') || btn.getAttribute('data-speak') || btn.innerText.replace(/🔊|Nghe|Ví Dụ/g, '').trim();
                const rate = parseFloat(btn.getAttribute('data-speech-rate') || '0.92');
                speak(text, { element: btn, rate: rate });
            }
        });
    }

    // Tự động kích hoạt khi load DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoBindTTS);
    } else {
        autoBindTTS();
    }

    return {
        speak: speak,
        stopSpeaking: stopSpeaking,
        startListening: startListening,
        stopListening: stopListening,
        evaluatePronunciation: evaluatePronunciation,
        isSupported: () => ('speechSynthesis' in window),
        isSTTSupported: () => !!(window.SpeechRecognition || window.webkitSpeechRecognition)
    };
})();
