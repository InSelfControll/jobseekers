
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
    const form = document.getElementById('ssoForm');
    const provider = document.getElementById('provider').value;
    const formData = new FormData();

    // Add common fields
    formData.append('provider', provider);
    formData.append('domain', document.getElementById('sso_domain').value);

    if (provider === 'SAML' || provider === 'AZURE_AD') {
        formData.append('entity_id', document.getElementById('entity_id').value);
        formData.append('sso_url', document.getElementById('sso_url').value);
        formData.append('idp_cert', document.getElementById('idp_cert').value);
    } else if (provider === 'GITHUB') {
        formData.append('github_client_id', document.getElementById('github_client_id').value);
        formData.append('github_client_secret', document.getElementById('github_client_secret').value);
    }
    
    try {
        const response = await fetch('/admin/update-saml-config', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
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
document.addEventListener('DOMContentLoaded', () => {
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
