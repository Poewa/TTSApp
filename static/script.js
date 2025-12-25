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
    const langButtons = document.querySelectorAll('.lang-btn');

    let currentFilename = null;
    let currentLang = 'da';

    // Translations
    const translations = {
        da: {
            title: '🎙️ Tekst-til-tale Generator',
            subtitle: 'Drevet af Azure OpenAI',
            inputLabel: 'Indtast din tekst:',
            inputPlaceholder: 'Skriv eller indsæt din tekst her...',
            serviceLabel: 'Vælg tjeneste:',
            voiceLabel: 'Vælg stemme:',
            speedLabel: 'Hastighed:',
            generateBtn: 'Generer tale',
            loading: 'Genererer lyd...',
            resultTitle: 'Genereret lyd',
            downloadBtn: '📥 Download lyd',
            loggedInAs: 'Logget ind som:',
            logoutBtn: 'Log ud',
            errorNoText: 'Indtast venligst noget tekst for at konvertere til tale.',
            errorNoConfig: 'Azure OpenAI er ikke konfigureret. Indstil venligst AZURE_OPENAI_API_KEY og AZURE_OPENAI_ENDPOINT i din .env fil for at aktivere tekst-til-tale funktionalitet.'
        },
        en: {
            title: '🎙️ Text-to-Speech Generator',
            subtitle: 'Powered by Azure OpenAI',
            inputLabel: 'Enter your text:',
            inputPlaceholder: 'Type or paste your text here...',
            serviceLabel: 'Select Service:',
            voiceLabel: 'Select Voice:',
            speedLabel: 'Speed:',
            generateBtn: 'Generate Speech',
            loading: 'Generating audio...',
            resultTitle: 'Generated Audio',
            downloadBtn: '📥 Download Audio',
            loggedInAs: 'Logged in as:',
            logoutBtn: 'Logout',
            errorNoText: 'Please enter some text to convert to speech.',
            errorNoConfig: 'Azure OpenAI is not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file to enable text-to-speech functionality.'
        }
    };

    // Speed slider update
    speedSlider.addEventListener('input', function () {
        speedValue.textContent = parseFloat(speedSlider.value).toFixed(1) + 'x';
    });

    // Language switcher
    function setLanguage(lang) {
        currentLang = lang;
        document.documentElement.lang = lang;

        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (key === 'loggedInAs') {
                // Special handling for "logged in as" to preserve username
                const username = element.querySelector('strong');
                if (username) {
                    const usernameText = username.textContent;
                    element.innerHTML = `${translations[lang][key]} <strong>${usernameText}</strong>`;
                }
            } else {
                element.textContent = translations[lang][key];
            }
        });

        // Update placeholder
        const placeholderKey = textInput.getAttribute('data-i18n-placeholder');
        if (placeholderKey) {
            textInput.placeholder = translations[lang][placeholderKey];
        }

        // Update active language button
        langButtons.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
        });
    }

    // Language button click handlers
    langButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setLanguage(btn.getAttribute('data-lang'));
        });
    });

    // Initialize with Danish
    setLanguage('da');

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
