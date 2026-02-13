"""Demo data generator for notices app: Notices, Documents, Responses, and NotifyGroup user links."""

import random
from datetime import timedelta
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import NotifyGroup, Notice, NoticeDocument, NoticeResponse


NOTICE_TITLES = [
    'Important: Exam Schedule Update',
    'Campus Closure Due to Maintenance',
    'New Library Hours Effective Immediately',
    'Tuition Payment Deadline Reminder',
    'Student ID Card Collection Notice',
    'Fire Drill Scheduled for This Week',
    'Holiday Calendar Announcement',
    'Scholarship Application Deadline',
    'New Cafeteria Menu Available',
    'Parking Regulations Update',
    'Health Check-up Schedule',
    'Sports Equipment Inventory',
    'IT System Maintenance Window',
    'Parent-Teacher Meeting Schedule',
    'End of Semester Grading Deadlines',
    'Campus WiFi Upgrade Notice',
    'Lab Safety Training Required',
    'Graduation Ceremony Rehearsal',
    'Summer Course Registration Open',
    'Emergency Contact Information Update',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    groups = list(NotifyGroup.objects.all())
    all_users = [s.student for s in students[:50]] + professors + staff

    # Link users to notify groups
    if groups:
        for group in groups:
            sample_users = random.sample(all_users, min(random.randint(5, 20), len(all_users)))
            group.users.add(*sample_users)

    # 1. Notices (20)
    notices = []
    for i, title in enumerate(NOTICE_TITLES):
        notice = Notice.objects.create(
            title=title,
            content=fake.paragraph(nb_sentences=random.randint(3, 6)),
            uploaded_by=random.choice(professors + staff[:3]),
            priority=random.choice(['low', 'normal', 'normal', 'high', 'urgent']),
            expires_at=timezone.now() + timedelta(days=random.randint(7, 90)),
            is_active=True,
        )
        if groups:
            notice.notify_groups.set(random.sample(groups, min(random.randint(1, 3), len(groups))))
        notices.append(notice)
    total += len(notices)

    # 2. Notice documents (10)
    documents = []
    for i in range(10):
        notice = random.choice(notices)
        doc = NoticeDocument.objects.create(
            notice=notice,
            file=ContentFile(
                b'%PDF-1.4 Notice attachment',
                name=f'notice_attachment_{i + 1}.pdf'
            ),
            filename=f'notice_attachment_{i + 1}.pdf',
            file_size=random.randint(10000, 500000),
        )
        documents.append(doc)
    total += len(documents)

    # 3. Notice responses (100)
    responses = []
    used_responses = set()
    for i in range(100):
        notice = random.choice(notices)
        user = random.choice(all_users)
        key = (notice.pk, user.pk)
        if key in used_responses:
            continue
        used_responses.add(key)

        try:
            resp = NoticeResponse.objects.create(
                notice=notice,
                user=user,
                read_at=timezone.now() - timedelta(hours=random.randint(1, 720)),
                acknowledged=random.choice([True, True, False]),
            )
            if resp.acknowledged:
                resp.acknowledged_at = resp.read_at + timedelta(minutes=random.randint(1, 60))
                resp.save(update_fields=['acknowledged_at'])
            responses.append(resp)
        except Exception:
            pass
    total += len(responses)

    if stdout and verbosity >= 1:
        stdout.write(f'  [notices] Created {total} records '
                     f'(notices: {len(notices)}, docs: {len(documents)}, responses: {len(responses)})')

    return {'notices': notices, '_total': total}
