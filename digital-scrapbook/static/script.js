// Language Toggle Handler (Korean / English)
document.addEventListener('DOMContentLoaded', () => {
    const langBtn = document.getElementById('lang-toggle');

    // Remember the choice in a cookie too, since localStorage can be blocked or cleared
    function loadLanguage() {
        const match = document.cookie.match(/(?:^|; )app_lang=(kr|en)/);
        if (match) return match[1];
        try {
            return localStorage.getItem('app_lang') || 'kr';
        } catch (e) {
            return 'kr';
        }
    }

    function saveLanguage(lang) {
        document.cookie = `app_lang=${lang}; path=/; max-age=31536000; SameSite=Lax`;
        try {
            localStorage.setItem('app_lang', lang);
        } catch (e) {}
    }

    let currentLang = loadLanguage();

    function applyLanguage(lang) {
        document.querySelectorAll('[data-kr][data-en]').forEach(el => {
            el.textContent = el.getAttribute(`data-${lang}`);
        });
        document.documentElement.lang = lang === 'kr' ? 'ko' : 'en';
        saveLanguage(lang);
    }

    if (langBtn) {
        langBtn.addEventListener('click', () => {
            currentLang = currentLang === 'kr' ? 'en' : 'kr';
            applyLanguage(currentLang);
        });
    }

    applyLanguage(currentLang);
});

// Global Modal Utilities
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function closeModalOnOuter(modalId, event) {
    if (event.target.id === modalId) {
        closeModal(modalId);
    }
}