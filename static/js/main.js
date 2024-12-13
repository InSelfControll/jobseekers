
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

// Initialize Feather icons
document.addEventListener('DOMContentLoaded', () => {
    feather.replace();
    
    // Initialize location picker for job posting
    const locationInputs = document.querySelectorAll('input[name="location"]');
    locationInputs.forEach(input => {
        input.addEventListener('blur', async (e) => {
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(e.target.value)}`
                );
                const data = await response.json();
                
                if (data.length > 0) {
                    const form = e.target.closest('form');
                    const latInput = form.querySelector('input[name="latitude"]');
                    const lngInput = form.querySelector('input[name="longitude"]');
                    
                    latInput.value = data[0].lat;
                    lngInput.value = data[0].lon;
                }
            } catch (error) {
                console.error('Error getting coordinates:', error);
                alert('Error getting location coordinates. Please try again.');
            }
        });
    });
    
    // Auto-submit status changes
    const statusSelects = document.querySelectorAll('select[name="status"]');
    statusSelects.forEach(select => {
        select.addEventListener('change', e => {
            e.target.form.submit();
        });
    });
    
    // Message scroll to bottom
    const messageContainers = document.querySelectorAll('.messages-container');
    messageContainers.forEach(container => {
        container.scrollTop = container.scrollHeight;
    });
});

// Form validation
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', e => {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
});
async function saveDomain(provider) {
    const domain = document.getElementById('sso_domain').value;
    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `domain=${encodeURIComponent(domain)}&provider=${encodeURIComponent(provider)}`
        });
        
        const data = await response.json();
        if (data.success) {
            document.getElementById('dns-records').textContent = 
                `${data.cname_record}\n${data.txt_record}`;
            document.getElementById('domain-records').style.display = 'block';
        }
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Error saving domain configuration');
    }
}
