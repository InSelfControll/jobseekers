// Initialize Feather icons
document.addEventListener('DOMContentLoaded', () => {
    feather.replace();
    
    // Initialize location picker for job posting
    const locationInput = document.querySelector('input[name="location"]');
    if (locationInput) {
        locationInput.addEventListener('change', async (e) => {
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(e.target.value)}`
                );
                const data = await response.json();
                
                if (data.length > 0) {
                    document.getElementById('latitude').value = data[0].lat;
                    document.getElementById('longitude').value = data[0].lon;
                }
            } catch (error) {
                console.error('Error getting coordinates:', error);
            }
        });
    }
    
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
