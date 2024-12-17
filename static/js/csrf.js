
// CSRF Token handling
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// Add CSRF token to all AJAX requests
document.addEventListener('DOMContentLoaded', function() {
    const token = getCSRFToken();
    if (token) {
        // Add token to fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            options.headers['X-CSRFToken'] = token;
            return originalFetch(url, options);
        };

        // Add token to XMLHttpRequest
        const originalXHR = window.XMLHttpRequest;
        function newXHR() {
            const xhr = new originalXHR();
            const send = xhr.send;
            xhr.send = function() {
                this.setRequestHeader('X-CSRFToken', token);
                return send.apply(this, arguments);
            };
            return xhr;
        }
        window.XMLHttpRequest = newXHR;
    }
});
