"""
Tests for filieres signal handlers.

Signals tested:
1. log_filiere_creation (post_save on Filiere) - logs when a new filiere is created
2. log_subject_added (post_save on FiliereSubject) - logs when a subject is added
3. log_subject_removed (pre_delete on FiliereSubject) - logs when a subject is removed
"""

import logging
from unittest.mock import patch, MagicMock

from django.test import TestCase

from filieres.models import Filiere, FiliereSubject
from tests.helpers import TestDataMixin


class LogFiliereCreationSignalTest(TestDataMixin, TestCase):
    """Tests for the log_filiere_creation post_save signal."""

    def test_new_filiere_logs_info(self):
        """Creating a new filiere logs an INFO message."""
        with self.assertLogs('filieres.signals', level='INFO') as cm:
            filiere = self.create_filiere()

        log_output = '\n'.join(cm.output)
        self.assertIn('New filiere created', log_output)

    def test_log_includes_filiere_name(self):
        """Log message includes the filiere name."""
        with self.assertLogs('filieres.signals', level='INFO') as cm:
            filiere = self.create_filiere(name='Computer Science')

        log_output = '\n'.join(cm.output)
        self.assertIn('Computer Science', log_output)

    def test_log_includes_filiere_code(self):
        """Log message includes the filiere code."""
        with self.assertLogs('filieres.signals', level='INFO') as cm:
            filiere = self.create_filiere(code='CS101')

        log_output = '\n'.join(cm.output)
        self.assertIn('CS101', log_output)

    def test_log_includes_tenant_info(self):
        """Log message includes the tenant (school) info."""
        school = self.create_school(name='Test Academy')

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            self.create_filiere(tenant=school)

        log_output = '\n'.join(cm.output)
        self.assertIn('Test Academy', log_output)

    def test_update_filiere_does_not_log_creation(self):
        """Updating a filiere does NOT log a creation message."""
        filiere = self.create_filiere()

        logger = logging.getLogger('filieres.signals')
        with patch.object(logger, 'info') as mock_info:
            filiere.name = 'Updated Name'
            filiere.save()

            for call in mock_info.call_args_list:
                self.assertNotIn('New filiere created', str(call))


class LogSubjectAddedSignalTest(TestDataMixin, TestCase):
    """Tests for the log_subject_added post_save signal."""

    def test_adding_subject_logs_info(self):
        """Adding a subject to a filiere logs an INFO message."""
        filiere = self.create_filiere()
        course = self.create_course()

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            FiliereSubject.objects.create(
                filiere=filiere,
                subject=course,
                year=1,
                semester=1,
                coefficient=2.00,
            )

        log_output = '\n'.join(cm.output)
        self.assertIn('added to', log_output)

    def test_log_includes_subject_title(self):
        """Log message includes the subject title."""
        filiere = self.create_filiere()
        course = self.create_course(title='Advanced Algorithms')

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            FiliereSubject.objects.create(
                filiere=filiere,
                subject=course,
                year=1,
                semester=1,
                coefficient=3.00,
            )

        log_output = '\n'.join(cm.output)
        self.assertIn('Advanced Algorithms', log_output)

    def test_log_includes_filiere_name(self):
        """Log message includes the filiere name."""
        filiere = self.create_filiere(name='Data Science')
        course = self.create_course()

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            FiliereSubject.objects.create(
                filiere=filiere,
                subject=course,
                year=2,
                semester=1,
                coefficient=1.50,
            )

        log_output = '\n'.join(cm.output)
        self.assertIn('Data Science', log_output)

    def test_log_includes_year_semester_coefficient(self):
        """Log message includes the year, semester, and coefficient."""
        filiere = self.create_filiere()
        course = self.create_course()

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            FiliereSubject.objects.create(
                filiere=filiere,
                subject=course,
                year=3,
                semester=2,
                coefficient=4.50,
            )

        log_output = '\n'.join(cm.output)
        self.assertIn('Year 3', log_output)
        self.assertIn('Semester 2', log_output)
        self.assertIn('4.5', log_output)

    def test_update_subject_does_not_log_added(self):
        """Updating an existing FiliereSubject does NOT log 'added to'."""
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere,
            subject=course,
            year=1,
            semester=1,
            coefficient=2.00,
        )

        logger = logging.getLogger('filieres.signals')
        with patch.object(logger, 'info') as mock_info:
            fs.coefficient = 3.00
            fs.save()

            for call in mock_info.call_args_list:
                self.assertNotIn('added to', str(call))


class LogSubjectRemovedSignalTest(TestDataMixin, TestCase):
    """Tests for the log_subject_removed pre_delete signal."""

    def test_removing_subject_logs_info(self):
        """Deleting a FiliereSubject logs an INFO message."""
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere,
            subject=course,
            year=1,
            semester=1,
            coefficient=2.00,
        )

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            fs.delete()

        log_output = '\n'.join(cm.output)
        self.assertIn('removed from', log_output)

    def test_removal_log_includes_subject_title(self):
        """Removal log includes the subject title."""
        filiere = self.create_filiere()
        course = self.create_course(title='Linear Algebra')
        fs = FiliereSubject.objects.create(
            filiere=filiere,
            subject=course,
            year=1,
            semester=1,
            coefficient=2.00,
        )

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            fs.delete()

        log_output = '\n'.join(cm.output)
        self.assertIn('Linear Algebra', log_output)

    def test_removal_log_includes_filiere_name(self):
        """Removal log includes the filiere name."""
        filiere = self.create_filiere(name='Mathematics')
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere,
            subject=course,
            year=1,
            semester=1,
            coefficient=2.00,
        )

        with self.assertLogs('filieres.signals', level='INFO') as cm:
            fs.delete()

        log_output = '\n'.join(cm.output)
        self.assertIn('Mathematics', log_output)
