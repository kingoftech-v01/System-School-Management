"""Demo data generator for quiz app: Quizzes, Questions, Choices, Sittings, Progress."""

import json
import random
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify

from .models import Quiz, MCQuestion, TrueFalseQuestion, EssayQuestion, Choice, Sitting, Progress


QUIZ_TEMPLATES = [
    ('Midterm Exam', 'exam'), ('Final Exam', 'exam'),
    ('Quiz 1', 'assignment'), ('Quiz 2', 'assignment'), ('Quiz 3', 'assignment'),
    ('Practice Test', 'practice'), ('Pop Quiz', 'assignment'),
    ('Lab Quiz', 'assignment'), ('Review Quiz', 'practice'),
    ('Chapter Test', 'exam'), ('Weekly Assessment', 'assignment'),
    ('Diagnostic Test', 'practice'), ('Unit Test', 'exam'),
    ('Homework Quiz', 'assignment'), ('Pre-exam Practice', 'practice'),
    ('Section Review', 'practice'), ('Comprehension Check', 'assignment'),
    ('Skill Assessment', 'exam'), ('Progress Check', 'practice'),
    ('Bonus Quiz', 'assignment'),
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    courses = context.get('courses', [])
    total = 0

    # 1. Quizzes (20)
    quizzes = []
    for i, (title_tpl, category) in enumerate(QUIZ_TEMPLATES):
        course = courses[i % len(courses)]
        title = f'{title_tpl} - {course.code}'
        quiz = Quiz.objects.create(
            course=course,
            title=title[:60],
            slug=slugify(f'{title}-demo-{i}-{fake.random_int(min=1000, max=9999)}')[:50],
            description=fake.paragraph(nb_sentences=2),
            category=category,
            random_order=random.choice([True, False]),
            answers_at_end=True,
            exam_paper=category == 'exam',
            single_attempt=category == 'exam',
            pass_mark=random.choice([40, 50, 60, 70]),
            draft=False,
            time_limit=random.choice([30, 45, 60, 90, None]),
        )
        quizzes.append(quiz)
    total += len(quizzes)

    # 2. Questions - mix of MC, TF, Essay
    mc_questions = []
    tf_questions = []
    essay_questions = []

    for quiz in quizzes:
        # 3 MC questions per quiz
        for j in range(3):
            q = MCQuestion.objects.create(
                content=fake.sentence(nb_words=12) + '?',
                explanation=fake.sentence(),
                choice_order='random',
            )
            q.quiz.add(quiz)
            mc_questions.append(q)

            # 4 choices per MC question
            correct_idx = random.randint(0, 3)
            for k in range(4):
                Choice.objects.create(
                    question=q,
                    choice_text=fake.sentence(nb_words=random.randint(3, 8)),
                    correct=(k == correct_idx),
                )

        # 1 TF question per quiz
        tf = TrueFalseQuestion.objects.create(
            content=fake.sentence(nb_words=10) + '?',
            explanation=fake.sentence(),
            correct_answer=random.choice([True, False]),
        )
        tf.quiz.add(quiz)
        tf_questions.append(tf)

        # 1 Essay question per quiz
        eq = EssayQuestion.objects.create(
            content=f'Explain the concept of {fake.word()} in {quiz.course.title}. '
                    f'Provide examples and discuss its significance.',
            explanation='Answers will vary. Look for clear explanation and relevant examples.',
        )
        eq.quiz.add(quiz)
        essay_questions.append(eq)

    all_questions = mc_questions + tf_questions + essay_questions
    total += len(all_questions)
    total += len(mc_questions) * 4  # choices

    # 3. Sittings (200)
    sittings = []
    for i in range(200):
        student_acct = random.choice(students)
        user = student_acct.student
        quiz = random.choice(quizzes)
        questions = list(quiz.question_set.all())
        q_ids = [str(q.pk) for q in questions]
        q_order = ','.join(q_ids)
        score = random.randint(0, len(questions))
        is_complete = random.choice([True, True, True, False])
        incorrect = random.sample(q_ids, random.randint(0, min(3, len(q_ids))))

        sitting = Sitting.objects.create(
            user=user,
            quiz=quiz,
            course=quiz.course,
            question_order=q_order,
            question_list=q_order if not is_complete else '',
            incorrect_questions=','.join(incorrect),
            current_score=score,
            complete=is_complete,
            user_answers=json.dumps({}),
            end=timezone.now() if is_complete else None,
            time_spent=timedelta(minutes=random.randint(5, 90)) if is_complete else None,
        )
        sittings.append(sitting)
    total += len(sittings)

    # 4. Progress (per student user)
    progress_records = []
    for student_acct in students[:100]:
        user = student_acct.student
        scores = [str(random.randint(30, 100)) for _ in range(random.randint(1, 5))]
        try:
            p = Progress.objects.create(
                user=user,
                score=','.join(scores),
            )
            progress_records.append(p)
        except Exception:
            pass  # OneToOne
    total += len(progress_records)

    if stdout and verbosity >= 1:
        stdout.write(f'  [quiz] Created {total} records '
                     f'(quizzes: {len(quizzes)}, questions: {len(all_questions)}, '
                     f'sittings: {len(sittings)}, progress: {len(progress_records)})')

    return {'quizzes': quizzes, '_total': total}
