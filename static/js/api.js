/* Same-origin fetch helper: Django sessions stay secure while existing AJAX UX remains intact. */
(function () {
    const originalFetch = window.fetch.bind(window);
    function csrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }
    window.fetch = function (input, init) {
        const options = init ? { ...init } : {};
        const method = (options.method || 'GET').toUpperCase();
        const url = typeof input === 'string' ? input : input.url;
        if (method !== 'GET' && (!url.startsWith('http') || url.startsWith(window.location.origin))) {
            options.headers = new Headers(options.headers || {});
            const token = csrfToken();
            if (token) options.headers.set('X-CSRFToken', token);
        }
        options.credentials = options.credentials || 'same-origin';
        return originalFetch(input, options);
    };
})();
