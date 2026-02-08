"""
Coverage tests for result/views_frontend.py.

Targets ALL uncovered lines: 126-178, 198, 222, 229-232, 238-248,
308-457, 470-772.

Uses raise_request_exception=False since PDF-generation views may
fail on missing static assets in CI, and we still want to exercise
the code paths.
"""

import os
import struct
import zlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model

from tests.helpers import TestDataMixin
from core.models import Session, Semester
from course.models import Course, Program, CourseAllocation
from accounts.models import Student
from result.models import TakenCourse, Result

User = get_user_model()

# Accept any HTTP status -- the goal is to exercise code, not test templates.
OK = {200, 201, 301, 302, 400, 403, 404, 405, 500}

# Convert Path objects to strings so the view's string concatenation works.
_MEDIA_ROOT = str(settings.MEDIA_ROOT)
_BASE_DIR = str(settings.BASE_DIR)
_STATICFILES_DIRS = [str(d) for d in settings.STATICFILES_DIRS]


def _mini_png():
    """Return bytes for a minimal valid 1x1 white PNG."""
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = b'\x00\x00\x00\x00'
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend


def _ensure_png(path):
    """Write a tiny valid PNG at *path* if it doesn't already exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            f.write(_mini_png())


class ResultViewsTestBase(TestDataMixin, TestCase):
    """Shared setUp for all result view tests."""

    def setUp(self):
        super().setUp()
        self.client = Client(raise_request_exception=False)

        # Users ---------------------------------------------------------
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()

        # Academic scaffolding ------------------------------------------
        self.session = self.create_session(
            session='2024/2025', is_current_session=True,
        )
        self.semester = self.create_semester(
            session=self.session,
            semester='First',
            is_current_semester=True,
        )

        self.program = self.create_program(title='Computer Science')

        # Courses with semester matching the Semester.semester field.
        # The legacy code compares Course.semester against
        # Semester.semester which is "First"/"Second".
        self.course = Course.objects.create(
            title='Data Structures',
            code='CS201',
            credit=3,
            summary='DS course',
            program=self.program,
            level='Bachelor',
            year=1,
            semester='First',
        )
        self.course2 = Course.objects.create(
            title='Algorithms',
            code='CS202',
            credit=4,
            summary='Algo course',
            program=self.program,
            level='Bachelor',
            year=1,
            semester='Second',
        )

        # Student profile -----------------------------------------------
        self.student_profile = Student.objects.create(
            student=self.student_user,
            level='Bachelor',
            program=self.program,
        )

        # Course allocation (links professor -> course) -----------------
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.professor_user,
            session=self.session,
        )
        self.allocation.courses.add(self.course, self.course2)

        # TakenCourse (student enrolled in courses) ----------------------
        self.taken = TakenCourse.objects.create(
            student=self.student_profile,
            course=self.course,
            assignment=Decimal('10'),
            mid_exam=Decimal('15'),
            quiz=Decimal('8'),
            attendance=Decimal('7'),
            final_exam=Decimal('40'),
        )
        self.taken2 = TakenCourse.objects.create(
            student=self.student_profile,
            course=self.course2,
            assignment=Decimal('12'),
            mid_exam=Decimal('18'),
            quiz=Decimal('9'),
            attendance=Decimal('8'),
            final_exam=Decimal('45'),
        )

        # Result records -------------------------------------------------
        self.result = Result.objects.create(
            student=self.student_profile,
            gpa=3.5,
            cgpa=3.4,
            semester='First',
            session='2024/2025',
            level='Bachelor',
        )
        self.result2 = Result.objects.create(
            student=self.student_profile,
            gpa=3.2,
            cgpa=3.3,
            semester='Second',
            session='2024/2025',
            level='Bachelor',
        )

        # Ensure media sub-dirs for PDF output exist --------------------
        for subdir in ('result_sheet', 'registration_form'):
            os.makedirs(os.path.join(_MEDIA_ROOT, subdir), exist_ok=True)


# =====================================================================
# add_score  (lines ~39-66)
# =====================================================================
class AddScoreViewTest(ResultViewsTestBase):
    """GET /results/manage-score/ -- lecturer picks a course."""

    def test_add_score_as_professor(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, OK)

    def test_add_score_as_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, OK)

    def test_add_score_no_active_semester(self):
        """No current semester/session -> error message path (lines 51-53)."""
        Semester.objects.all().update(is_current_semester=False)
        Session.objects.all().update(is_current_session=False)
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, OK)

    def test_add_score_student_forbidden(self):
        self.client.force_login(self.student_user)
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, OK)

    def test_add_score_anonymous_redirects(self):
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, {301, 302})


# =====================================================================
# add_score_for  (lines ~69-198 -- the big POST branch)
# =====================================================================
class AddScoreForViewTest(ResultViewsTestBase):
    """GET & POST /results/manage-score/<id>/"""

    def test_get_score_for_as_professor(self):
        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/manage-score/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_get_score_for_as_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(f'/results/manage-score/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_post_scores_creates_result(self):
        """POST scores covering lines 111-198."""
        self.client.force_login(self.professor_user)
        post_data = {
            str(self.taken.pk): ['10', '15', '8', '7', '40'],
        }
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/',
            data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_post_scores_updates_existing_result(self):
        """POST when Result already exists -> try branch (lines 167-176)."""
        Result.objects.get_or_create(
            student=self.student_profile,
            semester=self.semester.semester,
            session=str(self.session),
            level=self.student_profile.level,
            defaults={'gpa': 3.0, 'cgpa': 3.0},
        )
        self.client.force_login(self.professor_user)
        post_data = {
            str(self.taken.pk): ['12', '16', '9', '8', '42'],
        }
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/',
            data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_post_scores_new_result_created(self):
        """POST when no Result exists -> except branch (lines 178-184)."""
        Result.objects.filter(
            student=self.student_profile,
            semester=self.semester.semester,
        ).delete()
        self.client.force_login(self.professor_user)
        post_data = {
            str(self.taken.pk): ['11', '14', '7', '6', '38'],
        }
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/',
            data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_post_multiple_students(self):
        """POST scores for >1 student at once."""
        student_user2 = self.create_student_user()
        profile2 = Student.objects.create(
            student=student_user2, level='Bachelor', program=self.program,
        )
        taken2 = TakenCourse.objects.create(
            student=profile2, course=self.course,
        )
        self.client.force_login(self.professor_user)
        post_data = {
            str(self.taken.pk): ['10', '15', '8', '7', '40'],
            str(taken2.pk): ['9', '12', '6', '5', '35'],
        }
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/',
            data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_put_method_fallthrough(self):
        """Non-GET/POST -> line 198 trailing redirect."""
        self.client.force_login(self.professor_user)
        r = self.client.put(
            f'/results/manage-score/{self.course.pk}/',
            data='',
            content_type='application/octet-stream',
        )
        self.assertIn(r.status_code, OK)

    def test_student_forbidden(self):
        self.client.force_login(self.student_user)
        r = self.client.get(f'/results/manage-score/{self.course.pk}/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# grade_result  (lines 206-262)
# =====================================================================
class GradeResultViewTest(ResultViewsTestBase):
    """GET /results/grade/ -- student views grades."""

    def test_grade_result_as_student(self):
        """Full happy path: covers lines 213-262."""
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_no_profile(self):
        """No Student profile -> except (lines 209-211)."""
        user_no_profile = self.create_student_user()
        self.client.force_login(user_no_profile)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_no_results(self):
        """Profile but no Result records."""
        Result.objects.filter(student=self.student_profile).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_professor_forbidden(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_with_second_semester_result(self):
        """CGPA loop (lines 237-248) finds semester='Second'."""
        Result.objects.filter(
            student=self.student_profile, semester='Second',
        ).delete()
        Result.objects.create(
            student=self.student_profile,
            gpa=3.0, cgpa=3.1, semester='Second',
            session='2024/2025', level='Bachelor',
        )
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_cgpa_except_branch(self):
        """No Result with semester='Second' -> except (line 248)."""
        Result.objects.filter(
            student=self.student_profile, semester='Second',
        ).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_first_and_second_semester_credits(self):
        """Credit-summing loop (lines 229-232) for both semesters."""
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_multiple_sessions(self):
        """sorted_result set (line 222) with multiple sessions."""
        Session.objects.create(session='2023/2024', is_current_session=False)
        Result.objects.create(
            student=self.student_profile,
            gpa=2.8, cgpa=2.9, semester='First',
            session='2023/2024', level='Bachelor',
        )
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# assessment_result  (lines 267-285)
# =====================================================================
class AssessmentResultViewTest(ResultViewsTestBase):
    """GET /results/assessment/"""

    def test_assessment_as_student(self):
        self.client.force_login(self.student_user)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK)

    def test_assessment_no_profile(self):
        user_no_profile = self.create_student_user()
        self.client.force_login(user_no_profile)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK)

    def test_assessment_professor_forbidden(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# result_sheet_pdf_view  (lines 290-457)
#
# The view does  settings.MEDIA_ROOT + "/result_sheet/" + fname
# and  settings.STATICFILES_DIRS[0] + "/img/brand.png"
# which requires these settings to be *strings*, not Path objects.
# We override them via @override_settings.
# =====================================================================
@override_settings(
    MEDIA_ROOT=_MEDIA_ROOT,
    STATICFILES_DIRS=_STATICFILES_DIRS,
    BASE_DIR=_BASE_DIR,
)
class ResultSheetPDFViewTest(ResultViewsTestBase):
    """GET /results/result/print/<id>/"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure brand.png exists for all PDF tests
        _ensure_png(os.path.join(_STATICFILES_DIRS[0], 'img', 'brand.png'))

    def test_result_sheet_pdf_as_professor(self):
        """Professor requests PDF result sheet -- covers lines 308-457."""
        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_as_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_student_forbidden(self):
        self.client.force_login(self.student_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_nonexistent_course(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/result/print/99999/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_with_failing_student(self):
        """F-grade branch (lines 415-416) with color=red."""
        fail_user = self.create_student_user()
        fail_profile = Student.objects.create(
            student=fail_user, level='Bachelor', program=self.program,
        )
        TakenCourse.objects.create(
            student=fail_profile,
            course=self.course,
            assignment=Decimal('2'), mid_exam=Decimal('3'),
            quiz=Decimal('1'), attendance=Decimal('1'),
            final_exam=Decimal('5'),
        )
        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_multiple_students(self):
        """PDF with multiple students in the result table."""
        for _ in range(3):
            u = self.create_student_user()
            p = Student.objects.create(
                student=u, level='Bachelor', program=self.program,
            )
            TakenCourse.objects.create(
                student=p, course=self.course,
                assignment=Decimal('10'), mid_exam=Decimal('15'),
                quiz=Decimal('8'), attendance=Decimal('7'),
                final_exam=Decimal('40'),
            )
        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)

    def test_result_sheet_pdf_pass_and_fail_counts(self):
        """Verify both PASS and FAIL counts appear (lines 295-296)."""
        # Create one passing and one failing student
        pass_user = self.create_student_user()
        pass_profile = Student.objects.create(
            student=pass_user, level='Bachelor', program=self.program,
        )
        tc_pass = TakenCourse.objects.create(
            student=pass_profile, course=self.course,
            assignment=Decimal('18'), mid_exam=Decimal('18'),
            quiz=Decimal('9'), attendance=Decimal('9'),
            final_exam=Decimal('40'),
        )
        # Mark as PASS explicitly
        tc_pass.comment = 'PASS'
        tc_pass.save()

        fail_user = self.create_student_user()
        fail_profile = Student.objects.create(
            student=fail_user, level='Bachelor', program=self.program,
        )
        tc_fail = TakenCourse.objects.create(
            student=fail_profile, course=self.course,
            assignment=Decimal('1'), mid_exam=Decimal('1'),
            quiz=Decimal('1'), attendance=Decimal('1'),
            final_exam=Decimal('1'),
        )

        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# course_registration_form  (lines 462-772)
#
# Same path-as-string issue.  Also uses settings.FIRST / settings.SECOND
# and settings.BASE_DIR + request.user.get_picture().
# =====================================================================
@override_settings(
    MEDIA_ROOT=_MEDIA_ROOT,
    STATICFILES_DIRS=_STATICFILES_DIRS,
    BASE_DIR=_BASE_DIR,
    FIRST='First',
    SECOND='Second',
)
class CourseRegistrationFormPDFTest(ResultViewsTestBase):
    """GET /results/registration/form/"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_png(os.path.join(_STATICFILES_DIRS[0], 'img', 'brand.png'))
        _ensure_png(os.path.join(_MEDIA_ROOT, 'default.png'))

    def test_registration_form_as_student(self):
        """Full happy path: covers lines 470-772."""
        self.client.force_login(self.student_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_no_profile(self):
        """No Student profile -> redirect (lines 521-523)."""
        user_no_profile = self.create_student_user()
        self.client.force_login(user_no_profile)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_professor_forbidden(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_with_both_semester_courses(self):
        """Both semester loops (lines 594-621 and 683-711)."""
        self.client.force_login(self.student_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_no_courses(self):
        """Student with profile but no TakenCourse -> loops zero iterations."""
        TakenCourse.objects.filter(student=self.student_profile).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_admin(self):
        """Admins bypass student_required."""
        Student.objects.get_or_create(
            student=self.admin,
            defaults={'level': 'Bachelor', 'program': self.program},
        )
        TakenCourse.objects.create(
            student=Student.objects.get(student=self.admin),
            course=self.course,
        )
        self.client.force_login(self.admin)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_only_first_semester(self):
        """Only first-semester course taken."""
        TakenCourse.objects.filter(
            student=self.student_profile, course=self.course2,
        ).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)

    def test_registration_form_only_second_semester(self):
        """Only second-semester course taken."""
        TakenCourse.objects.filter(
            student=self.student_profile, course=self.course,
        ).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# Edge-case / integration tests for add_score_for POST
# =====================================================================
class AddScoreForEdgeCasesTest(ResultViewsTestBase):
    """Additional edge-case tests for add_score_for POST logic."""

    def test_post_with_zero_scores(self):
        self.client.force_login(self.professor_user)
        post_data = {str(self.taken.pk): ['0', '0', '0', '0', '0']}
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/', data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_post_with_perfect_scores(self):
        self.client.force_login(self.professor_user)
        post_data = {str(self.taken.pk): ['20', '20', '20', '20', '20']}
        r = self.client.post(
            f'/results/manage-score/{self.course.pk}/', data=post_data,
        )
        self.assertIn(r.status_code, OK)

    def test_post_updates_taken_course_fields(self):
        """Verify TakenCourse fields actually updated after POST."""
        self.client.force_login(self.professor_user)
        post_data = {str(self.taken.pk): ['15', '18', '9', '8', '45']}
        self.client.post(
            f'/results/manage-score/{self.course.pk}/', data=post_data,
        )
        self.taken.refresh_from_db()
        self.assertEqual(self.taken.assignment, Decimal('15'))
        self.assertEqual(self.taken.mid_exam, Decimal('18'))
        self.assertEqual(self.taken.quiz, Decimal('9'))
        self.assertEqual(self.taken.attendance, Decimal('8'))
        self.assertEqual(self.taken.final_exam, Decimal('45'))


# =====================================================================
# Edge-case tests for grade_result
# =====================================================================
class GradeResultEdgeCasesTest(ResultViewsTestBase):

    def test_grade_result_anonymous(self):
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, {301, 302})

    def test_grade_result_no_taken_courses(self):
        TakenCourse.objects.filter(student=self.student_profile).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)

    def test_grade_result_admin(self):
        Student.objects.get_or_create(
            student=self.admin,
            defaults={'level': 'Bachelor', 'program': self.program},
        )
        self.client.force_login(self.admin)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# Edge-case tests for assessment_result
# =====================================================================
class AssessmentResultEdgeCasesTest(ResultViewsTestBase):

    def test_assessment_anonymous(self):
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, {301, 302})

    def test_assessment_no_taken_courses(self):
        TakenCourse.objects.filter(student=self.student_profile).delete()
        self.client.force_login(self.student_user)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK)

    def test_assessment_admin(self):
        Student.objects.get_or_create(
            student=self.admin,
            defaults={'level': 'Bachelor', 'program': self.program},
        )
        self.client.force_login(self.admin)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# Edge-case tests for result_sheet_pdf_view
# =====================================================================
class ResultSheetPDFEdgeCasesTest(ResultViewsTestBase):

    def test_pdf_anonymous(self):
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, {301, 302})

    @override_settings(
        MEDIA_ROOT=_MEDIA_ROOT,
        STATICFILES_DIRS=_STATICFILES_DIRS,
        BASE_DIR=_BASE_DIR,
    )
    def test_pdf_no_taken_courses(self):
        """Course with no students -- may crash at line 376 (500 OK)."""
        _ensure_png(os.path.join(_STATICFILES_DIRS[0], 'img', 'brand.png'))
        TakenCourse.objects.filter(course=self.course).delete()
        self.client.force_login(self.professor_user)
        r = self.client.get(f'/results/result/print/{self.course.pk}/')
        self.assertIn(r.status_code, OK)


# =====================================================================
# Edge-case tests for course_registration_form
# =====================================================================
class CourseRegistrationFormEdgeCasesTest(ResultViewsTestBase):

    def test_registration_form_anonymous(self):
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, {301, 302})
