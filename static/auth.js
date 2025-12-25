document.addEventListener('DOMContentLoaded', function () {
    const langButtons = document.querySelectorAll('.lang-btn');
    let currentLang = 'da';

    // Translations for auth pages
    const translations = {
        da: {
            // Login page
            loginTitle: '🔐 Login',
            usernameLabel: 'Brugernavn:',
            passwordLabel: 'Adgangskode:',
            loginButton: 'Login',
            registerPrompt: 'Har du ikke en konto?',
            registerLink: 'Registrer her',

            // Register page
            registerTitle: '📝 Registrer',
            confirmPasswordLabel: 'Bekræft adgangskode:',
            registerButton: 'Registrer',
            loginPrompt: 'Har du allerede en konto?',
            loginLink: 'Login her'
        },
        en: {
            // Login page
            loginTitle: '🔐 Login',
            usernameLabel: 'Username:',
            passwordLabel: 'Password:',
            loginButton: 'Login',
            registerPrompt: "Don't have an account?",
            registerLink: 'Register here',

            // Register page
            registerTitle: '📝 Register',
            confirmPasswordLabel: 'Confirm Password:',
            registerButton: 'Register',
            loginPrompt: 'Already have an account?',
            loginLink: 'Login here'
        }
    };

    // Language switcher
    function setLanguage(lang) {
        currentLang = lang;
        document.documentElement.lang = lang;

        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (translations[lang][key]) {
                element.textContent = translations[lang][key];
            }
        });

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
});
