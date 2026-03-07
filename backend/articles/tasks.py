"""
Celery tasks for articles app.
Based on edX platform patterns for bulk operations and notifications.
"""

from celery import shared_task
from django.core.mail import send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_article_notification(self, article_id):
    """
    Send email notifications when a new article is published.
    Based on edX discussion notification pattern.
    """
    from .models import Article, Newsletter

    try:
        article = Article.objects.get(id=article_id, status='published')
        
        # Get all verified and subscribed emails
        subscribers = Newsletter.objects.filter(
            is_subscribed=True,
            is_verified=True
        ).values_list('email', flat=True)

        if not subscribers:
            logger.info(f"No subscribers for article {article.id}")
            return

        # Prepare email content
        subject = f"New Article: {article.title}"
        from_email = 'noreply@school.com'
        
        messages = []
        for email in subscribers:
            text_content = f"""
            New Article Published
            
            {article.title}
            
            {article.excerpt or article.content[:200]}
            
            Read more at: [Article Link]
            
            Unsubscribe: [Unsubscribe Link]
            """
            
            html_content = render_to_string('articles/email/new_article.html', {
                'article': article,
                'email': email
            })
            
            msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
            msg.attach_alternative(html_content, "text/html")
            messages.append(msg)

        # Send in batches to avoid overwhelming SMTP
        batch_size = 100
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            for msg in batch:
                msg.send(fail_silently=False)

        logger.info(f"Sent {len(messages)} notifications for article {article.id}")
        return f"Sent {len(messages)} notifications"

    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error sending article notifications: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry after 5 minutes


@shared_task
def send_weekly_newsletter():
    """
    Send weekly newsletter with latest articles.
    Based on edX bulk email pattern.
    """
    from .models import Article, Newsletter, NewsletterSent

    # Get articles published in the last 7 days
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    articles = Article.objects.filter(
        status='published',
        published_at__gte=one_week_ago
    ).order_by('-published_at')[:10]

    if not articles.exists():
        logger.info("No new articles for weekly newsletter")
        return "No new articles"

    # Get weekly subscribers
    subscribers = Newsletter.objects.filter(
        is_subscribed=True,
        is_verified=True,
        frequency='weekly'
    )

    if not subscribers.exists():
        logger.info("No weekly subscribers")
        return "No subscribers"

    subject = f"Weekly Newsletter - {timezone.now().strftime('%B %d, %Y')}"
    from_email = 'newsletter@school.com'

    messages = []
    for subscriber in subscribers:
        context = {
            'articles': articles,
            'subscriber': subscriber,
            'unsubscribe_url': f'/articles/newsletter/unsubscribe/{subscriber.email}/'
        }
        
        text_content = render_to_string('articles/email/weekly_newsletter.txt', context)
        html_content = render_to_string('articles/email/weekly_newsletter.html', context)
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [subscriber.email])
        msg.attach_alternative(html_content, "text/html")
        messages.append(msg)

    # Send emails
    sent_count = 0
    for msg in messages:
        try:
            msg.send(fail_silently=False)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send newsletter to {msg.to[0]}: {e}")

    # Record newsletter sent
    newsletter_sent = NewsletterSent.objects.create(
        subject=subject,
        recipients_count=sent_count
    )
    newsletter_sent.articles.set(articles)

    logger.info(f"Sent weekly newsletter to {sent_count} subscribers")
    return f"Sent to {sent_count} subscribers"


@shared_task
def cleanup_draft_articles():
    """
    Delete old draft articles that haven't been published.
    Based on edX content cleanup pattern.
    """
    from .models import Article

    # Delete drafts older than 90 days
    cutoff_date = timezone.now() - timezone.timedelta(days=90)
    old_drafts = Article.objects.filter(
        status='draft',
        created_at__lt=cutoff_date
    )

    count = old_drafts.count()
    old_drafts.delete()

    logger.info(f"Deleted {count} old draft articles")
    return f"Deleted {count} drafts"


@shared_task
def moderate_pending_comments():
    """
    Auto-approve comments from verified users, flag suspicious ones.
    Based on edX discussion moderation pattern.
    """
    from .models import Comment

    # Auto-approve comments from users with good history
    pending_comments = Comment.objects.filter(status='pending')

    auto_approved = 0
    flagged = 0

    for comment in pending_comments:
        # Auto-approve if user has 5+ approved comments
        previous_approved = Comment.objects.filter(
            author=comment.author,
            status='approved'
        ).count()

        if previous_approved >= 5:
            comment.status = 'approved'
            comment.save()
            auto_approved += 1
        # Flag if comment contains spam keywords
        elif any(keyword in comment.content.lower() for keyword in ['viagra', 'casino', 'lottery']):
            comment.status = 'spam'
            comment.save()
            flagged += 1

    logger.info(f"Auto-approved {auto_approved} comments, flagged {flagged} as spam")
    return f"Approved: {auto_approved}, Flagged: {flagged}"


@shared_task
def update_article_statistics():
    """
    Update article view counts and other statistics.
    Based on edX analytics pattern.
    """
    from .models import Article, Like, Comment

    articles = Article.objects.filter(status='published')

    updated_count = 0
    for article in articles:
        # Update likes and comments count
        article.likes_count = Like.objects.filter(article=article).count()
        article.comments_count = Comment.objects.filter(
            article=article,
            status='approved'
        ).count()
        article.save(update_fields=['likes_count', 'comments_count'])
        updated_count += 1

    logger.info(f"Updated statistics for {updated_count} articles")
    return f"Updated {updated_count} articles"
