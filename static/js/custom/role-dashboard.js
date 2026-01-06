/**
 * Role-Based Dashboard JavaScript
 * Handles sidebar navigation, mobile menu, dropdowns, and dashboard interactions
 */

document.addEventListener('DOMContentLoaded', function() {

    // ========================================
    // SIDEBAR TOGGLE FUNCTIONALITY
    // ========================================

    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('collapsed');

            // Update icon
            const icon = this.querySelector('i');
            if (icon) {
                if (sidebar.classList.contains('collapsed')) {
                    icon.classList.remove('ri-menu-fold-line');
                    icon.classList.add('ri-menu-unfold-line');
                } else {
                    icon.classList.remove('ri-menu-unfold-line');
                    icon.classList.add('ri-menu-fold-line');
                }
            }

            // Save state to localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });

        // Restore sidebar state from localStorage
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
        if (sidebarCollapsed === 'true') {
            sidebar.classList.add('collapsed');
            const icon = sidebarToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('ri-menu-fold-line');
                icon.classList.add('ri-menu-unfold-line');
            }
        }
    }

    // ========================================
    // MOBILE MENU TOGGLE
    // ========================================

    const mobileMenuToggle = document.getElementById('mobileMenuToggle');

    if (mobileMenuToggle && sidebar) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('active');

            // Update body overflow to prevent scrolling when menu is open
            if (sidebar.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768 && sidebar) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggle = mobileMenuToggle && mobileMenuToggle.contains(event.target);

            if (!isClickInsideSidebar && !isClickOnToggle && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    });

    // ========================================
    // ACTIVE MENU ITEM HIGHLIGHTING
    // ========================================

    function highlightActiveMenuItem() {
        const currentPath = window.location.pathname;
        const menuLinks = document.querySelectorAll('.menu-link');

        menuLinks.forEach(link => {
            const linkPath = new URL(link.href).pathname;
            const menuItem = link.closest('.menu-item');

            if (menuItem) {
                if (currentPath === linkPath || currentPath.startsWith(linkPath + '/')) {
                    menuItem.classList.add('active');
                } else {
                    menuItem.classList.remove('active');
                }
            }
        });
    }

    highlightActiveMenuItem();

    // ========================================
    // SEARCH FUNCTIONALITY
    // ========================================

    const searchForm = document.querySelector('.search-form');
    const searchInput = searchForm ? searchForm.querySelector('input[name="q"]') : null;

    if (searchForm && searchInput) {
        // Add search icon animation on focus
        searchInput.addEventListener('focus', function() {
            this.parentElement.classList.add('search-focused');
        });

        searchInput.addEventListener('blur', function() {
            this.parentElement.classList.remove('search-focused');
        });

        // Handle search form submission
        searchForm.addEventListener('submit', function(e) {
            if (searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // ========================================
    // NOTIFICATION DROPDOWN
    // ========================================

    const notificationDropdown = document.querySelector('.navbar-icon[data-bs-toggle="dropdown"]');

    if (notificationDropdown) {
        notificationDropdown.addEventListener('click', function() {
            // Mark notifications as read when dropdown is opened
            const badge = this.querySelector('.badge');
            if (badge) {
                setTimeout(() => {
                    badge.style.opacity = '0.5';
                }, 500);
            }
        });
    }

    // ========================================
    // STAT CARD ANIMATIONS
    // ========================================

    const statCards = document.querySelectorAll('.stat-card');

    if (statCards.length > 0) {
        // Animate stat values on page load
        statCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'all 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);

            // Animate number count-up effect
            const statValue = card.querySelector('.stat-value');
            if (statValue && !isNaN(parseFloat(statValue.textContent))) {
                animateValue(statValue, 0, parseFloat(statValue.textContent), 1000);
            }
        });
    }

    function animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        const isDecimal = end % 1 !== 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = isDecimal ? current.toFixed(2) : Math.floor(current);
        }, 16);
    }

    // ========================================
    // TABLE ENHANCEMENTS
    // ========================================

    // Initialize DataTables if available and tables exist
    if (typeof $.fn.DataTable !== 'undefined') {
        const tables = document.querySelectorAll('table.table-hover, table.table-striped');

        tables.forEach(table => {
            // Only initialize if not already initialized and has more than 10 rows
            const rowCount = table.querySelectorAll('tbody tr').length;

            if (rowCount > 10 && !$.fn.DataTable.isDataTable(table)) {
                $(table).DataTable({
                    responsive: true,
                    pageLength: 10,
                    language: {
                        search: "_INPUT_",
                        searchPlaceholder: "Search...",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        paginate: {
                            first: "First",
                            last: "Last",
                            next: "Next",
                            previous: "Previous"
                        }
                    },
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rt<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p">>',
                });
            }
        });
    }

    // ========================================
    // CHARTS INITIALIZATION
    // ========================================

    // This section will be populated by page-specific chart initialization
    // Charts are initialized in the individual dashboard template files

    // ========================================
    // FORM VALIDATION ENHANCEMENTS
    // ========================================

    const forms = document.querySelectorAll('form[data-validate="true"]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // ========================================
    // TOOLTIPS & POPOVERS
    // ========================================

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // ========================================
    // AUTO-DISMISS ALERTS
    // ========================================

    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');

    alerts.forEach(alert => {
        const dismissTime = parseInt(alert.getAttribute('data-auto-dismiss')) || 5000;

        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, dismissTime);
    });

    // ========================================
    // RESPONSIVE UTILITIES
    // ========================================

    // Handle window resize events
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Close mobile sidebar when resizing to desktop
            if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                document.body.style.overflow = '';
            }
        }, 250);
    });

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     */
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toastEl);

        const toast = new bootstrap.Toast(toastEl);
        toast.show();

        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    };

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Confirm action with modal
     * @param {string} message - Confirmation message
     * @param {Function} callback - Callback function if confirmed
     */
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };

    // ========================================
    // LOGOUT CONFIRMATION
    // ========================================

    const logoutForms = document.querySelectorAll('.sidebar-logout-form, form[action*="logout"]');

    logoutForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });

    // ========================================
    // PAGE LOADING INDICATOR
    // ========================================

    // Show loading indicator when navigating to new pages
    const navigationLinks = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])');

    navigationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Only show loader for internal navigation
            if (this.hostname === window.location.hostname && !this.hasAttribute('data-bs-toggle')) {
                showPageLoader();
            }
        });
    });

    function showPageLoader() {
        let loader = document.getElementById('pageLoader');

        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'pageLoader';
            loader.className = 'page-loader';
            loader.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            `;
            document.body.appendChild(loader);

            // Add CSS for loader
            const style = document.createElement('style');
            style.textContent = `
                .page-loader {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 99999;
                }
            `;
            document.head.appendChild(style);
        }

        loader.style.display = 'flex';
    }

    // Hide loader when page loads
    window.addEventListener('load', function() {
        const loader = document.getElementById('pageLoader');
        if (loader) {
            loader.style.display = 'none';
        }
    });

    console.log('Role Dashboard JavaScript initialized successfully');
});
