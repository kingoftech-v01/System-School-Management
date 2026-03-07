"""
Computed insights engine for the analytics app.
Generates actionable insights from analytics data for direction/admin users.
"""

import logging
from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_all_insights():
    """Run all insight computations and create Insight records."""
    from .models import Insight

    # Deactivate old insights before generating new ones
    Insight.objects.filter(is_active=True).update(is_active=False)

    total = 0
    total += _check_attendance_anomalies()
    total += _check_engagement_drops()
    total += _check_payment_shortfalls()
    total += _check_risk_clusters()
    total += _check_grade_trends()

    logger.info("Generated %d insights", total)
    return total


def _check_attendance_anomalies():
    """Flag courses with absence rates significantly above average."""
    from .models import Insight

    try:
        from dailystat.models import DailyAttendanceStat
        fourteen_days_ago = timezone.now().date() - timedelta(days=14)

        stats = DailyAttendanceStat.objects.filter(day__gte=fourteen_days_ago)
        if not stats.exists():
            return 0

        overall_avg = stats.aggregate(
            avg_absent=Avg('total_absent'),
            avg_present=Avg('total_present'),
        )
        avg_absent = overall_avg['avg_absent'] or 0
        avg_present = overall_avg['avg_present'] or 0

        if avg_present == 0:
            return 0

        absence_rate = avg_absent / (avg_present + avg_absent) * 100

        created = 0
        if absence_rate > 20:
            severity = 'critical' if absence_rate > 40 else 'warning'
            Insight.objects.create(
                insight_type='attendance_anomaly',
                title=f'High absence rate: {absence_rate:.1f}% over last 14 days',
                description=(
                    f'The overall absence rate is {absence_rate:.1f}%, '
                    f'which is above the 20% threshold. '
                    f'Average {avg_absent:.0f} absences per day out of '
                    f'{avg_present + avg_absent:.0f} total students.'
                ),
                severity=severity,
                data={
                    'absence_rate': round(absence_rate, 1),
                    'avg_absent': round(avg_absent, 1),
                    'avg_present': round(avg_present, 1),
                    'period_days': 14,
                },
            )
            created = 1
        return created
    except Exception:
        logger.exception("Error checking attendance anomalies")
        return 0


def _check_engagement_drops():
    """Compare this week's avg engagement vs last month's."""
    from .models import Insight, StudentEngagement

    try:
        now = timezone.now().date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        this_week = StudentEngagement.objects.filter(
            date__gte=week_ago
        ).aggregate(avg=Avg('engagement_score'))['avg']

        last_month = StudentEngagement.objects.filter(
            date__gte=month_ago, date__lt=week_ago
        ).aggregate(avg=Avg('engagement_score'))['avg']

        if this_week is None or last_month is None or last_month == 0:
            return 0

        drop_pct = ((last_month - this_week) / last_month) * 100

        created = 0
        if drop_pct > 20:
            severity = 'critical' if drop_pct > 40 else 'warning'
            Insight.objects.create(
                insight_type='engagement_drop',
                title=f'Engagement dropped {drop_pct:.0f}% this week',
                description=(
                    f'Average engagement this week ({this_week:.1f}) is {drop_pct:.0f}% lower '
                    f'than the previous month average ({last_month:.1f}). '
                    f'This may indicate students disengaging from coursework.'
                ),
                severity=severity,
                data={
                    'this_week_avg': round(float(this_week), 1),
                    'last_month_avg': round(float(last_month), 1),
                    'drop_percentage': round(drop_pct, 1),
                },
            )
            created = 1
        return created
    except Exception:
        logger.exception("Error checking engagement drops")
        return 0


def _check_payment_shortfalls():
    """Compare collected payments vs expected."""
    from .models import Insight

    try:
        from payments.models import Invoice
        from core.models import Session

        current_session = Session.objects.filter(is_current_session=True).first()
        if not current_session:
            return 0

        totals = Invoice.objects.filter(
            session=current_session
        ).aggregate(
            total_due=Sum('total_amount'),
            total_paid=Sum('amount_paid'),
        )

        total_due = totals['total_due'] or 0
        total_paid = totals['total_paid'] or 0

        if total_due == 0:
            return 0

        collection_rate = (total_paid / total_due) * 100

        created = 0
        if collection_rate < 80:
            severity = 'critical' if collection_rate < 60 else 'warning'
            shortfall = total_due - total_paid
            Insight.objects.create(
                insight_type='payment_shortfall',
                title=f'Payment collection at {collection_rate:.0f}% ({shortfall:,.0f} outstanding)',
                description=(
                    f'Only {collection_rate:.0f}% of expected payments have been collected '
                    f'for the current session. Total due: {total_due:,.0f}, '
                    f'collected: {total_paid:,.0f}, outstanding: {shortfall:,.0f}.'
                ),
                severity=severity,
                data={
                    'collection_rate': round(collection_rate, 1),
                    'total_due': float(total_due),
                    'total_paid': float(total_paid),
                    'shortfall': float(shortfall),
                },
            )
            created = 1
        return created
    except Exception:
        logger.exception("Error checking payment shortfalls")
        return 0


def _check_risk_clusters():
    """Flag courses with multiple critical at-risk students."""
    from .models import Insight, AtRiskStudent

    try:
        course_risks = (
            AtRiskStudent.objects
            .filter(is_active=True, risk_level__in=['high', 'critical'])
            .values('course__name', 'course_id')
            .annotate(count=Count('id'))
            .filter(count__gte=3)
            .order_by('-count')
        )

        created = 0
        for cluster in course_risks:
            severity = 'critical' if cluster['count'] >= 5 else 'warning'
            Insight.objects.create(
                insight_type='risk_cluster',
                title=f'{cluster["count"]} at-risk students in {cluster["course__name"]}',
                description=(
                    f'{cluster["course__name"]} has {cluster["count"]} students flagged '
                    f'as high or critical risk. This concentration suggests a systemic '
                    f'issue with the course that may need instructor intervention.'
                ),
                severity=severity,
                data={
                    'course_name': cluster['course__name'],
                    'course_id': cluster['course_id'],
                    'at_risk_count': cluster['count'],
                },
            )
            created += 1
        return created
    except Exception:
        logger.exception("Error checking risk clusters")
        return 0


def _check_grade_trends():
    """Compare recent grade averages vs historical."""
    from .models import Insight

    try:
        from result.models import TakenCourse
        from core.models import Semester

        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return 0

        current_avg = TakenCourse.objects.filter(
            course__semester=current_semester,
            total__isnull=False
        ).aggregate(avg=Avg('total'))['avg']

        previous_avg = TakenCourse.objects.exclude(
            course__semester=current_semester
        ).filter(total__isnull=False).aggregate(avg=Avg('total'))['avg']

        if current_avg is None or previous_avg is None or previous_avg == 0:
            return 0

        change_pct = ((current_avg - previous_avg) / previous_avg) * 100

        created = 0
        if abs(change_pct) > 10:
            if change_pct < -10:
                Insight.objects.create(
                    insight_type='grade_trend',
                    title=f'Grade average dropped {abs(change_pct):.0f}% this semester',
                    description=(
                        f'The current semester average ({current_avg:.1f}) is '
                        f'{abs(change_pct):.0f}% lower than historical average '
                        f'({previous_avg:.1f}). This may indicate increased difficulty '
                        f'or student struggles.'
                    ),
                    severity='warning',
                    data={
                        'current_avg': round(float(current_avg), 1),
                        'previous_avg': round(float(previous_avg), 1),
                        'change_pct': round(change_pct, 1),
                    },
                )
                created = 1
            elif change_pct > 15:
                Insight.objects.create(
                    insight_type='grade_trend',
                    title=f'Grade average improved {change_pct:.0f}% this semester',
                    description=(
                        f'The current semester average ({current_avg:.1f}) is '
                        f'{change_pct:.0f}% higher than historical average '
                        f'({previous_avg:.1f}). Teaching improvements are showing results.'
                    ),
                    severity='info',
                    data={
                        'current_avg': round(float(current_avg), 1),
                        'previous_avg': round(float(previous_avg), 1),
                        'change_pct': round(change_pct, 1),
                    },
                )
                created = 1
        return created
    except Exception:
        logger.exception("Error checking grade trends")
        return 0
