
async function handleSamlMetadataUpload(event) {
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

async function saveDomain() {
    const provider = document.getElementById('provider').value;
    const domain = document.getElementById('sso_domain').value.trim();
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    const formData = {
        domain,
        provider,
    };

    if (provider === 'GITHUB') {
        formData.github_client_id = document.getElementById('github_client_id')?.value;
        formData.github_client_secret = document.getElementById('github_client_secret')?.value;
    } else if (provider === 'AZURE_AD' || provider === 'SAML') {
        formData.entity_id = document.getElementById('entity_id')?.value;
        formData.sso_url = document.getElementById('sso_url')?.value;
        formData.idp_cert = document.getElementById('idp_cert')?.value;
    }

    const domain = domainInput.value.trim();
    if (!domain) {
        alert('Please enter a domain');
        return;
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

        if (provider === 'AZURE_AD' || provider === 'SAML') {
            await fetch('/admin/update-saml-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfMeta.content
                },
                body: JSON.stringify({
                    entity_id: formData.entity_id,
                    sso_url: formData.sso_url,
                    idp_cert: formData.idp_cert
                })
            });
        }

        const data = await response.json();
        if (data.success) {
            const statusDiv = document.getElementById('domain-status');
            const dnsRecords = document.getElementById('dns-records');
            const domainRecords = document.getElementById('domain-records');
            
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <span class="badge bg-warning">Pending Verification</span>
                    <small class="text-muted ms-2">Shadow SSO Interface: ${data.shadow_url}</small>
                `;
            }
            
            if (dnsRecords) {
                dnsRecords.innerHTML = `${data.cname_record}\n${data.txt_record}`;
            }
            
            if (domainRecords) {
                domainRecords.style.display = 'block';
            }
        } else {
            alert(data.error || 'Failed to save domain');
        }
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Error saving domain: ' + error.message);
    }
}

function toggleDarkMode() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function saveSSOSettings() {
    const form = document.getElementById('ssoForm');
    const formData = new FormData(form);
    
    fetch('/admin/update-saml-config', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('SSO settings saved successfully');
        } else {
            alert(data.error || 'Failed to save SSO settings');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving SSO settings');
    });
}

function toggleProviderSettings() {
    const provider = document.getElementById('provider')?.value;
    const githubSettings = document.getElementById('github-settings');
    const azureSettings = document.getElementById('azure-settings');
    const samlSettings = document.getElementById('saml-settings');
    
    if (githubSettings) {
        githubSettings.style.display = provider === 'GITHUB' ? 'block' : 'none';
    }
    if (azureSettings) {
        azureSettings.style.display = provider === 'AZURE_AD' ? 'block' : 'none';
    }
    if (samlSettings) {
        samlSettings.style.display = provider === 'SAML' ? 'block' : 'none';
    }
}
