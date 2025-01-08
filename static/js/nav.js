document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const themeIcon = themeToggle.querySelector('i');

        function updateTheme(isDark) {
            document.body.classList.toggle('light-mode', !isDark);
            themeIcon.setAttribute('data-feather', isDark ? 'sun' : 'moon');
            feather.replace();
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }

        // Initialize theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        updateTheme(savedTheme === 'dark');

        // Theme toggle click handler
        themeToggle.addEventListener('click', () => {
            updateTheme(document.body.classList.contains('light-mode'));
        });
    }

    // Handle dropdown toggle
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        const dropdownToggle = userDropdown.querySelector('.dropdown-toggle');
        const dropdownMenu = userDropdown.querySelector('.dropdown-menu');

        dropdownToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }

    // Add active class handling for navigation
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});