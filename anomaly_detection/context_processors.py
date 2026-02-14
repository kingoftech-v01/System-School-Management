def anomaly_alert_count(request):
    """Add unread anomaly alert count for admin/direction users."""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'anomaly_alert_count': 0}

    role = getattr(request.user, 'role', '')
    privileged_roles = ('direction', 'admin', 'accountant', 'professor', 'secretary', 'registrar')

    if role in privileged_roles or request.user.is_superuser:
        from anomaly_detection.models import AnomalyAlert
        count = AnomalyAlert.objects.filter(status='new').count()
        return {'anomaly_alert_count': count}

    return {'anomaly_alert_count': 0}
