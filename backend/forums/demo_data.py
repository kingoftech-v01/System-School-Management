"""Demo data generator for forums app: Threads, Posts, Votes, Subscriptions, Reports."""

import random
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType

from .models import ForumCategory, Tag, Thread, Post, Vote, ThreadSubscription, Report


THREAD_TITLES = [
    'How to prepare for final exams?',
    'Best study resources for this semester',
    'Looking for study group partners',
    'Tips for time management',
    'Anyone else struggling with the assignment?',
    'Great lecture today!',
    'Upcoming campus events discussion',
    'Internship opportunities shared',
    'Library hours during exam week',
    'New course material uploaded',
    'Feedback on the new grading system',
    'Student council elections discussion',
    'Career fair preparation tips',
    'Lab equipment availability',
    'Scholarship application deadlines',
    'Research paper writing tips',
    'Group project coordination',
    'Campus food review',
    'Dormitory maintenance issues',
    'Club recruitment announcements',
    'Workshop registration open',
    'Guest lecture announcement',
    'Sports team tryouts',
    'Mental health resources',
    'Part-time job recommendations',
    'Summer program applications',
    'Transfer credit questions',
    'Parking pass information',
    'WiFi issues on campus',
    'Textbook exchange thread',
    'Study abroad experiences',
    'Graduation requirements checklist',
    'Petition for extended library hours',
    'Lost and found',
    'Campus safety concerns',
    'Holiday break schedule',
    'New semester course recommendations',
    'Alumni networking event',
    'Environmental sustainability initiatives',
    'Technology requirements for courses',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    categories = list(ForumCategory.objects.filter(is_active=True))
    tags = list(Tag.objects.all())
    all_users = [s.student for s in students[:50]] + professors + staff[:3]

    if not categories:
        if stdout:
            stdout.write('  [forums] No forum categories found, skipping')
        return {'_total': 0}

    # 1. Threads (40)
    threads = []
    for i, title in enumerate(THREAD_TITLES[:40]):
        author = random.choice(all_users)
        category = random.choice(categories)
        status = random.choices(
            ['published', 'published', 'published', 'archived', 'locked'],
            weights=[0.7, 0.1, 0.05, 0.1, 0.05],
            k=1
        )[0]

        thread = Thread.objects.create(
            category=category,
            title=title,
            slug=slugify(f'{title}-{i}')[:220],
            author=author,
            content=fake.paragraph(nb_sentences=random.randint(2, 6)),
            status=status,
            is_published=status == 'published',
            is_pinned=random.random() < 0.1,
            is_locked=status == 'locked',
            is_featured=random.random() < 0.05,
            view_count=random.randint(5, 500),
            reply_count=0,  # Will be updated
        )
        # Add tags
        if tags:
            thread.tags.set(random.sample(tags, min(random.randint(1, 3), len(tags))))
        threads.append(thread)
    total += len(threads)

    # 2. Posts (150)
    posts = []
    for i in range(150):
        thread = random.choice(threads)
        author = random.choice(all_users)
        parent = random.choice(posts[-20:]) if posts and random.random() < 0.3 else None
        # Only set parent if it's in the same thread
        if parent and parent.thread != thread:
            parent = None

        post = Post.objects.create(
            thread=thread,
            author=author,
            parent=parent,
            content=fake.paragraph(nb_sentences=random.randint(1, 4)),
            is_edited=random.random() < 0.15,
            upvotes=0,
            downvotes=0,
        )
        posts.append(post)
    total += len(posts)

    # Update thread reply counts
    for thread in threads:
        thread.reply_count = Post.objects.filter(thread=thread).count()
        thread.save(update_fields=['reply_count'])

    # 3. Votes (200)
    votes = []
    used_votes = set()
    for i in range(200):
        post = random.choice(posts)
        user = random.choice(all_users)
        key = (post.pk, user.pk)
        if key in used_votes:
            continue
        used_votes.add(key)

        vote_type = random.choice([1, 1, 1, -1])  # More upvotes than downvotes
        try:
            v = Vote.objects.create(
                post=post,
                user=user,
                vote_type=vote_type,
            )
            votes.append(v)
            # Update post vote counts
            if vote_type == 1:
                post.upvotes += 1
            else:
                post.downvotes += 1
            post.save(update_fields=['upvotes', 'downvotes'])
        except Exception:
            pass
    total += len(votes)

    # 4. Thread subscriptions (50)
    subscriptions = []
    used_subs = set()
    for i in range(50):
        thread = random.choice(threads)
        user = random.choice(all_users)
        key = (thread.pk, user.pk)
        if key in used_subs:
            continue
        used_subs.add(key)

        try:
            sub = ThreadSubscription.objects.create(
                thread=thread,
                user=user,
                email_on_reply=random.choice([True, True, False]),
            )
            subscriptions.append(sub)
        except Exception:
            pass
    total += len(subscriptions)

    # 5. Reports (5)
    reports = []
    post_ct = ContentType.objects.get_for_model(Post)
    for i in range(5):
        post = random.choice(posts)
        reporter = random.choice(all_users)
        r = Report.objects.create(
            content_type=post_ct,
            object_id=post.pk,
            reported_by=reporter,
            report_type=random.choice(['spam', 'offensive', 'harassment', 'misinformation', 'other']),
            description=fake.paragraph(nb_sentences=2),
            status=random.choice(['pending', 'reviewing', 'resolved', 'dismissed']),
        )
        reports.append(r)
    total += len(reports)

    if stdout and verbosity >= 1:
        stdout.write(f'  [forums] Created {total} records '
                     f'(threads: {len(threads)}, posts: {len(posts)}, '
                     f'votes: {len(votes)}, subscriptions: {len(subscriptions)})')

    return {'threads': threads, 'posts': posts, '_total': total}
