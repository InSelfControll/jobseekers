
// Dark mode toggle
function toggleDarkMode() {
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    document.body.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Set initial theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);

    // Initialize Feather icons if available
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize provider settings visibility
    toggleProviderSettings();
});

function toggleProviderSettings() {
    const provider = document.getElementById('provider').value;
    const githubSettings = document.getElementById('github-settings');
    
    if (provider === 'GITHUB') {
        githubSettings.style.display = 'block';
    } else {
        githubSettings.style.display = 'none';
    }
}

function toggleProviderSettings() {
    const provider = document.getElementById('provider').value;
    const githubSettings = document.getElementById('github-settings');
    const azureSettings = document.getElementById('azure-settings');
    
    githubSettings.style.display = provider === 'GITHUB' ? 'block' : 'none';
    azureSettings.style.display = provider === 'AZURE_AD' ? 'block' : 'none';
}

async function saveDomain(provider) {
    const domainId = provider === 'azure' ? 'azure_domain' : 'sso_domain';
    const domain = document.getElementById(domainId).value;
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Content-Type-Options': 'nosniff',
                'X-CSRF-TOKEN': csrfToken
            },
            body: JSON.stringify({
                domain: domain,
                provider: provider,
                csrf_token: csrfToken
            })
        });
        
        const data = await response.json();
        if (data.success) {
            const dnsRecords = document.getElementById('dns-records');
            dnsRecords.textContent = `${data.cname_record}\n${data.txt_record}`;
            const recordsElement = provider === 'azure' ? 'azure-domain-records' : 'domain-records';
            const dnsRecordsElement = provider === 'azure' ? 'azure-dns-records' : 'dns-records';
            document.getElementById(recordsElement).style.display = 'block';
            document.getElementById(dnsRecordsElement).textContent = `${data.cname_record}\n${data.txt_record}`;
            
            // Verify domain after saving
            await verifyDomain(provider);
        } else {
            alert(data.error || 'Failed to save domain configuration');
        }
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Error saving domain configuration');
    }
}

async function verifyDomain(provider) {
    const domainId = provider === 'azure' ? 'azure_domain' : 'sso_domain';
    const domain = document.getElementById(domainId).value;
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const verifyResponse = await fetch(`/admin/verify-domain/${provider}?domain=${domain}`);
        const verifyData = await verifyResponse.json();
        
        const statusSpan = document.getElementById('verification-status');
        if (verifyData.verified) {
            statusSpan.className = 'ms-2 text-success';
            statusSpan.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
            
            const domainInput = document.getElementById('sso_domain');
            domainInput.classList.add('is-valid');
            domainInput.setAttribute('readonly', 'true');
            domainInput.value = `${domain} (Verified)`;
        } else {
            statusSpan.className = 'ms-2 text-danger';
            statusSpan.innerHTML = '<i class="fas fa-times-circle"></i> Not Verified';
            alert('Domain verification failed. Please check your DNS records and try again.');
        }
    } catch (error) {
        console.error('Error verifying domain:', error);
        alert('Error verifying domain');
    }
}
function toggleProviderSettings() {
    const provider = document.getElementById('provider').value;
    const githubSettings = document.getElementById('github-settings');
    const azureSettings = document.getElementById('azure-settings');
    
    githubSettings.style.display = provider === 'GITHUB' ? 'block' : 'none';
    azureSettings.style.display = provider === 'AZURE_AD' ? 'block' : 'none';
}

async function saveDomain(provider) {
    const domain = document.getElementById('sso_domain').value.trim();
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ domain, provider })
        });

        const data = await response.json();
        if (data.success) {
            const statusDiv = document.getElementById('domain-status');
            statusDiv.innerHTML = `
                <span class="badge bg-warning">Pending Verification</span>
                <small class="text-muted ms-2">Shadow SSO Interface: ${data.shadow_url}</small>
            `;
            
            const dnsRecords = document.getElementById('dns-records');
            dnsRecords.innerHTML = `${data.cname_record}\n${data.txt_record}`;
            document.getElementById('domain-records').style.display = 'block';
        } else {
            alert(data.error || 'Failed to save domain');
        }
    } catch (error) {
        alert('Error saving domain');
        console.error(error);
    }
}
