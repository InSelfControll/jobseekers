
// CSRF Token handling
function getCSRFToken() {
    // Try to get token from meta tag first
    let token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // If not found in meta, try to get from DNS records component
    if (!token) {
        token = document.querySelector('.dns-records')?.getAttribute('data-csrf-token');
    }
    
    return token || '';
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
            if (options.method && ['POST', 'PUT', 'PATCH','DELETE'].includes(options.method.toUpperCase())) {
		    options.headers['X-CSRFToken'] = token;
	    }
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
