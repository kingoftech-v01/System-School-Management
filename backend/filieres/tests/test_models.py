"""Tests for filieres app models."""

from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError

from filieres.models import Filiere, FiliereSubject, FiliereRequirement
from tests.helpers import TestDataMixin


class FiliereModelTest(TestDataMixin, TestCase):
    def test_create_filiere(self):
        filiere = self.create_filiere()
        self.assertIsNotNone(filiere.pk)

    def test_str(self):
        filiere = self.create_filiere(name='Computer Science', code='CS')
        self.assertEqual(str(filiere), 'Computer Science (CS)')

    def test_default_is_active(self):
        filiere = self.create_filiere()
        self.assertTrue(filiere.is_active)

    def test_default_duration_years(self):
        filiere = self.create_filiere()
        self.assertEqual(filiere.duration_years, 3)

    def test_get_total_subjects_empty(self):
        filiere = self.create_filiere()
        self.assertEqual(filiere.get_total_subjects(), 0)

    def test_get_total_subjects_with_subjects(self):
        filiere = self.create_filiere()
        course = self.create_course()
        FiliereSubject.objects.create(
            filiere=filiere, subject=course, year=1, semester=1,
        )
        self.assertEqual(filiere.get_total_subjects(), 1)

    def test_get_enrolled_students_count(self):
        filiere = self.create_filiere()
        self.assertEqual(filiere.get_enrolled_students_count(), 0)

    def test_is_full_no_capacity(self):
        filiere = self.create_filiere(capacity=None)
        self.assertFalse(filiere.is_full())

    def test_is_full_under_capacity(self):
        filiere = self.create_filiere(capacity=10)
        self.assertFalse(filiere.is_full())

    def test_unique_code_per_tenant(self):
        tenant = self.create_school()
        self.create_filiere(tenant=tenant, code='CS')
        with self.assertRaises(Exception):
            self.create_filiere(tenant=tenant, code='CS')

    def test_coordinator_optional(self):
        filiere = self.create_filiere(coordinator=None)
        self.assertIsNone(filiere.coordinator)

    def test_coordinator_assignment(self):
        prof = self.create_professor_user()
        filiere = self.create_filiere(coordinator=prof)
        self.assertEqual(filiere.coordinator, prof)


class FiliereSubjectModelTest(TestDataMixin, TestCase):
    def test_create_subject(self):
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere, subject=course,
            coefficient=Decimal('2.0'), year=1, semester=1,
            credits=3, hours_per_week=4,
        )
        self.assertIsNotNone(fs.pk)

    def test_str(self):
        filiere = self.create_filiere(code='CS')
        course = self.create_course(title='Programming')
        fs = FiliereSubject.objects.create(
            filiere=filiere, subject=course, year=1, semester=1,
        )
        result = str(fs)
        self.assertIn('CS', result)

    def test_get_total_hours(self):
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere, subject=course, year=1, semester=1,
            hours_per_week=4,
        )
        self.assertEqual(fs.get_total_hours(), 60)  # 4 * 15

    def test_default_is_mandatory(self):
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere, subject=course, year=1, semester=1,
        )
        self.assertTrue(fs.is_mandatory)

    def test_default_credits(self):
        filiere = self.create_filiere()
        course = self.create_course()
        fs = FiliereSubject.objects.create(
            filiere=filiere, subject=course, year=1, semester=1,
        )
        self.assertEqual(fs.credits, 3)


class FiliereRequirementModelTest(TestDataMixin, TestCase):
    def test_create_requirement(self):
        filiere = self.create_filiere()
        req = FiliereRequirement.objects.create(
            filiere=filiere, requirement_type='academic',
            description='Must have minimum GPA 3.0',
        )
        self.assertIsNotNone(req.pk)

    def test_str(self):
        filiere = self.create_filiere(code='CS')
        req = FiliereRequirement.objects.create(
            filiere=filiere, requirement_type='academic',
            description='Test requirement',
        )
        result = str(req)
        self.assertIn('CS', result)

    def test_default_is_mandatory(self):
        filiere = self.create_filiere()
        req = FiliereRequirement.objects.create(
            filiere=filiere, requirement_type='language',
            description='English proficiency',
        )
        self.assertTrue(req.is_mandatory)

    def test_default_order(self):
        filiere = self.create_filiere()
        req = FiliereRequirement.objects.create(
            filiere=filiere, requirement_type='exam',
            description='Entrance exam',
        )
        self.assertEqual(req.order, 0)
