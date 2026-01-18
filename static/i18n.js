let translations = {};
let currentLang = 'da';

async function loadTranslations() {
    try {
        const response = await fetch('/static/translations.json');
        translations = await response.json();
    } catch (error) {
        console.error('Failed to load translations:', error);
    }
}

function setLanguage(lang) {
    currentLang = lang;
    document.documentElement.lang = lang;
    const langButtons = document.querySelectorAll('.lang-btn');

    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (key === 'loggedInAs') {
            const username = element.querySelector('strong');
            if (username) {
                const usernameText = username.textContent;
                element.innerHTML = `${translations[lang][key]} <strong>${usernameText}</strong>`;
            }
        } else if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        if (translations[lang] && translations[lang][key]) {
            element.placeholder = translations[lang][key];
        }
    });

    langButtons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadTranslations();
    const langButtons = document.querySelectorAll('.lang-btn');
    
    langButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setLanguage(btn.getAttribute('data-lang'));
        });
    });

    // Set initial language
    setLanguage(currentLang);
});
