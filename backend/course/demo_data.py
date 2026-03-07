"""Demo data generator for course app: CourseAllocations, Uploads."""

import random
from django.core.files.base import ContentFile

from core.models import Session
from .models import CourseAllocation, Upload, UploadVideo


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    session = context.get('session')
    total = 0

    # 1. Course Allocations - assign courses to professors
    allocations = []
    shuffled_courses = list(courses)
    random.shuffle(shuffled_courses)
    courses_per_prof = max(1, len(shuffled_courses) // len(professors))

    for i, prof in enumerate(professors):
        start = i * courses_per_prof
        end = start + courses_per_prof
        prof_courses = shuffled_courses[start:end]
        if not prof_courses:
            prof_courses = [random.choice(shuffled_courses)]

        alloc = CourseAllocation.objects.create(
            lecturer=prof,
            session=session,
        )
        alloc.courses.set(prof_courses)
        allocations.append(alloc)
    total += len(allocations)

    # 2. Course uploads (fake PDF files)
    uploads = []
    upload_titles = [
        'Lecture Notes Week {}', 'Assignment {}', 'Lab Manual',
        'Study Guide', 'Practice Problems', 'Syllabus',
        'Reading Material', 'Tutorial Notes', 'Project Guidelines',
        'Exam Preparation Guide', 'Reference Sheet', 'Formula Sheet',
        'Case Study', 'Workshop Handout', 'Course Outline',
    ]
    for i, title_tpl in enumerate(upload_titles):
        course = random.choice(courses)
        title = title_tpl.format(random.randint(1, 10)) if '{}' in title_tpl else title_tpl
        upload = Upload.objects.create(
            course=course,
            title=f'{title} - {course.code}',
            file=ContentFile(
                b'%PDF-1.4 Demo file content',
                name=f'{course.code.lower()}_{title.lower().replace(" ", "_")}.pdf'
            ),
        )
        uploads.append(upload)
    total += len(uploads)

    # 3. Upload videos
    videos = []
    video_titles = [
        'Introduction to {}', 'Chapter {} Overview', '{} Tutorial',
        'Lab Demonstration', 'Problem Solving Session',
        'Revision Lecture', 'Guest Lecture Recording',
        'Practical Demonstration', 'Q&A Session', 'Exam Review',
    ]
    for i, title_tpl in enumerate(video_titles):
        course = random.choice(courses)
        title = title_tpl.format(course.title[:30]) if '{}' in title_tpl else title_tpl
        video = UploadVideo.objects.create(
            course=course,
            title=f'{title} - {course.code}',
            video=ContentFile(
                b'Demo video content',
                name=f'{course.code.lower()}_video_{i + 1}.mp4'
            ),
            summary=fake.paragraph(nb_sentences=2),
        )
        videos.append(video)
    total += len(videos)

    if stdout and verbosity >= 1:
        stdout.write(f'  [course] Created {total} records '
                     f'(allocations: {len(allocations)}, uploads: {len(uploads)}, videos: {len(videos)})')

    return {
        'allocations': allocations,
        'uploads': uploads,
        'videos': videos,
        '_total': total,
    }
