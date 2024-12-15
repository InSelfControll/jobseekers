
// CSRF Token handling
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Add CSRF token to all AJAX requests
function setupCSRFProtection() {
    // Add CSRF token to all AJAX requests
    let token = getCSRFToken();
    
    if (token) {
        // Add to fetch requests
        let originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            if (options.method && options.method.toLowerCase() !== 'get') {
                options.headers['X-CSRFToken'] = token;
            }
            return originalFetch(url, options);
        };

        // Add to XMLHttpRequest
        let originalXHR = window.XMLHttpRequest;
        function newXHR() {
            let xhr = new originalXHR();
            let send = xhr.send;
            xhr.send = function(body) {
                if (xhr.method && xhr.method.toLowerCase() !== 'get') {
                    xhr.setRequestHeader('X-CSRFToken', token);
                }
                return send.apply(this, arguments);
            };
            return xhr;
        }
        window.XMLHttpRequest = newXHR;
    }
}

// Initialize CSRF protection when DOM loads
document.addEventListener('DOMContentLoaded', setupCSRFProtection);
