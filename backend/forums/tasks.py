"""
Celery tasks for forums app.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from .models import Thread, Post, Report, ThreadSubscription


@shared_task(name='forums.send_new_thread_notifications')
def send_new_thread_notifications(thread_id):
    """Send notifications when a new thread is created."""
    try:
        thread = Thread.objects.get(pk=thread_id)

        # Get category subscribers or all forum members
        # This is a simplified version - you'd want to implement category subscriptions
        subscribers = thread.category.subscribers.all() if hasattr(thread.category, 'subscribers') else []

        for subscriber in subscribers:
            if subscriber != thread.author:
                send_mail(
                    subject=f'New Thread: {thread.title}',
                    message=f'{thread.author.get_full_name} created a new thread in {thread.category.name}:\n\n{thread.title}\n\n{thread.content[:200]}...',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=True,
                )

        return f'Sent notifications for thread {thread_id}'
    except Thread.DoesNotExist:
        return f'Thread {thread_id} not found'


@shared_task(name='forums.send_new_post_notifications')
def send_new_post_notifications(post_id):
    """Send notifications to thread subscribers when a new post is added."""
    try:
        post = Post.objects.get(pk=post_id)
        thread = post.thread

        # Get all subscribers to this thread
        subscriptions = ThreadSubscription.objects.filter(
            thread=thread,
            email_on_reply=True
        ).exclude(user=post.author)

        for subscription in subscriptions:
            send_mail(
                subject=f'New Reply: {thread.title}',
                message=f'{post.author.get_full_name} replied to "{thread.title}":\n\n{post.content[:200]}...',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=True,
            )

        return f'Sent notifications for post {post_id}'
    except Post.DoesNotExist:
        return f'Post {post_id} not found'


@shared_task(name='forums.process_flagged_content')
def process_flagged_content():
    """Process flagged content and notify moderators."""
    # Get unresolved reports
    pending_reports = Report.objects.filter(status='pending')

    if not pending_reports.exists():
        return 'No pending reports to process'

    # Get moderators (users with can_moderate_threads permission)
    from accounts.models import User
    moderators = User.objects.filter(
        Q(is_staff=True) | Q(groups__permissions__codename='can_moderate_threads')
    ).distinct()

    report_summary = []
    for report in pending_reports[:10]:  # Process first 10
        report_summary.append(f'- {report.get_reason_display()}: {report.content_type}')

    # Send summary to moderators
    for moderator in moderators:
        send_mail(
            subject=f'Forum Moderation Required: {pending_reports.count()} Reports',
            message=f'There are {pending_reports.count()} pending reports requiring moderation:\n\n' + '\n'.join(report_summary),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[moderator.email],
            fail_silently=True,
        )

    return f'Notified {moderators.count()} moderators about {pending_reports.count()} reports'


@shared_task(name='forums.cleanup_old_threads')
def cleanup_old_threads():
    """Archive or delete old inactive threads."""
    # Archive threads with no activity for 365 days
    cutoff_date = timezone.now() - timedelta(days=365)

    old_threads = Thread.objects.filter(
        updated_at__lt=cutoff_date,
        is_pinned=False,
        is_locked=False
    )

    archived_count = old_threads.count()

    # Mark as archived (you could add an is_archived field)
    # For now, we'll just count them
    # old_threads.update(is_archived=True)

    return f'Found {archived_count} threads older than 1 year'


@shared_task(name='forums.update_thread_view_counts')
def update_thread_view_counts():
    """Batch update thread view counts (if using cache)."""
    from django.core.cache import cache

    # This would be used if you're caching view counts
    # and want to batch update them to the database

    updated_count = 0
    threads = Thread.objects.all()

    for thread in threads:
        cache_key = f'thread_views_{thread.id}'
        cached_views = cache.get(cache_key)

        if cached_views is not None and cached_views != thread.view_count:
            thread.view_count = cached_views
            thread.save(update_fields=['view_count'])
            updated_count += 1

    return f'Updated {updated_count} thread view counts'
