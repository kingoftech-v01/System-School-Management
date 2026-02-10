"""
Custom context processor for template rendering.
Provides static file path configuration for the w3crm theme.
"""


def dz_static(request):
    """
    Context processor for static file paths.
    Provides the dz_array configuration used by templates.
    """
    return {
        'STATIC_PREFIX': '/static/',
        'MEDIA_PREFIX': '/media/',
        'dz_array': {
            'public': {
                'title': 'School Management System',
                'description': 'Multi-tenant School Management Platform',
                'favicon': 'w3crm/images/favicon.png',
            },
            'global': {
                'css': [
                    # Vendor CSS
                    'w3crm/vendor/bootstrap/css/bootstrap.min.css',
                    'w3crm/vendor/perfect-scrollbar/css/perfect-scrollbar.css',
                    'w3crm/vendor/metismenu/css/metisMenu.min.css',
                    # Font Awesome
                    'w3crm/icons/fontawesome/css/all.min.css',
                    # Theme CSS
                    'w3crm/css/perfect-scrollbar.css',
                    'w3crm/css/style.css',
                ],
                'js': {
                    'top': [
                        # Global JS at top
                        'w3crm/vendor/global/global.min.js',
                    ],
                    'bottom': [
                        # JS at bottom
                        'w3crm/vendor/bootstrap/js/bootstrap.bundle.min.js',
                        'w3crm/vendor/perfect-scrollbar/js/perfect-scrollbar.min.js',
                        'w3crm/vendor/metismenu/js/metisMenu.min.js',
                        'w3crm/js/deznav-init.js',
                        'w3crm/js/custom.min.js',
                    ],
                },
            },
        },
    }
