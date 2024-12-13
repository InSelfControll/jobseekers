
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
    const domain = document.getElementById('sso_domain').value;
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
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                domain: domain,
                provider: provider
            })
        });
        
        const data = await response.json();
        if (data.success) {
            const dnsRecords = document.getElementById('dns-records');
            dnsRecords.textContent = `${data.cname_record}\n${data.txt_record}`;
            document.getElementById('domain-records').style.display = 'block';
        } else {
            alert(data.error || 'Failed to save domain configuration');
        }
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Error saving domain configuration');
    }
}
