
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}

async function saveDomain() {
    const domain = document.getElementById('domain').value;
    const provider = document.getElementById('provider').value;
    
    try {
        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain, provider })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Domain settings saved successfully!');
        } else {
            alert(data.error || 'Error saving domain settings');
        }
    } catch (error) {
        alert('Error saving domain settings');
    }
}

async function verifyDomain() {
    const domain = document.getElementById('domain').value;
    if (!domain) {
        alert('Please enter a domain first');
        return;
    }
    
    try {
        const response = await fetch('/admin/verify-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Domain verified successfully!');
        } else {
            alert(data.error || 'Domain verification failed');
        }
    } catch (error) {
        alert('Error verifying domain');
    }
}

function saveSSOSettings() {
    document.getElementById('sso-form').submit();
}
