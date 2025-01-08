document.addEventListener('DOMContentLoaded', function() {
    initializeFeatherIcons();
    initializeTheme();
    initializeDropdowns();
    initializeNavigation();
    initializeSSLHandling();
    initializeSmoothScrolling();
    initializeLayoutPreference();
    initializeProfilePicture();
});

function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const themeIcon = themeToggle.querySelector('i');

        function updateTheme(isDark) {
            document.body.classList.toggle('light-mode', !isDark);
            themeIcon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }

        const savedTheme = localStorage.getItem('theme') || 'dark';
        updateTheme(savedTheme === 'dark');

        themeToggle.addEventListener('click', () => {
            updateTheme(document.body.classList.contains('light-mode'));
        });
    }
}

function toggleDarkMode() {
    const body = document.body;
    const isDarkMode = !body.classList.contains('dark-mode');
    body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');

    const themeIcon = document.querySelector('[data-feather]');
    if (themeIcon) {
        themeIcon.setAttribute('data-feather', isDarkMode ? 'sun' : 'moon');
        feather.replace();
    }
}

// Icon Management
function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function initializeDropdowns() {
    document.querySelectorAll('.dropdown-submenu').forEach(submenu => {
        submenu.addEventListener('mouseenter', function() {
            const menu = this.querySelector('.dropdown-menu');
            const rect = menu.getBoundingClientRect();

            // Check if submenu would go off screen
            if (rect.right > window.innerWidth) {
                menu.style.left = 'auto';
                menu.style.right = '100%';
            }
        });
    });
}

function initializeNavigation() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

function setupDropdownHandling(toggle, menu) {
    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        menu.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
            menu.classList.remove('show');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            menu.classList.remove('show');
        }
    });
}

function setupMobileMenu(button, nav) {
    button.addEventListener('click', () => {
        nav.classList.toggle('show');
        button.setAttribute('aria-expanded', nav.classList.contains('show'));
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && nav.classList.contains('show')) {
            nav.classList.remove('show');
            button.setAttribute('aria-expanded', 'false');
        }
    });
}

// SSO Provider Management
function toggleProviderFields() {
    const provider = document.getElementById('provider');
    const githubFields = document.getElementById('github-fields');
    const azureFields = document.getElementById('azure-fields');

    if (provider && githubFields && azureFields) {
        githubFields.style.display = provider.value === 'GITHUB' ? 'block' : 'none';
        azureFields.style.display = provider.value === 'AZURE' ? 'block' : 'none';
    }
}

// SSL and Domain Management
function initializeSSLHandling() {
    const radioButtons = document.querySelectorAll('input[name="sslOption"]');
    if (radioButtons.length) {
        radioButtons.forEach(radio => radio.addEventListener('change', toggleSSLSections));
        toggleSSLSections();
    }
}

function toggleSSLSections() {
    const letsEncryptSection = document.getElementById('letsEncryptSection');
    const customCertSection = document.getElementById('customCertSection');
    const selectedOption = document.querySelector('input[name="sslOption"]:checked');

    if (letsEncryptSection && customCertSection && selectedOption) {
        letsEncryptSection.style.display = selectedOption.value === 'letsencrypt' ? 'block' : 'none';
        customCertSection.style.display = selectedOption.value === 'custom' ? 'block' : 'none';
    }
}

// API Calls
async function saveDomain() {
    const domainInput = document.getElementById('domain');
    if (!domainInput) return;

    try {
        const response = await fetch('/admin/save-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? .content
            },
            body: JSON.stringify({ domain: domainInput.value })
        });

        const data = await response.json();
        updateDNSRecords(data);
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Failed to save domain');
    }
}

// Utility Functions
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initializeLayoutPreference() {
    const layoutToggle = document.getElementById('layoutToggle');
    const navLinks = document.getElementById('navLinks');

    if (layoutToggle && navLinks) {
        const savedLayout = localStorage.getItem('navLayout') || 'horizontal';
        updateNavLayout(savedLayout);

        layoutToggle.addEventListener('click', toggleNavLayout);
    }
}

function toggleNavLayout() {
    const currentLayout = localStorage.getItem('navLayout') || 'horizontal';
    const newLayout = currentLayout === 'horizontal' ? 'vertical' : 'horizontal';
    updateNavLayout(newLayout);
    localStorage.setItem('navLayout', newLayout);
}

function updateNavLayout(layout) {
    const body = document.body;
    const navLinks = document.getElementById('navLinks');

    if (layout === 'vertical') {
        body.classList.add('vertical-nav');
        navLinks.classList.add('vertical');
    } else {
        body.classList.remove('vertical-nav');
        navLinks.classList.remove('vertical');
    }
}

function openProfilePictureModal() {
    const modal = new bootstrap.Modal(document.getElementById('profilePictureModal'));
    modal.show();
}

function initializeProfilePicture() {
    const fileInput = document.querySelector('input[name="profile_picture"]');
    const preview = document.getElementById('picturePreview');
    const previewContainer = document.querySelector('.preview-container');

    if (fileInput && preview) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    previewContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    const form = document.getElementById('profilePictureForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(form);

            try {
                const response = await fetch('/update-profile-picture', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        const userAvatar = document.getElementById('userAvatar');
                        userAvatar.innerHTML = `<img src="${data.picture_url}" alt="Profile">`;
                        bootstrap.Modal.getInstance(document.getElementById('profilePictureModal')).hide();
                    } else {
                        alert('Failed to update profile picture: ' + data.error);
                    }
                }
            } catch (error) {
                console.error('Error uploading profile picture:', error);
                alert('Failed to upload profile picture');
            }
        });
    }
}