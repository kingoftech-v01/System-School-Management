"""
Custom context processor for template variables.
Provides dz_array (w3crm theme asset configuration) and branding context.
"""


def dz_static(request):
    """Provide static/branding context variables and theme asset paths for templates."""
    return {
        'DZ_NAME': 'Aurelius School Management',
        'DZ_FULL_NAME': 'Aurelius - School Management System',
        'dz_array': {
            'public': {
                'title': 'Aurelius School Management',
                'description': 'School Management System - Manage students, courses, grades and more.',
                'favicon': 'w3crm/images/favicon.png',
            },
            'global': {
                'css': [
                    'w3crm/vendor/bootstrap/scss/bootstrap.css',
                    'w3crm/vendor/animate/animate.min.css',
                    'w3crm/vendor/perfect-scrollbar/css/perfect-scrollbar.css',
                    'w3crm/vendor/metismenu/css/metisMenu.min.css',
                    'w3crm/vendor/deznav/deznav.css',
                    'w3crm/css/style.css',
                ],
                'js': {
                    'top': [
                        'w3crm/vendor/global/global.min.js',
                    ],
                    'bottom': [
                        'w3crm/vendor/bootstrap/js/bootstrap.bundle.min.js',
                        'w3crm/vendor/perfect-scrollbar/js/perfect-scrollbar.min.js',
                        'w3crm/vendor/metismenu/js/metisMenu.min.js',
                        'w3crm/vendor/deznav/deznav.min.js',
                        'w3crm/js/deznav-init.js',
                        'w3crm/js/custom.min.js',
                    ],
                },
            },
        },
    }
