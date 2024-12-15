
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}

function toggleProviderFields() {
    const provider = document.getElementById('provider').value;
    document.getElementById('github-fields').style.display = provider === 'GITHUB' ? 'block' : 'none';
    document.getElementById('saml-fields').style.display = provider === 'SAML' ? 'block' : 'none';
}

function saveDomain() {
    const domain = document.getElementById('domain').value;
    const provider = document.getElementById('provider').value;
    
    fetch('/admin/save-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ domain, provider })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('dns-records').style.display = 'block';
            document.getElementById('dns-output').textContent = 
                `${data.cname_record}\n${data.txt_record}`;
            alert('Domain saved successfully!');
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function verifyDomain() {
    const domain = document.getElementById('domain').value;
    const provider = document.getElementById('provider').value;
    
    fetch('/admin/verify-domain', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ domain, provider })
    })
    .then(response => response.json())
    .then(data => {
        if (data.verified) {
            alert('Domain verified successfully!');
        } else {
            alert('Domain verification failed. Please check your DNS records.');
        }
    });
}

function saveSSOSettings() {
    const provider = document.getElementById('provider').value;
    const data = {
        domain: document.getElementById('domain').value,
        provider: provider
    };
    
    if (provider === 'GITHUB') {
        data.client_id = document.getElementById('client_id').value;
        data.client_secret = document.getElementById('client_secret').value;
    } else if (provider === 'SAML') {
        data.saml_manifest = document.getElementById('saml_manifest').value;
    }
    
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
