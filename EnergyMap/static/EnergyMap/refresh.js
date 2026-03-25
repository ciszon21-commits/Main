(function () {
    const DEFAULT_COOLDOWN_MS = 60000;
    const DEFAULT_STORAGE_KEY = 'energymap-refresh-cooldown-until';
    const DEFAULT_FORCE_REFRESH_KEY = 'energymap-force-refresh';
    const DEFAULT_LABEL = '\u91cd\u65b0\u6574\u7406';
    const DEFAULT_LOADING_LABEL = '\u91cd\u65b0\u6574\u7406\u4e2d...';

    function consumeForceRefresh(storageKey = DEFAULT_FORCE_REFRESH_KEY) {
        const value = sessionStorage.getItem(storageKey);
        if (!value) {
            return false;
        }

        sessionStorage.removeItem(storageKey);
        return value === '1';
    }

    function initRefreshCooldown(options = {}) {
        const cooldownMs = Number(options.cooldownMs || DEFAULT_COOLDOWN_MS);
        const storageKey = options.storageKey || DEFAULT_STORAGE_KEY;
        const forceRefreshKey = options.forceRefreshKey || DEFAULT_FORCE_REFRESH_KEY;
        const baseLabel = options.baseLabel || DEFAULT_LABEL;
        const loadingLabel = options.loadingLabel || DEFAULT_LOADING_LABEL;
        const button = document.getElementById(options.buttonId || 'refreshPageBtn');
        const label = document.getElementById(options.labelId || 'refreshPageBtnLabel');
        const ring = document.getElementById(options.ringId || 'refreshCooldownRing');

        if (!button || !label || !ring) {
            return;
        }

        let timer = null;

        function render(remainingMs) {
            const clamped = Math.max(0, remainingMs);
            const progress = clamped > 0 ? clamped / cooldownMs : 1;
            ring.style.setProperty('--progress', `${progress}turn`);

            if (clamped > 0) {
                button.disabled = true;
                label.textContent = `${baseLabel} ${Math.ceil(clamped / 1000)}s`;
                return;
            }

            button.disabled = false;
            label.textContent = baseLabel;
        }

        function start() {
            const cooldownUntil = Number(sessionStorage.getItem(storageKey) || 0);

            if (timer) {
                clearInterval(timer);
                timer = null;
            }

            const tick = () => {
                const remaining = cooldownUntil - Date.now();
                render(remaining);

                if (remaining <= 0) {
                    sessionStorage.removeItem(storageKey);
                    clearInterval(timer);
                    timer = null;
                }
            };

            tick();
            if (cooldownUntil > Date.now()) {
                timer = setInterval(tick, 200);
            }
        }

        button.addEventListener('click', () => {
            const cooldownUntil = Date.now() + cooldownMs;
            sessionStorage.setItem(storageKey, String(cooldownUntil));
            sessionStorage.setItem(forceRefreshKey, '1');
            render(cooldownMs);
            label.textContent = loadingLabel;
            window.location.reload();
        });

        start();
    }

    window.initRefreshCooldown = initRefreshCooldown;
    window.consumeEnergyMapForceRefresh = consumeForceRefresh;
})();
