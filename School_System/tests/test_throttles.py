"""Tests for School_System throttle classes."""

from django.test import TestCase

from School_System.throttles import (
    BurstRateThrottle,
    SustainedRateThrottle,
    AnonymousBurstRateThrottle,
    AnonymousSustainedRateThrottle,
    VerificationRateThrottle,
    UploadRateThrottle,
    ExportRateThrottle,
)
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BurstRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(BurstRateThrottle.scope, 'burst')

    def test_inherits_user_throttle(self):
        self.assertTrue(issubclass(BurstRateThrottle, UserRateThrottle))


class SustainedRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(SustainedRateThrottle.scope, 'sustained')

    def test_inherits_user_throttle(self):
        self.assertTrue(issubclass(SustainedRateThrottle, UserRateThrottle))


class AnonymousBurstRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(AnonymousBurstRateThrottle.scope, 'anon_burst')

    def test_inherits_anon_throttle(self):
        self.assertTrue(issubclass(AnonymousBurstRateThrottle, AnonRateThrottle))


class AnonymousSustainedRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(AnonymousSustainedRateThrottle.scope, 'anon_sustained')

    def test_inherits_anon_throttle(self):
        self.assertTrue(issubclass(AnonymousSustainedRateThrottle, AnonRateThrottle))


class VerificationRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(VerificationRateThrottle.scope, 'verification')

    def test_inherits_anon_throttle(self):
        self.assertTrue(issubclass(VerificationRateThrottle, AnonRateThrottle))


class UploadRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(UploadRateThrottle.scope, 'uploads')

    def test_inherits_user_throttle(self):
        self.assertTrue(issubclass(UploadRateThrottle, UserRateThrottle))


class ExportRateThrottleTest(TestCase):
    def test_scope(self):
        self.assertEqual(ExportRateThrottle.scope, 'exports')

    def test_inherits_user_throttle(self):
        self.assertTrue(issubclass(ExportRateThrottle, UserRateThrottle))
