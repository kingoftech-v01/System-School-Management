"""Demo data generator for articles app: Articles, Comments, Likes, Newsletters."""

import random
from django.utils import timezone

from .models import Category, Article, Comment, Like, Newsletter


ARTICLE_TITLES = [
    'New Academic Year Kicks Off with Record Enrollment',
    'Science Fair Winners Announced',
    'Campus Library Undergoes Major Renovation',
    'Student Research Team Wins National Competition',
    'Annual Sports Day Results and Highlights',
    'New Scholarship Programs Available for 2026',
    'Faculty Member Publishes Groundbreaking Research',
    'Technology Lab Receives Major Equipment Upgrade',
    'Community Service Week Sees Record Participation',
    'Alumni Association Launches Mentorship Program',
    'New Student Wellness Center Opens Its Doors',
    'Mathematics Olympiad Team Prepares for Finals',
    'Cultural Festival Celebrates Diversity',
    'Career Fair Brings 50+ Employers to Campus',
    'Environmental Sustainability Initiative Launched',
    'Debate Team Advances to Regional Championships',
    'New Online Learning Platform Introduced',
    'Music Department Concert Season Announced',
    'International Exchange Program Expands',
    'Student Government Election Results',
    'Campus Safety Improvements Completed',
    'Art Exhibition Features Student Work',
    'Engineering Students Build Solar-Powered Car',
    'Psychology Department Opens Counseling Clinic',
    'Spring Graduation Ceremony Details Released',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    categories = list(Category.objects.filter(is_active=True))
    all_users = [s.student for s in students[:30]] + professors + staff[:3]
    authors = professors + staff[:3]

    # 1. Articles (25)
    articles = []
    for i, title in enumerate(ARTICLE_TITLES):
        status = random.choices(
            ['published', 'draft', 'pending', 'archived'],
            weights=[0.7, 0.1, 0.1, 0.1],
            k=1
        )[0]
        article = Article.objects.create(
            title=title,
            author=random.choice(authors),
            summary=fake.paragraph(nb_sentences=2)[:500],
            content='\n\n'.join(fake.paragraphs(nb=random.randint(3, 6))),
            status=status,
            is_featured=random.random() < 0.15,
            is_pinned=random.random() < 0.08,
            views_count=random.randint(10, 1000),
            likes_count=0,
            comments_count=0,
            published_at=timezone.now() if status == 'published' else None,
            meta_description=fake.sentence()[:160],
        )
        if categories:
            article.categories.set(random.sample(categories, min(random.randint(1, 3), len(categories))))
        articles.append(article)
    total += len(articles)

    # 2. Comments (80)
    published_articles = [a for a in articles if a.status == 'published']
    comments = []
    for i in range(80):
        article = random.choice(published_articles) if published_articles else random.choice(articles)
        same_article_comments = [c for c in comments if c.article == article]
        parent = random.choice(same_article_comments) if same_article_comments and random.random() < 0.2 else None

        comment = Comment.objects.create(
            article=article,
            author=random.choice(all_users),
            parent=parent,
            content=fake.paragraph(nb_sentences=random.randint(1, 3))[:1000],
            status=random.choices(
                ['approved', 'pending', 'rejected', 'spam'],
                weights=[0.8, 0.1, 0.05, 0.05],
                k=1
            )[0],
        )
        comments.append(comment)
    total += len(comments)

    # Update comment counts
    for article in articles:
        article.comments_count = Comment.objects.filter(article=article, status='approved').count()
        article.save(update_fields=['comments_count'])

    # 3. Likes (100)
    likes = []
    used_likes = set()
    for i in range(100):
        article = random.choice(published_articles) if published_articles else random.choice(articles)
        user = random.choice(all_users)
        key = (article.pk, user.pk)
        if key in used_likes:
            continue
        used_likes.add(key)

        try:
            like = Like.objects.create(article=article, user=user)
            likes.append(like)
        except Exception:
            pass
    total += len(likes)

    # Update like counts
    for article in articles:
        article.likes_count = Like.objects.filter(article=article).count()
        article.save(update_fields=['likes_count'])

    # 4. Newsletters (20)
    newsletters = []
    for i, user_obj in enumerate(all_users[:20]):
        try:
            nl = Newsletter.objects.create(
                email=user_obj.email,
                user=user_obj,
                is_subscribed=True,
                is_verified=random.choice([True, True, False]),
                frequency=random.choice(['daily', 'weekly', 'monthly']),
            )
            newsletters.append(nl)
        except Exception:
            pass  # Unique email
    total += len(newsletters)

    if stdout and verbosity >= 1:
        stdout.write(f'  [articles] Created {total} records '
                     f'(articles: {len(articles)}, comments: {len(comments)}, '
                     f'likes: {len(likes)}, newsletters: {len(newsletters)})')

    return {'articles': articles, '_total': total}
