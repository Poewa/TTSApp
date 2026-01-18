document.addEventListener('DOMContentLoaded', function () {
    const textInput = document.getElementById('text-input');
    const serviceSelect = document.getElementById('service-select');
    const voiceSelect = document.getElementById('voice-select');
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');
    const generateBtn = document.getElementById('generate-btn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('result-section');
    const audioPlayer = document.getElementById('audio-player');
    const downloadBtn = document.getElementById('download-btn');
    const errorMessage = document.getElementById('error-message');

    let currentFilename = null;

    // Speed slider update
    speedSlider.addEventListener('input', function () {
        speedValue.textContent = parseFloat(speedSlider.value).toFixed(1) + 'x';
    });

    // Load voices when service changes
    async function loadVoices(service) {
        try {
            const response = await fetch(`/get-voices?service=${service}`);
            const data = await response.json();

            if (response.ok && data.voices) {
                voiceSelect.innerHTML = '';
                data.voices.forEach((voice, index) => {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = voice.displayName;
                    if (index === 0) {
                        option.selected = true;
                    }
                    voiceSelect.appendChild(option);
                });
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

    generateBtn.addEventListener('click', async function () {
        const text = textInput.value.trim();

        if (!text) {
            showError(translations[currentLang].errorNoText);
            return;
        }

        // Hide previous results and errors
        hideError();
        resultSection.style.display = 'none';

        // Show loading
        loading.style.display = 'block';
        generateBtn.disabled = true;

        try {
            const response = await fetch('/generate-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    voice: voiceSelect.value,
                    service: serviceSelect.value,
                    speed: parseFloat(speedSlider.value)
                })
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

    // Allow Enter key in textarea with Shift, but generate on Ctrl+Enter
    textInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            generateBtn.click();
        }
    });
});
