"""
Super-admin views for cross-tenant comparison and SaaS operator dashboard.
These views query across all tenant schemas (production) or show single-tenant
data (development with SQLite).
"""

import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from accounts.decorators import superuser_required
from accounts.models import User
from core.models import School

logger = logging.getLogger(__name__)


def _is_multi_tenant():
    """Check if running in multi-tenant mode (production with django-tenants)."""
    try:
        from django.conf import settings
        return settings.TENANT_MODEL is not None and 'django_tenants' in settings.INSTALLED_APPS
    except Exception:
        return False


def _collect_tenant_data_multi(school):
    """Collect metrics for a single tenant in multi-tenant mode."""
    from django_tenants.utils import tenant_context

    data = {
        'name': school.name,
        'slug': school.slug,
        'subscription_type': school.subscription_type,
        'subscription_end': school.subscription_end,
        'is_active': school.is_active,
        'max_students': school.max_students,
    }

    try:
        with tenant_context(school):
            data['students'] = User.objects.filter(role='student', is_active=True).count()
            data['professors'] = User.objects.filter(role='professor', is_active=True).count()
            data['parents'] = User.objects.filter(role='parent', is_active=True).count()
            data['total_users'] = User.objects.filter(is_active=True).count()

            # Revenue
            try:
                from payments.models import Invoice
                data['revenue'] = float(
                    Invoice.objects.filter(
                        status='paid'
                    ).aggregate(total=Sum('amount_paid'))['total'] or 0
                )
            except (ImportError, Exception):
                data['revenue'] = 0

            # At-risk students
            try:
                from analytics.models import AtRiskStudent
                data['at_risk'] = AtRiskStudent.objects.filter(is_active=True).count()
                data['at_risk_critical'] = AtRiskStudent.objects.filter(
                    is_active=True, risk_level='critical'
                ).count()
            except (ImportError, Exception):
                data['at_risk'] = 0
                data['at_risk_critical'] = 0

            # Attendance rate (last 30 days)
            try:
                from attendance.models import AttendanceReport
                thirty_days_ago = timezone.now().date() - timedelta(days=30)
                total_records = AttendanceReport.objects.filter(date__gte=thirty_days_ago).count()
                present_records = AttendanceReport.objects.filter(
                    date__gte=thirty_days_ago, status='present'
                ).count()
                data['attendance_rate'] = round((present_records / total_records) * 100, 1) if total_records else 0
            except (ImportError, Exception):
                data['attendance_rate'] = 0

            # Average engagement
            try:
                from analytics.models import StudentEngagement
                avg = StudentEngagement.objects.filter(
                    date__gte=timezone.now().date() - timedelta(days=30)
                ).aggregate(avg=Avg('engagement_score'))['avg']
                data['avg_engagement'] = round(float(avg), 1) if avg else 0
            except (ImportError, Exception):
                data['avg_engagement'] = 0

            # Anomaly count (last 30 days)
            try:
                from anomaly_detection.models import AnomalyAlert
                data['anomalies'] = AnomalyAlert.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).count()
            except (ImportError, Exception):
                data['anomalies'] = 0

    except Exception:
        logger.exception("Failed to collect data for tenant %s", school.name)
        data.update({
            'students': 0, 'professors': 0, 'parents': 0, 'total_users': 0,
            'revenue': 0, 'at_risk': 0, 'at_risk_critical': 0,
            'attendance_rate': 0, 'avg_engagement': 0, 'anomalies': 0,
        })

    return data


def _collect_single_tenant_data():
    """Collect metrics for single-tenant (development) mode."""
    data = {
        'students': User.objects.filter(role='student', is_active=True).count(),
        'professors': User.objects.filter(role='professor', is_active=True).count(),
        'parents': User.objects.filter(role='parent', is_active=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'revenue': 0,
        'at_risk': 0,
        'at_risk_critical': 0,
        'attendance_rate': 0,
        'avg_engagement': 0,
        'anomalies': 0,
    }

    try:
        from payments.models import Invoice
        data['revenue'] = float(
            Invoice.objects.filter(status='paid').aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
        )
    except (ImportError, Exception):
        pass

    try:
        from analytics.models import AtRiskStudent
        data['at_risk'] = AtRiskStudent.objects.filter(is_active=True).count()
        data['at_risk_critical'] = AtRiskStudent.objects.filter(
            is_active=True, risk_level='critical'
        ).count()
    except (ImportError, Exception):
        pass

    try:
        from attendance.models import AttendanceReport
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        total = AttendanceReport.objects.filter(date__gte=thirty_days_ago).count()
        present = AttendanceReport.objects.filter(
            date__gte=thirty_days_ago, status='present'
        ).count()
        data['attendance_rate'] = round((present / total) * 100, 1) if total else 0
    except (ImportError, Exception):
        pass

    try:
        from analytics.models import StudentEngagement
        avg = StudentEngagement.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).aggregate(avg=Avg('engagement_score'))['avg']
        data['avg_engagement'] = round(float(avg), 1) if avg else 0
    except (ImportError, Exception):
        pass

    try:
        from anomaly_detection.models import AnomalyAlert
        data['anomalies'] = AnomalyAlert.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
    except (ImportError, Exception):
        pass

    return data


@login_required
@superuser_required
def tenant_comparison(request):
    """
    Cross-tenant comparison dashboard for the SaaS operator (superusers only).
    In multi-tenant mode: queries each tenant schema and compares metrics.
    In dev mode: shows single-tenant summary data.
    """
    multi_tenant = _is_multi_tenant()
    tenants_data = []
    totals = {
        'students': 0, 'professors': 0, 'parents': 0, 'total_users': 0,
        'revenue': 0, 'at_risk': 0, 'at_risk_critical': 0, 'anomalies': 0,
    }

    if multi_tenant:
        schools = School.objects.exclude(schema_name='public').order_by('name')
        for school in schools:
            data = _collect_tenant_data_multi(school)
            tenants_data.append(data)
            for key in totals:
                totals[key] += data.get(key, 0)
    else:
        # Single-tenant mode — show one "school" row
        school = School.objects.first()
        data = _collect_single_tenant_data()
        data['name'] = school.name if school else 'Development School'
        data['slug'] = school.slug if school else 'dev'
        data['subscription_type'] = getattr(school, 'subscription_type', 'N/A') if school else 'N/A'
        data['subscription_end'] = getattr(school, 'subscription_end', None) if school else None
        data['is_active'] = getattr(school, 'is_active', True) if school else True
        data['max_students'] = getattr(school, 'max_students', 500) if school else 500
        tenants_data.append(data)
        for key in totals:
            totals[key] = data.get(key, 0)

    # Prepare chart data
    chart_names = json.dumps([t['name'] for t in tenants_data])
    chart_students = json.dumps([t['students'] for t in tenants_data])
    chart_revenue = json.dumps([t['revenue'] for t in tenants_data])
    chart_at_risk = json.dumps([t['at_risk'] for t in tenants_data])
    chart_engagement = json.dumps([t.get('avg_engagement', 0) for t in tenants_data])

    context = {
        'tenants': tenants_data,
        'totals': totals,
        'multi_tenant': multi_tenant,
        'tenant_count': len(tenants_data),
        'chart_names': chart_names,
        'chart_students': chart_students,
        'chart_revenue': chart_revenue,
        'chart_at_risk': chart_at_risk,
        'chart_engagement': chart_engagement,
        'title': 'Tenant Comparison Dashboard',
    }

    return render(request, 'monitoring/tenant_comparison.html', context)
