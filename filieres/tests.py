"""
Tests for filieres app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Filiere, FiliereSubject, FiliereRequirement
from core.models import School
from course.models import Course, Program

User = get_user_model()


class FiliereModelTest(TestCase):
    """Test Filiere model."""

    def setUp(self):
        """Set up test data."""
        self.tenant = School.objects.create(
            schema_name='test_school',
            name='Test School'
        )

    def test_create_filiere(self):
        """Test creating a filiere."""
        filiere = Filiere.objects.create(
            tenant=self.tenant,
            name='Computer Science',
            code='CS',
            level='Bachelor',
            duration_years=3
        )

        self.assertEqual(str(filiere), 'Computer Science (CS)')
        self.assertTrue(filiere.is_active)
        self.assertEqual(filiere.get_total_subjects(), 0)

    def test_filiere_unique_code_per_tenant(self):
        """Test that filiere codes must be unique per tenant."""
        Filiere.objects.create(
            tenant=self.tenant,
            name='Computer Science',
            code='CS'
        )

        # Should raise error for duplicate code in same tenant
        with self.assertRaises(Exception):
            Filiere.objects.create(
                tenant=self.tenant,
                name='Cyber Security',
                code='CS'
            )


class FiliereSubjectModelTest(TestCase):
    """Test FiliereSubject model."""

    def setUp(self):
        """Set up test data."""
        self.tenant = School.objects.create(
            schema_name='test_school',
            name='Test School'
        )
        self.filiere = Filiere.objects.create(
            tenant=self.tenant,
            name='Computer Science',
            code='CS'
        )
        self.program = Program.objects.create(
            title='Test Program',
            summary='Test'
        )
        self.course = Course.objects.create(
            title='Programming 101',
            code='CS101',
            credit=3,
            program=self.program
        )

    def test_add_subject_to_filiere(self):
        """Test adding a subject to a filiere."""
        filiere_subject = FiliereSubject.objects.create(
            filiere=self.filiere,
            subject=self.course,
            coefficient=Decimal('2.0'),
            year=1,
            semester=1,
            credits=3,
            hours_per_week=4
        )

        self.assertEqual(self.filiere.get_total_subjects(), 1)
        self.assertEqual(filiere_subject.get_total_hours(), 60)  # 4 * 15 weeks
