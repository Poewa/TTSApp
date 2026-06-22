document.addEventListener('DOMContentLoaded', function () {
    const textInput = document.getElementById('text-input');
    const textInputDa = document.getElementById('text-input-da');
    const textInputEn = document.getElementById('text-input-en');
    const serviceSelect = document.getElementById('service-select');
    const voiceSelect = document.getElementById('voice-select');
    const voiceSelectDa = document.getElementById('voice-select-da');
    const voiceSelectEn = document.getElementById('voice-select-en');
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');
    const generateBtn = document.getElementById('generate-btn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('result-section');
    const audioPlayer = document.getElementById('audio-player');
    const downloadBtn = document.getElementById('download-btn');
    const errorMessage = document.getElementById('error-message');

    // Mode elements
    const modeButtons = document.querySelectorAll('.mode-btn');
    const singleInput = document.getElementById('single-input');
    const combinedInput = document.getElementById('combined-input');
    const singleVoiceWrap = document.getElementById('single-voice-wrap');
    const combinedVoiceWrap = document.getElementById('combined-voice-wrap');
    const combinedVoiceWrapEn = document.getElementById('combined-voice-wrap-en');

    let currentFilename = null;
    let currentMode = 'single';

    // Speed slider update
    speedSlider.addEventListener('input', function () {
        speedValue.textContent = parseFloat(speedSlider.value).toFixed(1) + 'x';
    });

    // Populate a <select> with voices, optionally filtered by language prefix
    // (e.g. 'da' or 'en'). Falls back to the full list if the filter is empty,
    // so services without language-specific voices (e.g. OpenAI) still work.
    function populateVoiceSelect(selectEl, voices, langPrefix) {
        if (!selectEl) return;
        let list = voices;
        if (langPrefix) {
            const filtered = voices.filter(v => (v.language || '').toLowerCase().startsWith(langPrefix));
            if (filtered.length > 0) list = filtered;
        }
        selectEl.innerHTML = '';
        list.forEach((voice, index) => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = voice.displayName;
            if (index === 0) {
                option.selected = true;
            }
            selectEl.appendChild(option);
        });
    }

    // Load voices for the selected service and populate every voice select
    async function loadVoices(service) {
        try {
            const response = await fetch(`/get-voices?service=${service}`);
            const data = await response.json();

            if (response.ok && data.voices) {
                populateVoiceSelect(voiceSelect, data.voices, null);
                populateVoiceSelect(voiceSelectDa, data.voices, 'da');
                populateVoiceSelect(voiceSelectEn, data.voices, 'en');
            }
        } catch (error) {
            console.error('Error loading voices:', error);
        }
    }

    // Service selector change handler
    serviceSelect.addEventListener('change', function () {
        loadVoices(serviceSelect.value);
    });

    // Load initial voices based on the selected service on page load
    loadVoices(serviceSelect.value);

    // Mode toggle (single vs. combined Danish + English)
    function setMode(mode) {
        currentMode = mode;
        const isCombined = mode === 'combined';
        singleInput.style.display = isCombined ? 'none' : 'block';
        combinedInput.style.display = isCombined ? 'block' : 'none';
        singleVoiceWrap.style.display = isCombined ? 'none' : 'block';
        combinedVoiceWrap.style.display = isCombined ? 'block' : 'none';
        combinedVoiceWrapEn.style.display = isCombined ? 'block' : 'none';
        modeButtons.forEach(btn => btn.classList.toggle('active', btn.getAttribute('data-mode') === mode));
        hideError();
        resultSection.style.display = 'none';
    }

    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => setMode(btn.getAttribute('data-mode')));
    });

    async function generateSingle() {
        const text = textInput.value.trim();
        if (!text) {
            showError(translations[currentLang].errorNoText);
            return;
        }
        await postGenerate('/generate-speech', {
            text: text,
            voice: voiceSelect.value,
            service: serviceSelect.value,
            speed: parseFloat(speedSlider.value)
        });
    }

    async function generateCombined() {
        const textDa = textInputDa.value.trim();
        const textEn = textInputEn.value.trim();
        if (!textDa || !textEn) {
            showError(translations[currentLang].errorNoTextCombined || translations[currentLang].errorNoText);
            return;
        }
        await postGenerate('/generate-combined', {
            text_da: textDa,
            text_en: textEn,
            voice_da: voiceSelectDa.value,
            voice_en: voiceSelectEn.value,
            service: serviceSelect.value,
            speed: parseFloat(speedSlider.value)
        });
    }

    // Shared request/response handling for both modes
    async function postGenerate(url, payload) {
        hideError();
        resultSection.style.display = 'none';
        loading.style.display = 'block';
        generateBtn.disabled = true;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                // Use the actual error message from the server
                throw new Error(data.error || 'Failed to generate speech');
            }

            // Set audio source and show player
            audioPlayer.src = data.audio_url;
            currentFilename = data.filename;

            // Show results
            loading.style.display = 'none';
            resultSection.style.display = 'block';

            // Auto-play the audio
            audioPlayer.play().catch(e => console.log('Auto-play prevented:', e));
        } catch (error) {
            loading.style.display = 'none';
            showError(error.message);
        } finally {
            generateBtn.disabled = false;
        }
    }

    generateBtn.addEventListener('click', function () {
        if (currentMode === 'combined') {
            generateCombined();
        } else {
            generateSingle();
        }
    });

    downloadBtn.addEventListener('click', function () {
        if (currentFilename) {
            const formatSelect = document.getElementById('download-format');
            const fmt = formatSelect ? formatSelect.value : 'mp3';
            // Add format as query parameter
            window.location.href = `/download/${currentFilename}?format=${fmt}`;
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // Generate on Ctrl+Enter from any text area
    [textInput, textInputDa, textInputEn].forEach(function (el) {
        if (!el) return;
        el.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                generateBtn.click();
            }
        });
    });
});
