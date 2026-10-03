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
     * @param {Object} callbacks - { onStart, onResult, onError, onEnd, continuous, lang }
     */
    function startListening(callbacks = {}) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            const errMsg = 'Trình duyệt chưa hỗ trợ Web Speech Recognition (Khuyên dùng Chrome/Edge).';
            if (callbacks.onError) callbacks.onError({ error: 'not_supported' }, errMsg);
            return null;
        }

        // Dừng phiên đang chạy nếu có
        if (activeRecognition) {
            try { activeRecognition.abort(); } catch (e) {}
            activeRecognition = null;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = callbacks.lang || 'en-US';
        // Mặc định bật continuous để tránh Chrome tự ngắt tức thì sau 1s im lặng
        recognition.continuous = callbacks.continuous !== undefined ? callbacks.continuous : true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        let accumulatedFinal = '';
        let lastInterim = '';

        recognition.onstart = function () {
            if (callbacks.onStart) callbacks.onStart();
        };

        recognition.onresult = function (event) {
            let currentInterim = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    accumulatedFinal += event.results[i][0].transcript + ' ';
                } else {
                    currentInterim += event.results[i][0].transcript;
                }
            }
            lastInterim = currentInterim;
            const fullTranscript = (accumulatedFinal + currentInterim).trim();
            const isFinal = event.results[event.results.length - 1].isFinal;

            if (callbacks.onResult) {
                callbacks.onResult(fullTranscript, isFinal, {
                    finalText: accumulatedFinal.trim(),
                    interimText: currentInterim.trim(),
                    rawTranscript: fullTranscript
                });
            }
        };

        recognition.onerror = function (event) {
            console.warn('[TAPSpeech] Speech Recognition error:', event.error);
            let friendlyMsg = 'Lỗi thu âm: ' + event.error;
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
                friendlyMsg = 'Quyền sử dụng Micro bị chặn. Vui lòng bấm vào biểu tượng Micro/Khóa trên thanh URL để Cho phép (Allow)!';
            } else if (event.error === 'no-speech') {
                friendlyMsg = 'Chưa phát hiện giọng nói. Hãy nói to, rõ ràng và gần Micro hơn!';
            } else if (event.error === 'network') {
                friendlyMsg = 'Lỗi kết nối máy chủ giọng nói Google Web Speech. Vui lòng kiểm tra mạng hoặc dùng ô nhập đối soát bên dưới!';
            } else if (event.error === 'audio-capture') {
                friendlyMsg = 'Không tìm thấy thiết bị Microphone khả dụng trên máy tính của bạn.';
            }
            if (callbacks.onError) callbacks.onError(event, friendlyMsg);
        };

        recognition.onend = function () {
            const finalSpoken = (accumulatedFinal + lastInterim).trim();
            activeRecognition = null;
            if (callbacks.onEnd) callbacks.onEnd(finalSpoken);
        };

        activeRecognition = recognition;
        try {
            recognition.start();
        } catch (e) {
            console.error('[TAPSpeech] Không thể khởi động thu âm:', e);
            if (callbacks.onError) callbacks.onError(e, 'Không thể khởi động thu âm: ' + e.message);
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
     * ĐO ĐỘ KHỚP PHÁT ÂM & ĐỐI SOÁT TỪNG TỪ (Mirror Pronunciation Evaluator)
     * So sánh xâu ký tự và đối soát từng từ giữa mục tiêu và giọng đọc của người dùng.
     */
    function evaluatePronunciation(targetText, spokenText) {
        if (!targetText || !spokenText) {
            return {
                score: 0,
                tier: 'retry',
                label: 'Chưa phát hiện giọng nói',
                badgeColor: '#ef4444',
                targetWords: [],
                spokenWords: [],
                advice: 'Hãy bấm lại micro và đọc to rõ ràng từ mục tiêu.'
            };
        }

        const rawTargetTokens = targetText.trim().split(/\s+/);
        const rawSpokenTokens = spokenText.trim().split(/\s+/);

        const cleanTarget = targetText.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().split(/\s+/);
        const cleanSpoken = spokenText.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().split(/\s+/);

        if (cleanTarget.length === 0 || cleanSpoken.length === 0) {
            return {
                score: 0,
                tier: 'retry',
                label: 'Cần thử lại',
                badgeColor: '#ef4444',
                targetWords: [],
                spokenWords: [],
                advice: 'Âm thanh chưa rõ chữ. Hãy nói lại từ tốn hơn nhé!'
            };
        }

        // Đối soát từng từ chuẩn mục tiêu với các từ người dùng phát âm
        const targetWords = cleanTarget.map((w, idx) => {
            const rawWord = rawTargetTokens[idx] || w;
            const isExactMatch = cleanSpoken.includes(w);
            let isCloseMatch = false;
            if (!isExactMatch) {
                isCloseMatch = cleanSpoken.some(sp => calculateStringSimilarity(w, sp) >= 0.7);
            }
            return {
                word: rawWord,
                clean: w,
                matched: isExactMatch,
                close: isCloseMatch
            };
        });

        // Đối soát các từ giọng đọc của người dùng
        const spokenWords = cleanSpoken.map((w, idx) => {
            const rawWord = rawSpokenTokens[idx] || w;
            const isExactMatch = cleanTarget.includes(w);
            let isCloseMatch = false;
            if (!isExactMatch) {
                isCloseMatch = cleanTarget.some(tgt => calculateStringSimilarity(tgt, w) >= 0.7);
            }
            return {
                word: rawWord,
                clean: w,
                matched: isExactMatch,
                close: isCloseMatch
            };
        });

        // Đếm số từ đúng
        let matchedCount = targetWords.filter(t => t.matched).length;
        let closeCount = targetWords.filter(t => !t.matched && t.close).length;
        const wordAccuracy = Math.min(1.0, (matchedCount + closeCount * 0.7) / targetWords.length);

        // Tính độ tương đồng xâu ký tự toàn diện
        const s1 = cleanTarget.join(' ');
        const s2 = cleanSpoken.join(' ');
        const charSimilarity = calculateStringSimilarity(s1, s2);

        // Điểm số tổng hợp thang 100
        const finalScore = Math.round((wordAccuracy * 0.6 + charSimilarity * 0.4) * 100);

        let tier = 'retry';
        let label = 'Cần Luyện Thêm (Thử Lại Nhé)';
        let badgeColor = '#ec4899';
        let advice = 'Chú ý lắng nghe lại phát âm mẫu để bắt chước chuẩn trọng âm và âm đuôi.';

        if (finalScore >= 88) {
            tier = 'excellent';
            label = 'Phát Âm Tuyệt Vời (Chuẩn Bản Xứ)';
            badgeColor = '#22c55e';
            advice = 'Ngữ âm cực kỳ chuẩn xác, rõ chữ và tròn vành rõ tiếng! Tiếp tục phát huy nhé.';
        } else if (finalScore >= 70) {
            tier = 'good';
            label = 'Rất Tốt (Rõ Ràng & Dễ Hiểu)';
            badgeColor = '#06b6d4';
            advice = 'Giọng đọc tự nhiên, người bản ngữ hiểu hoàn toàn. Có thể nhấn rõ thêm các phụ âm cuối.';
        } else if (finalScore >= 50) {
            tier = 'average';
            label = 'Khá Ổn (Cần Chỉnh Vài Âm)';
            badgeColor = '#f59e0b';
            advice = 'Một vài âm tiết bị nuốt hoặc nhầm lẫn. Hãy nghe lại âm mẫu ở tốc độ 0.8x.';
        } else {
            advice = 'Phát âm đang lệch khá nhiều so với từ chuẩn. Hãy bấm "🔊 NGHE ĐỌC MẪU" rồi đọc lại từng âm!';
        }

        return {
            score: Math.max(10, finalScore),
            tier: tier,
            label: label,
            badgeColor: badgeColor,
            targetWords: targetWords,
            spokenWords: spokenWords,
            advice: advice,
            cleanTarget: s1,
            cleanSpoken: s2
        };
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
     * ==============================================================================
     * NATIVE WAV AUDIO RECORDER
     * Thu âm trực tiếp bằng Web Audio API (PCM 16kHz Mono 16-bit WAV)
     * Hoạt động 100% trên Brave Browser, Chrome, Firefox, Edge, Safari.
     * Hoàn toàn không phụ thuộc vào máy chủ ngoài hay Google Web Speech API.
     * ==============================================================================
     */
    class SimpleWavRecorder {
        constructor() {
            this.audioCtx = null;
            this.mediaStream = null;
            this.inputSource = null;
            this.processor = null;
            this.analyser = null;
            this.recordedSamples = [];
            this.sampleRate = 16000;
            this.isRecording = false;
            this.animFrame = null;
        }

        async start(options = {}) {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error("Trình duyệt không hỗ trợ getUserMedia.");
            }

            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContextClass();
            const inputSampleRate = this.audioCtx.sampleRate;

            this.inputSource = this.audioCtx.createMediaStreamSource(this.mediaStream);

            this.analyser = this.audioCtx.createAnalyser();
            this.analyser.fftSize = 256;
            this.inputSource.connect(this.analyser);

            const bufferSize = 4096;
            this.processor = this.audioCtx.createScriptProcessor(bufferSize, 1, 1);
            this.recordedSamples = [];
            this.isRecording = true;

            this.processor.onaudioprocess = (e) => {
                if (!this.isRecording) return;
                const inputData = e.inputBuffer.getChannelData(0);
                const downsampled = this.downsampleBuffer(inputData, inputSampleRate, this.sampleRate);
                this.recordedSamples.push(new Float32Array(downsampled));
            };

            this.inputSource.connect(this.processor);
            this.processor.connect(this.audioCtx.destination);

            if (options.onVolume) {
                const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
                const checkVolume = () => {
                    if (!this.isRecording) return;
                    this.analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        sum += dataArray[i];
                    }
                    const avg = sum / dataArray.length;
                    options.onVolume(avg);
                    this.animFrame = requestAnimationFrame(checkVolume);
                };
                this.animFrame = requestAnimationFrame(checkVolume);
            }
        }

        downsampleBuffer(buffer, sourceRate, targetRate) {
            if (sourceRate === targetRate) return buffer;
            const ratio = sourceRate / targetRate;
            const newLength = Math.round(buffer.length / ratio);
            const result = new Float32Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;
            while (offsetResult < newLength) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0;
                let count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                    accum += buffer[i];
                    count++;
                }
                result[offsetResult] = count > 0 ? accum / count : 0;
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        stop() {
            this.isRecording = false;
            if (this.animFrame) cancelAnimationFrame(this.animFrame);
            if (this.processor) {
                try { this.processor.disconnect(); } catch (e) {}
                this.processor = null;
            }
            if (this.inputSource) {
                try { this.inputSource.disconnect(); } catch (e) {}
                this.inputSource = null;
            }
            if (this.analyser) {
                try { this.analyser.disconnect(); } catch (e) {}
                this.analyser = null;
            }
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(t => t.stop());
                this.mediaStream = null;
            }
            if (this.audioCtx && this.audioCtx.state !== 'closed') {
                try { this.audioCtx.close(); } catch (e) {}
                this.audioCtx = null;
            }

            let totalLength = 0;
            for (let i = 0; i < this.recordedSamples.length; i++) {
                totalLength += this.recordedSamples[i].length;
            }
            const merged = new Float32Array(totalLength);
            let offset = 0;
            for (let i = 0; i < this.recordedSamples.length; i++) {
                merged.set(this.recordedSamples[i], offset);
                offset += this.recordedSamples[i].length;
            }

            return this.encodeWAV(merged, this.sampleRate);
        }

        encodeWAV(samples, sampleRate) {
            const buffer = new ArrayBuffer(44 + samples.length * 2);
            const view = new DataView(buffer);

            this.writeString(view, 0, 'RIFF');
            view.setUint32(4, 36 + samples.length * 2, true);
            this.writeString(view, 8, 'WAVE');

            this.writeString(view, 12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true);
            view.setUint16(22, 1, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);

            this.writeString(view, 36, 'data');
            view.setUint32(40, samples.length * 2, true);

            let index = 44;
            for (let i = 0; i < samples.length; i++) {
                const s = Math.max(-1, Math.min(1, samples[i]));
                view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                index += 2;
            }

            return new Blob([view], { type: 'audio/wav' });
        }

        writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }
    }

    let activeWavRecorder = null;

    async function startWavRecording(options = {}) {
        if (activeWavRecorder) {
            try { activeWavRecorder.stop(); } catch (e) {}
            activeWavRecorder = null;
        }
        activeWavRecorder = new SimpleWavRecorder();
        await activeWavRecorder.start(options);
        return activeWavRecorder;
    }

    function stopWavRecording() {
        if (!activeWavRecorder) return null;
        const blob = activeWavRecorder.stop();
        activeWavRecorder = null;
        return blob;
    }

    async function evaluateAudioBlob(blob, targetWord, band = 'A1') {
        const formData = new FormData();
        formData.append('audio', blob, 'speech.wav');
        formData.append('target', targetWord);
        formData.append('band', band);

        const res = await fetch('/api/game/speaking/evaluate_audio', {
            method: 'POST',
            body: formData
        });
        return await res.json();
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
        SimpleWavRecorder: SimpleWavRecorder,
        startWavRecording: startWavRecording,
        stopWavRecording: stopWavRecording,
        evaluateAudioBlob: evaluateAudioBlob,
        isSupported: () => ('speechSynthesis' in window),
        isSTTSupported: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) || !!(window.SpeechRecognition || window.webkitSpeechRecognition),
        isWavSupported: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
    };
})();
