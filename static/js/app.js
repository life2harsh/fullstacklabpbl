(() => {
    const nativeFetch = window.fetch.bind(window);
    const csrfToken = () => decodeURIComponent((document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || '');

    window.fetch = (input, init = {}) => {
        const options = { credentials: 'same-origin', ...init };
        const url = new URL(typeof input === 'string' ? input : input.url, location.href);
        if ((options.method || 'GET').toUpperCase() !== 'GET' && url.origin === location.origin) {
            options.headers = new Headers(options.headers || {});
            options.headers.set('X-CSRFToken', csrfToken());
        }
        return nativeFetch(input, options);
    };

    function toast(text, kind = 'error') {
        let box = document.querySelector('.toasts');
        if (!box) document.body.append(box = Object.assign(document.createElement('div'), { className: 'toasts' }));
        box.append(Object.assign(document.createElement('div'), { className: `toast ${kind}`, textContent: text }));
    }

    async function toggle(button) {
        const response = await fetch(button.dataset.toggle, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) return toast(data.detail || 'Something went wrong.');
        if ('reload' in button.dataset) return location.reload();
        button.classList.toggle('active', data.active);
        const label = button.querySelector('[data-label]');
        if (label) label.textContent = data.active ? label.dataset.on : label.dataset.off;
        const count = button.querySelector('[data-count]') || document.getElementById(button.dataset.countTarget);
        if (count && 'count' in data) count.textContent = data.count;
    }

    document.addEventListener('click', (event) => {
        const target = event.target;
        const button = target.closest('[data-toggle]');
        if (button) {
            event.preventDefault();
            return toggle(button);
        }
        const opener = target.closest('[data-open]');
        if (opener) return document.getElementById(opener.dataset.open).classList.add('active');
        const closer = target.closest('[data-close]');
        if (closer) return closer.closest('.modal').classList.remove('active');
        const card = target.closest('[data-href]');
        if (card && !target.closest('a, button, form, input, label, summary, details')) location.href = card.dataset.href;
    });

    document.addEventListener('submit', (event) => {
        const message = event.target.dataset.confirm;
        if (message && !confirm(message)) event.preventDefault();
    });

    document.addEventListener('DOMContentLoaded', () => {
        const search = document.querySelector('[data-live-search]');
        if (search) {
            let timer;
            search.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(async () => {
                    const url = new URL(location.href);
                    url.searchParams.set('q', search.value.trim());
                    url.searchParams.delete('page');
                    const response = await fetch(url, { headers: { 'X-Requested-With': 'fetch' } });
                    if (response.ok) document.getElementById(search.dataset.liveSearch).innerHTML = await response.text();
                    history.replaceState(null, '', url);
                }, 250);
            });
        }

        setTimeout(() => document.querySelectorAll('.toast').forEach(el => el.remove()), 5000);

        if (!document.querySelector('[data-badge]')) return;
        setInterval(async () => {
            const response = await fetch('/badges').catch(() => null);
            if (!response || !response.ok) return;
            for (const [name, value] of Object.entries(await response.json())) {
                const badge = document.querySelector(`[data-badge="${name}"]`);
                if (badge) Object.assign(badge, { textContent: value > 99 ? '99+' : value, hidden: !value });
            }
        }, 15000);
    });
})();
