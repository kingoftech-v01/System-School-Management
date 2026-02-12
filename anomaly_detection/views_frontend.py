from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import direction_only
from .models import AnomalyAlert, AnomalyType


@login_required
@direction_only
def anomaly_dashboard(request):
    """Anomaly detection dashboard with summary stats."""
    alerts = AnomalyAlert.objects.select_related('anomaly_type', 'user')

    # Summary counts by severity
    severity_counts = dict(
        alerts.filter(status='new').values_list('severity').annotate(c=Count('id')).values_list('severity', 'c')
    )

    # Counts by domain
    domain_counts = dict(
        alerts.filter(status='new')
        .values_list('anomaly_type__domain')
        .annotate(c=Count('id'))
        .values_list('anomaly_type__domain', 'c')
    )

    # Status breakdown
    status_counts = dict(
        alerts.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
    )

    # Recent alerts (last 10)
    recent_alerts = alerts.order_by('-detected_at')[:10]

    # Total new alerts
    total_new = alerts.filter(status='new').count()

    return render(request, 'anomaly_detection/dashboard.html', {
        'severity_counts': severity_counts,
        'domain_counts': domain_counts,
        'status_counts': status_counts,
        'recent_alerts': recent_alerts,
        'total_new': total_new,
        'page_title': _('Anomaly Detection Dashboard'),
    })


@login_required
@direction_only
def alert_list(request):
    """Paginated list of anomaly alerts with filters."""
    alerts = AnomalyAlert.objects.select_related('anomaly_type', 'user').order_by('-detected_at')

    # Filters
    domain = request.GET.get('domain', '').strip()
    if domain:
        alerts = alerts.filter(anomaly_type__domain=domain)

    severity = request.GET.get('severity', '').strip()
    if severity:
        alerts = alerts.filter(severity=severity)

    status = request.GET.get('status', '').strip()
    if status:
        alerts = alerts.filter(status=status)

    search = request.GET.get('search', '').strip()
    if search:
        alerts = alerts.filter(
            Q(title__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search)
        )

    paginator = Paginator(alerts, 25)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)

    return render(request, 'anomaly_detection/alert_list.html', {
        'alerts': page,
        'total_count': paginator.count,
        'domain_choices': AnomalyType.DOMAIN_CHOICES,
        'severity_choices': AnomalyType.SEVERITY_CHOICES,
        'status_choices': AnomalyAlert.STATUS_CHOICES,
        'current_filters': {
            'domain': domain,
            'severity': severity,
            'status': status,
            'search': search,
        },
        'page_title': _('Anomaly Alerts'),
    })


@login_required
@direction_only
def alert_detail(request, pk):
    """Detail view for a single anomaly alert."""
    alert = get_object_or_404(
        AnomalyAlert.objects.select_related('anomaly_type', 'user', 'acknowledged_by', 'resolved_by'),
        pk=pk,
    )

    return render(request, 'anomaly_detection/alert_detail.html', {
        'alert': alert,
        'page_title': f'Alert: {alert.title[:50]}',
    })


@login_required
@direction_only
def alert_acknowledge(request, pk):
    """Acknowledge an anomaly alert."""
    if request.method != 'POST':
        return redirect('frontend:anomaly_detection:alert_detail', pk=pk)

    alert = get_object_or_404(AnomalyAlert, pk=pk)

    if alert.status not in ('new',):
        messages.warning(request, _('This alert has already been processed.'))
        return redirect('frontend:anomaly_detection:alert_detail', pk=pk)

    alert.status = 'acknowledged'
    alert.acknowledged_by = request.user
    alert.acknowledged_at = timezone.now()
    alert.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])

    messages.success(request, _('Alert acknowledged.'))
    return redirect('frontend:anomaly_detection:alert_detail', pk=pk)


@login_required
@direction_only
def alert_resolve(request, pk):
    """Resolve or mark as false positive an anomaly alert."""
    if request.method != 'POST':
        return redirect('frontend:anomaly_detection:alert_detail', pk=pk)

    alert = get_object_or_404(AnomalyAlert, pk=pk)

    if alert.status == 'resolved':
        messages.warning(request, _('This alert has already been resolved.'))
        return redirect('frontend:anomaly_detection:alert_detail', pk=pk)

    resolution = request.POST.get('resolution', 'resolved')
    if resolution not in ('resolved', 'false_positive'):
        resolution = 'resolved'

    notes = request.POST.get('notes', '').strip()

    alert.status = resolution
    alert.resolved_by = request.user
    alert.resolved_at = timezone.now()
    alert.notes = notes
    alert.save(update_fields=['status', 'resolved_by', 'resolved_at', 'notes'])

    label = _('resolved') if resolution == 'resolved' else _('marked as false positive')
    messages.success(request, _('Alert %(label)s.') % {'label': label})
    return redirect('frontend:anomaly_detection:alert_detail', pk=pk)
