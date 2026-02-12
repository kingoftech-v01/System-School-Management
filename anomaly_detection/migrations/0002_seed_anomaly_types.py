"""Seed default anomaly types and thresholds."""
from django.db import migrations


ANOMALY_TYPES = [
    {
        'code': 'grade_sudden_jump',
        'name': 'Sudden Grade Jump',
        'domain': 'grade',
        'severity': 'high',
        'description': 'Student score deviates significantly from their personal or class average.',
        'notify_roles': ['professor', 'direction', 'admin'],
        'thresholds': [
            ('std_dev_multiplier', '2.00', 'Standard deviation multiplier for statistical check'),
            ('jump_threshold', '20.00', 'Absolute point jump above average'),
        ],
    },
    {
        'code': 'grade_abnormally_high',
        'name': 'Abnormally High Grade',
        'domain': 'grade',
        'severity': 'medium',
        'description': 'Individual score is abnormally high compared to the class average.',
        'notify_roles': ['professor', 'direction', 'admin'],
        'thresholds': [
            ('class_std_dev_multiplier', '2.50', 'Class standard deviation multiplier'),
        ],
    },
    {
        'code': 'grade_unauthorized_change',
        'name': 'Unauthorized Grade Change',
        'domain': 'grade',
        'severity': 'critical',
        'description': 'Grade changed by someone not allocated to the course, or excessive modifications.',
        'notify_roles': ['direction', 'admin'],
        'thresholds': [
            ('max_changes_per_course', '5.00', 'Maximum grade changes per student per course'),
        ],
    },
    {
        'code': 'payment_amount_mismatch',
        'name': 'Payment Amount Mismatch',
        'domain': 'payment',
        'severity': 'critical',
        'description': 'Payment amount does not match the invoice amount.',
        'notify_roles': ['accountant', 'direction', 'admin'],
        'thresholds': [],
    },
    {
        'code': 'payment_double',
        'name': 'Double Payment',
        'domain': 'payment',
        'severity': 'critical',
        'description': 'Multiple completed payments for the same invoice.',
        'notify_roles': ['accountant', 'direction', 'admin'],
        'thresholds': [],
    },
    {
        'code': 'payment_status_reversal',
        'name': 'Payment Status Reversal',
        'domain': 'payment',
        'severity': 'high',
        'description': 'Suspicious payment status transition (e.g. completed to failed).',
        'notify_roles': ['accountant', 'direction', 'admin'],
        'thresholds': [],
    },
    {
        'code': 'payment_fee_mismatch',
        'name': 'Invoice/Fee Structure Mismatch',
        'domain': 'payment',
        'severity': 'high',
        'description': 'Invoice amount does not match the associated fee structure total.',
        'notify_roles': ['accountant', 'direction', 'admin'],
        'thresholds': [],
    },
    {
        'code': 'enrollment_duplicate',
        'name': 'Duplicate Enrollment',
        'domain': 'enrollment',
        'severity': 'high',
        'description': 'Multiple enrollment applications with same email, program, and academic year.',
        'notify_roles': ['direction', 'admin', 'secretary'],
        'thresholds': [],
    },
    {
        'code': 'enrollment_invalid_transition',
        'name': 'Invalid Status Transition',
        'domain': 'enrollment',
        'severity': 'medium',
        'description': 'Enrollment status changed through an invalid transition path.',
        'notify_roles': ['direction', 'admin', 'secretary'],
        'thresholds': [],
    },
    {
        'code': 'enrollment_unauthorized_approval',
        'name': 'Unauthorized Enrollment Approval',
        'domain': 'enrollment',
        'severity': 'critical',
        'description': 'Enrollment approved by user without proper authority.',
        'notify_roles': ['direction', 'admin'],
        'thresholds': [],
    },
    {
        'code': 'login_brute_force',
        'name': 'Brute Force Login Attempt',
        'domain': 'login',
        'severity': 'high',
        'description': 'Multiple failed login attempts from a single source.',
        'notify_roles': ['admin'],
        'thresholds': [
            ('failure_threshold', '5.00', 'Number of failures before alert'),
            ('window_minutes', '30.00', 'Time window in minutes'),
        ],
    },
    {
        'code': 'login_unusual_time',
        'name': 'Unusual Login Time',
        'domain': 'login',
        'severity': 'low',
        'description': 'Login outside normal operating hours.',
        'notify_roles': ['admin'],
        'thresholds': [
            ('start_hour', '6.00', 'Normal hours start (24h format)'),
            ('end_hour', '23.00', 'Normal hours end (24h format)'),
        ],
    },
    {
        'code': 'login_device_change',
        'name': 'Device Change Detected',
        'domain': 'login',
        'severity': 'medium',
        'description': 'User agent changed between consecutive login sessions.',
        'notify_roles': ['admin'],
        'thresholds': [],
    },
]


def seed_anomaly_types(apps, schema_editor):
    AnomalyType = apps.get_model('anomaly_detection', 'AnomalyType')
    AnomalyThreshold = apps.get_model('anomaly_detection', 'AnomalyThreshold')

    for type_data in ANOMALY_TYPES:
        thresholds = type_data.pop('thresholds')
        anomaly_type, _ = AnomalyType.objects.get_or_create(
            code=type_data['code'],
            defaults=type_data,
        )
        for key, value, description in thresholds:
            AnomalyThreshold.objects.get_or_create(
                anomaly_type=anomaly_type,
                key=key,
                defaults={'value': value, 'description': description},
            )


def reverse_seed(apps, schema_editor):
    AnomalyType = apps.get_model('anomaly_detection', 'AnomalyType')
    codes = [t['code'] for t in ANOMALY_TYPES]
    AnomalyType.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('anomaly_detection', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_anomaly_types, reverse_seed),
    ]
