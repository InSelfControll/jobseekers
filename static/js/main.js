
function uploadSSLCertificate() {
    const formData = new FormData();
    const certFile = document.getElementById('certFile').files[0];
    const keyFile = document.getElementById('keyFile').files[0];
    
    if (!certFile || !keyFile) {
        alert('Please select both certificate and key files');
        return;
    }
    
    formData.append('cert', certFile);
    formData.append('key', keyFile);
    
    fetch('/admin/upload-ssl', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('SSL certificate uploaded successfully!');
        } else {
            alert('Error: ' + (data.error || 'Failed to upload SSL certificate'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to upload SSL certificate');
    });
}


let isDarkMode = localStorage.getItem('darkMode') === 'true';

function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    localStorage.setItem('darkMode', isDarkMode);
    document.body.classList.toggle('dark-mode', isDarkMode);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.querySelector('[data-feather="moon"]');
    if (icon) {
        icon.setAttribute('data-feather', isDarkMode ? 'sun' : 'moon');
        feather.replace();
    }
}

function encryptSensitiveData(data) {
    // Simple encryption for demonstration - in production use proper encryption
    return btoa(JSON.stringify(data));
}

function saveDomain() {
    const domain = document.getElementById('domain').value;
    
    fetch('/admin/update-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ domain })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Domain saved successfully!');
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function verifyDomain() {
    const domain = document.getElementById('domain').value;
    
    fetch('/admin/verify-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ domain })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Domain verified successfully!');
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function saveSSOSettings() {
    const provider = document.getElementById('provider').value;
    let data = {
        domain: document.getElementById('domain').value,
        provider: provider
    };
    
    if (provider === 'GITHUB') {
        data.client_id = encryptSensitiveData({
            id: document.getElementById('client_id').value
        });
        data.client_secret = encryptSensitiveData({
            secret: document.getElementById('client_secret').value
        });
    } else if (provider === 'SAML') {
        const manifestFile = document.getElementById('saml_manifest').files[0];
        if (manifestFile) {
            const reader = new FileReader();
            reader.onload = function(e) {
                data.saml_manifest = encryptSensitiveData({
                    content: e.target.result
                });
                sendSSOSettings(data);
            };
            reader.readAsText(manifestFile);
            return;
        }
    }
    
    sendSSOSettings(data);
}

function sendSSOSettings(data) {
    fetch('/admin/save-sso-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('SSO settings saved successfully!');
        } else {
            alert('Error: ' + data.error);
        }
    });
}

// Initialize dark mode on page load
document.addEventListener('DOMContentLoaded', () => {
    const prefersDark = localStorage.getItem('darkMode') === 'true';
    document.body.classList.toggle('dark-mode', prefersDark);
    updateThemeIcon();
    feather.replace();
});

function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', isDark);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.querySelector('[data-feather]');
    if (icon) {
        icon.setAttribute('data-feather', document.body.classList.contains('dark-mode') ? 'sun' : 'moon');
        feather.replace();
    }
}

function toggleProviderFields() {
    const provider = document.getElementById('provider').value;
    const githubFields = document.getElementById('github-fields');
    const azureFields = document.getElementById('azure-fields');
    
    if (provider === 'GITHUB') {
        githubFields.style.display = 'block';
        azureFields.style.display = 'none';
    } else if (provider === 'AZURE') {
        githubFields.style.display = 'none';
        azureFields.style.display = 'block';
    } else {
        githubFields.style.display = 'none';
        azureFields.style.display = 'none';
    }
}

// Call toggleProviderFields on page load to set initial state
document.addEventListener('DOMContentLoaded', () => {
    toggleProviderFields();
});
