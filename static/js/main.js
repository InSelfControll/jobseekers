
function generateSSLCertificate() {
    const statusDiv = document.getElementById('sslStatus');
    const alertDiv = statusDiv.querySelector('.alert');
    
    statusDiv.style.display = 'block';
    alertDiv.className = 'alert alert-info';
    alertDiv.textContent = 'Generating SSL certificate...';
    
    fetch('/admin/generate-ssl', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = 'SSL certificate generated successfully!';
        } else {
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = 'Error: ' + (data.error || 'Failed to generate SSL certificate');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alertDiv.className = 'alert alert-danger';
        alertDiv.textContent = 'Failed to generate SSL certificate';
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
    if (!domain) {
        alert('Please enter a domain name');
        return;
    }
    
    fetch('/admin/save-domain', {
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
            const dnsRecords = document.getElementById('dns-records');
            const dnsRecordsBody = document.getElementById('dns-records-body');
            const verifySection = document.getElementById('verify-section');
            
            if (data.records && dnsRecordsBody) {
                dnsRecordsBody.innerHTML = data.records.map(record => `
                    <tr>
                        <td>${record.type}</td>
                        <td>${record.name}</td>
                        <td><code>${record.value}</code></td>
                    </tr>
                `).join('');
                dnsRecords.style.display = 'block';
                verifySection.style.display = 'block'; // Show verify button after save
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to save domain'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save domain settings');
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

function saveSSOSettings(event) {
    event.preventDefault();
    const form = event.target;
    const provider = form.querySelector('#provider')?.value;
    let data = {
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
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
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
    const provider = document.getElementById('provider');
    const githubFields = document.getElementById('github-fields');
    const azureFields = document.getElementById('azure-fields');
    
    if (!provider || !githubFields || !azureFields) {
        return; // Exit if elements aren't loaded yet
    }
    
    if (provider.value === 'GITHUB') {
        githubFields.style.display = 'block';
        azureFields.style.display = 'none';
    } else if (provider.value === 'AZURE') {
        githubFields.style.display = 'none';
        azureFields.style.display = 'block';
    } else {
        githubFields.style.display = 'none';
        azureFields.style.display = 'none';
    }
}

// Ensure DOM is loaded before calling toggleProviderFields
document.addEventListener('DOMContentLoaded', toggleProviderFields);

// Call toggleProviderFields on page load to set initial state
document.addEventListener('DOMContentLoaded', () => {
    toggleProviderFields();
});
