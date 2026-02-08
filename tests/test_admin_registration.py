"""
Test that all models are properly registered with Django admin.

This ensures admin.py files are correctly configured and don't crash
on import. Each test verifies the model is registered and the admin
class has expected attributes.
"""

from django.contrib import admin
from django.test import TestCase


class AdminRegistrationTest(TestCase):
    """Verify all models are registered with Django admin."""

    def _check_registered(self, model_class):
        """Assert model is registered in admin."""
        self.assertIn(model_class, admin.site._registry,
                       f"{model_class.__name__} not registered in admin")
        return admin.site._registry[model_class]

    # --- core ---
    def test_school_registered(self):
        from core.models import School
        self._check_registered(School)

    def test_session_registered(self):
        from core.models import Session
        self._check_registered(Session)

    def test_semester_registered(self):
        from core.models import Semester
        self._check_registered(Semester)

    def test_news_events_registered(self):
        from core.models import NewsAndEvents
        self._check_registered(NewsAndEvents)

    def test_activity_log_registered(self):
        from core.models import ActivityLog
        self._check_registered(ActivityLog)

    # --- accounts ---
    def test_user_registered(self):
        from accounts.models import User
        self._check_registered(User)

    # --- course ---
    def test_program_registered(self):
        from course.models import Program
        self._check_registered(Program)

    def test_course_registered(self):
        from course.models import Course
        ma = self._check_registered(Course)
        self.assertIn('title', ma.search_fields)

    def test_course_allocation_registered(self):
        from course.models import CourseAllocation
        self._check_registered(CourseAllocation)

    def test_upload_registered(self):
        from course.models import Upload
        self._check_registered(Upload)

    # --- result ---
    def test_taken_course_registered(self):
        from result.models import TakenCourse
        ma = self._check_registered(TakenCourse)
        self.assertTrue(len(ma.list_display) > 1)

    def test_result_registered(self):
        from result.models import Result
        self._check_registered(Result)

    # --- quiz ---
    def test_quiz_registered(self):
        from quiz.models import Quiz
        self._check_registered(Quiz)

    def test_mcquestion_registered(self):
        from quiz.models import MCQuestion
        self._check_registered(MCQuestion)

    def test_essay_question_registered(self):
        from quiz.models import EssayQuestion
        self._check_registered(EssayQuestion)

    def test_progress_registered(self):
        from quiz.models import Progress
        self._check_registered(Progress)

    def test_sitting_registered(self):
        from quiz.models import Sitting
        self._check_registered(Sitting)

    # --- enrollment ---
    def test_registration_form_registered(self):
        from enrollment.models import RegistrationForm
        ma = self._check_registered(RegistrationForm)
        self.assertTrue(len(ma.list_display) > 1)
        self.assertTrue(len(ma.list_filter) > 0)

    def test_enrollment_document_registered(self):
        from enrollment.models import EnrollmentDocument
        self._check_registered(EnrollmentDocument)

    def test_enrollment_status_history_registered(self):
        from enrollment.models import EnrollmentStatusHistory
        self._check_registered(EnrollmentStatusHistory)

    # --- filieres ---
    def test_filiere_registered(self):
        from filieres.models import Filiere
        self._check_registered(Filiere)

    # --- payments ---
    # payments admin is empty, skip

    # --- attendance ---
    def test_attendance_group_registered(self):
        from attendance.models import Group
        self._check_registered(Group)

    def test_attendance_student_registered(self):
        from attendance.models import Student
        self._check_registered(Student)

    def test_subject_registered(self):
        from attendance.models import Subject
        ma = self._check_registered(Subject)
        self.assertIn('name', ma.search_fields)

    def test_attendance_registered(self):
        from attendance.models import Attendance
        self._check_registered(Attendance)

    def test_attendance_report_registered(self):
        from attendance.models import AttendanceReport
        self._check_registered(AttendanceReport)

    # --- library ---
    def test_book_registered(self):
        from library.models import Book
        ma = self._check_registered(Book)
        self.assertIn('title', ma.search_fields)

    def test_borrow_record_registered(self):
        from library.models import BorrowRecord
        self._check_registered(BorrowRecord)

    # --- forums ---
    def test_forum_category_registered(self):
        from forums.models import ForumCategory
        self._check_registered(ForumCategory)

    def test_thread_registered(self):
        from forums.models import Thread
        ma = self._check_registered(Thread)
        self.assertTrue(len(ma.list_display) > 1)

    def test_post_registered(self):
        from forums.models import Post
        self._check_registered(Post)

    def test_vote_registered(self):
        from forums.models import Vote
        self._check_registered(Vote)

    def test_tag_registered(self):
        from forums.models import Tag
        self._check_registered(Tag)

    def test_thread_subscription_registered(self):
        from forums.models import ThreadSubscription
        self._check_registered(ThreadSubscription)

    def test_report_registered(self):
        from forums.models import Report
        self._check_registered(Report)

    # --- notices ---
    def test_notice_registered(self):
        from notices.models import Notice
        ma = self._check_registered(Notice)
        self.assertTrue(len(ma.list_display) > 1)

    def test_notice_document_registered(self):
        from notices.models import NoticeDocument
        self._check_registered(NoticeDocument)

    def test_notify_group_registered(self):
        from notices.models import NotifyGroup
        self._check_registered(NotifyGroup)

    def test_notice_response_registered(self):
        from notices.models import NoticeResponse
        self._check_registered(NoticeResponse)

    # --- articles ---
    def test_article_category_registered(self):
        from articles.models import Category
        self._check_registered(Category)

    def test_article_registered(self):
        from articles.models import Article
        ma = self._check_registered(Article)
        self.assertTrue(len(ma.list_display) > 1)

    def test_article_comment_registered(self):
        from articles.models import Comment
        self._check_registered(Comment)

    def test_article_like_registered(self):
        from articles.models import Like
        self._check_registered(Like)

    def test_newsletter_registered(self):
        from articles.models import Newsletter
        self._check_registered(Newsletter)

    def test_newsletter_sent_registered(self):
        from articles.models import NewsletterSent
        self._check_registered(NewsletterSent)

    # --- events ---
    def test_event_registered(self):
        from events.models import Event
        ma = self._check_registered(Event)
        self.assertTrue(len(ma.list_display) > 1)

    # --- discipline ---
    def test_disciplinary_action_registered(self):
        from discipline.models import DisciplinaryAction
        self._check_registered(DisciplinaryAction)

    # --- notes ---
    def test_professor_note_registered(self):
        from notes.models import ProfessorNote
        ma = self._check_registered(ProfessorNote)
        self.assertTrue(len(ma.list_display) > 1)

    def test_note_history_registered(self):
        from notes.models import NoteHistory
        self._check_registered(NoteHistory)

    def test_note_comment_registered(self):
        from notes.models import NoteComment
        self._check_registered(NoteComment)

    # --- grading ---
    def test_grading_rubric_registered(self):
        from grading.models import GradingRubric
        ma = self._check_registered(GradingRubric)
        self.assertTrue(len(ma.list_display) > 1)

    def test_rubric_criterion_registered(self):
        from grading.models import RubricCriterion
        self._check_registered(RubricCriterion)

    def test_rubric_grade_registered(self):
        from grading.models import RubricGrade
        self._check_registered(RubricGrade)

    def test_criterion_grade_registered(self):
        from grading.models import CriterionGrade
        self._check_registered(CriterionGrade)

    def test_peer_review_registered(self):
        from grading.models import PeerReview
        self._check_registered(PeerReview)

    def test_grade_curve_registered(self):
        from grading.models import GradeCurve
        self._check_registered(GradeCurve)

    # --- certificates ---
    def test_certificate_template_registered(self):
        from certificates.models import CertificateTemplate
        self._check_registered(CertificateTemplate)

    def test_certificate_registered(self):
        from certificates.models import Certificate
        ma = self._check_registered(Certificate)
        self.assertTrue(len(ma.list_display) > 1)

    def test_certificate_verification_registered(self):
        from certificates.models import CertificateVerification
        self._check_registered(CertificateVerification)

    def test_batch_certificate_registered(self):
        from certificates.models import BatchCertificateGeneration
        self._check_registered(BatchCertificateGeneration)

    # --- analytics ---
    def test_student_engagement_registered(self):
        from analytics.models import StudentEngagement
        ma = self._check_registered(StudentEngagement)
        self.assertTrue(len(ma.list_display) > 1)

    def test_course_completion_registered(self):
        from analytics.models import CourseCompletion
        self._check_registered(CourseCompletion)

    def test_learning_outcome_registered(self):
        from analytics.models import LearningOutcome
        self._check_registered(LearningOutcome)

    def test_outcome_measurement_registered(self):
        from analytics.models import OutcomeMeasurement
        self._check_registered(OutcomeMeasurement)

    def test_analytics_activity_log_registered(self):
        from analytics.models import ActivityLog
        self._check_registered(ActivityLog)

    def test_at_risk_student_registered(self):
        from analytics.models import AtRiskStudent
        self._check_registered(AtRiskStudent)

    # --- admissions ---
    def test_admission_session_registered(self):
        from admissions.models import AdmissionSession
        self._check_registered(AdmissionSession)

    def test_admission_student_registered(self):
        from admissions.models import AdmissionStudent
        self._check_registered(AdmissionStudent)

    def test_counseling_comment_registered(self):
        from admissions.models import CounselingComment
        self._check_registered(CounselingComment)

    def test_admission_payment_registered(self):
        from admissions.models import AdmissionPayment
        self._check_registered(AdmissionPayment)

    # --- alumni ---
    def test_alumni_registered(self):
        from alumni.models import Alumni
        self._check_registered(Alumni)

    def test_alumni_event_registered(self):
        from alumni.models import AlumniEvent
        self._check_registered(AlumniEvent)

    def test_alumni_donation_registered(self):
        from alumni.models import AlumniDonation
        self._check_registered(AlumniDonation)

    def test_alumni_achievement_registered(self):
        from alumni.models import AlumniAchievement
        self._check_registered(AlumniAchievement)

    # --- dailystat ---
    def test_dailystat_registered(self):
        from dailystat.models import DailyAttendanceStat
        self._check_registered(DailyAttendanceStat)
