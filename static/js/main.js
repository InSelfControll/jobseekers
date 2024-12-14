
// SAML Metadata Upload Handler
function handleSamlMetadataUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(e.target.result, "text/xml");
        
        const ssoInput = document.getElementById('sso_url');
        const certInput = document.getElementById('idp_cert');
        
        if (ssoInput && xmlDoc.querySelector('SingleSignOnService[Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"]')) {
            ssoInput.value = xmlDoc.querySelector('SingleSignOnService[Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"]').getAttribute('Location');
        }
        
        if (certInput && xmlDoc.querySelector('X509Certificate')) {
            const cert = xmlDoc.querySelector('X509Certificate').textContent.trim();
            certInput.value = `-----BEGIN CERTIFICATE-----\n${cert}\n-----END CERTIFICATE-----`;
        }
    };
    reader.readAsText(file);
}

// Domain Save Function
async function saveDomain() {
    const provider = document.getElementById('provider').value;
    const sso_domain = document.getElementById('sso_domain').value.trim();
    const dnsRecordsDiv = document.getElementById('domain-records');
    const dnsRecordsPre = document.getElementById('dns-records');
    const verificationStatus = document.getElementById('verification-status');
    
    if (!sso_domain) {
        alert('Please enter a domain');
        return;
    }

    const formData = {
        domain: sso_domain,
        provider: provider,
    };

    if (provider === 'GITHUB') {
        formData.github_client_id = document.getElementById('github_client_id')?.value;
        formData.github_client_secret = document.getElementById('github_client_secret')?.value;
    } else if (provider === 'AZURE_AD' || provider === 'SAML') {
        formData.entity_id = document.getElementById('entity_id')?.value;
        formData.sso_url = document.getElementById('sso_url')?.value;
        formData.idp_cert = document.getElementById('idp_cert')?.value;
    }

    try {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (!csrfMeta) {
            throw new Error('CSRF token not found');
        }

        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfMeta.content
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.success) {
            dnsRecordsDiv.style.display = 'block';
            dnsRecordsPre.textContent = `${data.cname_record}\n${data.txt_record}`;
            verificationStatus.innerHTML = '<span class="badge bg-warning">Pending Verification</span>';
            alert('Domain saved successfully!');
        } else {
            alert(data.error || 'Failed to save domain');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving domain');
    }
}

// Domain Verification Function
async function verifyDomain() {
    const domain = document.getElementById('sso_domain').value.trim();
    const provider = document.getElementById('provider').value;
    const verificationStatus = document.getElementById('verification-status');
    
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const response = await fetch('/admin/verify-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ domain, provider })
        });

        const data = await response.json();
        if (data.success) {
            verificationStatus.innerHTML = '<span class="badge bg-success">Verified</span>';
            alert('Domain verified successfully!');
        } else {
            verificationStatus.innerHTML = '<span class="badge bg-danger">Unverified</span>';
            alert(data.error || 'Domain verification failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error verifying domain');
    }
}

// SSO Settings Save Function
async function saveSSOSettings() {
    const provider = document.getElementById('provider')?.value;
    const sso_domain = document.getElementById('sso_domain')?.value;
    
    if (!provider || !sso_domain) {
        alert('Please fill in all required fields');
        return;
    }

    const formData = {
        provider: provider,
        domain: sso_domain
    };

    if (provider === 'SAML' || provider === 'AZURE_AD') {
        formData.entity_id = document.getElementById('entity_id')?.value;
        formData.sso_url = document.getElementById('sso_url')?.value;
        formData.idp_cert = document.getElementById('idp_cert')?.value;
    } else if (provider === 'GITHUB') {
        formData.github_client_id = document.getElementById('github_client_id')?.value;
        formData.github_client_secret = document.getElementById('github_client_secret')?.value;
    }
    
    try {
        const response = await fetch('/admin/update-saml-config', {
            method: 'POST',
            body: JSON.stringify(formData),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('SSO settings saved successfully');
            location.reload();
        } else {
            alert(result.error || 'Failed to save SSO settings');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving SSO settings');
    }
}

// Theme Toggle Function
function toggleTheme() {
    const body = document.body;
    const icon = document.getElementById('themeIcon');
    const currentTheme = body.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    if (icon) {
        icon.setAttribute('data-feather', newTheme === 'dark' ? 'moon' : 'sun');
        feather.replace();
    }
    
    // Keep container styles consistent
    const containers = document.querySelectorAll('.card, .container, .card-title, h1, h2, h3, h4, h5, h6, p, label, .form-label');
    containers.forEach(container => {
        container.style.backgroundColor = 'var(--container-bg)';
        container.style.color = 'var(--text-color)';
    });
    
    // Update navbar styles
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.style.backgroundColor = 'var(--navbar-bg)';
    }
}

// Provider Settings Toggle Function
function toggleProviderSettings() {
    const provider = document.getElementById('provider').value;
    const githubSettings = document.getElementById('github-settings');
    const azureSettings = document.getElementById('azure-settings');
    const samlSettings = document.getElementById('saml-settings');
    
    if (githubSettings) githubSettings.style.display = provider === 'GITHUB' ? 'block' : 'none';
    if (azureSettings) azureSettings.style.display = provider === 'AZURE_AD' ? 'block' : 'none';
    if (samlSettings) samlSettings.style.display = provider === 'SAML' ? 'block' : 'none';
}

// Initialize theme on page load
// Register form handling
function handleRegisterForm() {
    const form = document.getElementById('registerForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = document.getElementById('registerButton');
        const errorDiv = document.getElementById('registerError');
        
        try {
            button.disabled = true;
            const formData = new FormData(form);
            
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json();
            if (data.error) {
                errorDiv.textContent = data.error;
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Registration error:', error);
            errorDiv.textContent = 'An error occurred during registration. Please try again.';
            errorDiv.style.display = 'block';
        } finally {
            button.disabled = false;
        }
    });
}

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                const data = await response.json();
                if (data.error) {
                    errorDiv.textContent = data.error;
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            errorDiv.textContent = 'An error occurred. Please try again.';
            errorDiv.style.display = 'block';
        } finally {
            button.disabled = false;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    handleRegisterForm();
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.setAttribute('data-feather', savedTheme === 'dark' ? 'moon' : 'sun');
        feather.replace();
    }
    
    const provider = document.getElementById('provider');
    if (provider) {
        provider.addEventListener('change', toggleProviderSettings);
        toggleProviderSettings();
    }
    
    const samlMetadataInput = document.getElementById('saml-metadata');
    if (samlMetadataInput) {
        samlMetadataInput.addEventListener('change', handleSamlMetadataUpload);
    }
});
function toggleProviderSettings() {
    const provider = document.getElementById('provider').value;
    document.getElementById('github-settings').style.display = provider === 'GITHUB' ? 'block' : 'none';
    document.getElementById('saml-settings').style.display = provider === 'SAML' ? 'block' : 'none';
    document.getElementById('azure-settings').style.display = provider === 'AZURE_AD' ? 'block' : 'none';
}

function saveDomain() {
    const domain = document.getElementById('sso_domain').value;
    const provider = document.getElementById('provider').value;
    const githubClientId = document.getElementById('github-settings').querySelector('input[name="github_client_id"]').value;
    const githubClientSecret = document.getElementById('github-settings').querySelector('input[name="github_client_secret"]').value;

    fetch('/admin/save-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            domain,
            provider,
            github_client_id: githubClientId,
            github_client_secret: githubClientSecret
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('dns-records').textContent = `${data.cname_record}\n${data.txt_record}`;
            document.getElementById('domain-records').style.display = 'block';
        } else {
            alert(data.error);
        }
    });
}

function verifyDomain() {
    const domain = document.getElementById('sso_domain').value;
    const provider = document.getElementById('provider').value;

    fetch('/admin/verify-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            domain,
            provider
        })
    })
    .then(response => response.json())
    .then(data => {
        const status = document.getElementById('verification-status');
        if (data.success) {
            status.textContent = 'Domain verified successfully!';
            status.className = 'alert alert-success';
        } else {
            status.textContent = data.error || 'Domain verification failed';
            status.className = 'alert alert-danger';
        }
    });
}

function saveSSOSettings() {
    const provider = document.getElementById('provider').value;
    const formData = {};

    if (provider === 'SAML' || provider === 'AZURE_AD') {
        formData.entity_id = document.getElementById('entity_id').value;
        formData.sso_url = document.getElementById('sso_url').value;
        formData.idp_cert = document.getElementById('idp_cert').value;
    }

    fetch('/admin/update-saml-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('SSO settings saved successfully');
        } else {
            alert(data.error || 'Failed to save SSO settings');
        }
    });
}
