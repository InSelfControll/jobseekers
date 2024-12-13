
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
});

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
