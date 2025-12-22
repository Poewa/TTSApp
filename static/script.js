document.addEventListener('DOMContentLoaded', function () {
    const textInput = document.getElementById('text-input');
    const voiceSelect = document.getElementById('voice-select');
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
            voiceLabel: 'Vælg stemme:',
            generateBtn: 'Generer tale',
            loading: 'Genererer lyd...',
            resultTitle: 'Genereret lyd',
            downloadBtn: '📥 Download lyd',
            errorNoText: 'Indtast venligst noget tekst for at konvertere til tale.',
            errorNoConfig: 'Azure OpenAI er ikke konfigureret. Indstil venligst AZURE_OPENAI_API_KEY og AZURE_OPENAI_ENDPOINT i din .env fil for at aktivere tekst-til-tale funktionalitet.'
        },
        en: {
            title: '🎙️ Text-to-Speech Generator',
            subtitle: 'Powered by Azure OpenAI',
            inputLabel: 'Enter your text:',
            inputPlaceholder: 'Type or paste your text here...',
            voiceLabel: 'Select Voice:',
            generateBtn: 'Generate Speech',
            loading: 'Generating audio...',
            resultTitle: 'Generated Audio',
            downloadBtn: '📥 Download Audio',
            errorNoText: 'Please enter some text to convert to speech.',
            errorNoConfig: 'Azure OpenAI is not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file to enable text-to-speech functionality.'
        }
    };

    // Language switcher
    function setLanguage(lang) {
        currentLang = lang;
        document.documentElement.lang = lang;

        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = translations[lang][key];
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
                    voice: voiceSelect.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                // Check if it's the "not configured" error
                if (response.status === 503 && data.error.includes('not configured')) {
                    throw new Error(translations[currentLang].errorNoConfig);
                }
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
            window.location.href = `/download/${currentFilename}`;
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
