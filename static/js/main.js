
// Domain configuration
function toggleSSLSections() {
    const letsEncryptSection = document.getElementById('letsEncryptSection');
    const customCertSection = document.getElementById('customCertSection');
    const selectedOption = document.querySelector('input[name="sslOption"]:checked');
    
    if (letsEncryptSection && customCertSection && selectedOption) {
        letsEncryptSection.style.display = selectedOption.value === 'letsencrypt' ? 'block' : 'none';
        customCertSection.style.display = selectedOption.value === 'custom' ? 'block' : 'none';
    }
}

function saveDomain() {
    const domainInput = document.getElementById('domain');
    if (!domainInput) return;
    
    const domain = domainInput.value;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    fetch('/admin/save-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ domain })
    })
    .then(response => response.json())
    .then(data => {
        const dnsRecords = document.getElementById('dns-records');
        const dnsRecordsBody = document.getElementById('dns-records-body');
        
        if (data.success && dnsRecords && dnsRecordsBody) {
            dnsRecords.style.display = 'block';
            dnsRecordsBody.innerHTML = `
                <tr>
                    <td>CNAME</td>
                    <td>${domain}</td>
                    <td>${data.records[0].value}</td>
                </tr>`;
        } else {
            alert('Error: ' + (data.error || 'Failed to save domain'));
        }
    });
}

function verifyDomain() {
    const domainInput = document.getElementById('domain');
    if (!domainInput) return;
    
    const domain = domainInput.value;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    fetch('/admin/verify-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ domain })
    })
    .then(response => response.json())
    .then(data => {
        const sslSection = document.getElementById('ssl-section');
        if (data.success && sslSection) {
            alert('Domain verified successfully!');
            sslSection.style.display = 'block';
            const verifiedDomainsDiv = document.querySelector('.alert-info, .alert-success');
            if (verifiedDomainsDiv) {
                verifiedDomainsDiv.className = 'alert alert-success';
                verifiedDomainsDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${data.domain}`;
            }
        } else {
            alert('Verification failed: ' + data.error);
        }
    });
}

// Initialize event listeners only if elements exist
document.addEventListener('DOMContentLoaded', () => {
    const radioButtons = document.querySelectorAll('input[name="sslOption"]');
    if (radioButtons.length) {
        radioButtons.forEach(radio => radio.addEventListener('change', toggleSSLSections));
        toggleSSLSections();
    }
});
