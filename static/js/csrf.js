
// CSRF Token handling
function getCSRFToken() {
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    return metaToken || '';
}

// Add CSRF token to all AJAX requests
function setupCSRFProtection() {
    let token = getCSRFToken();
    
    if (token) {
        // Add to fetch requests
        let originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            options.headers = {
                ...options.headers,
                'X-CSRFToken': token
            };
            return originalFetch(url, options);
        };

        // Add to XMLHttpRequest
        let originalXHR = window.XMLHttpRequest;
        function newXHR() {
            let xhr = new originalXHR();
            let send = xhr.send;
            xhr.send = function(body) {
                xhr.setRequestHeader('X-CSRFToken', token);
                return send.apply(this, arguments);
            };
            return xhr;
        }
        window.XMLHttpRequest = newXHR;
    }
}

document.addEventListener('DOMContentLoaded', setupCSRFProtection);
