// This opens only a user-entered source URL on a click. Page content stays in
// that browser tab until the user explicitly copies/pastes it into the form.
(() => {
    const button = document.getElementById('open-recipe-page');
    const input = document.getElementById('id_source_url');
    const status = document.getElementById('open-recipe-help');
    if (!button || !input || !status) return;
    button.hidden = false;
    button.addEventListener('click', () => {
        try {
            const url = new URL(input.value);
            if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
                throw new Error('Unsupported URL');
            }
            window.open(url.href, '_blank', 'noopener,noreferrer');
            status.textContent = 'Copy the recipe in the new tab, then return here to paste it.';
        } catch {
            status.textContent = 'Enter the original HTTP or HTTPS recipe page URL first.';
            input.focus();
        }
    });
})();
