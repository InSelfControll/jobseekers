
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

async function saveDomain(provider) {
    const domainInput = document.getElementById(provider === 'azure' ? 'azure_domain' : 'sso_domain');
    if (!domainInput) {
        console.error('Domain input element not found');
        return;
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
            body: JSON.stringify({ domain, provider })
        });

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
