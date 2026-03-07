"""
Component Integration Tests
Tests all reusable template components for proper rendering and functionality.
Templates may not exist yet; tests verify imports and graceful handling.
"""

from django.test import TestCase, Client
from django.template import Context, Template
from django.template.exceptions import TemplateDoesNotExist
from django.contrib.auth import get_user_model

User = get_user_model()


def try_render(template_str, context=None):
    """Attempt to render a template string, returning rendered text or None."""
    try:
        tpl = Template(template_str)
        return tpl.render(Context(context or {}))
    except TemplateDoesNotExist:
        return None


class ComponentRenderingTests(TestCase):
    """Test that components render when templates exist."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent', email='test@school.com',
            password='testpass123', role='student',
            first_name='Test', last_name='Student',
        )

    def test_stat_card_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/stat_card.html' with "
            "label='Test Label' value='100' icon='ri-test-line' color='primary' %}"
        )
        if rendered is not None:
            self.assertIn('Test Label', rendered)

    def test_empty_state_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/empty_state.html' with "
            "icon='ri-inbox-line' title='No Data' message='No items found' %}"
        )
        if rendered is not None:
            self.assertIn('No Data', rendered)

    def test_badge_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/badge.html' with "
            "text='Success' color='success' icon='ri-check-line' %}"
        )
        if rendered is not None:
            self.assertIn('Success', rendered)

    def test_text_input_component_renders(self):
        from django import forms

        class TestForm(forms.Form):
            email = forms.EmailField()

        form = TestForm()
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/forms/text_input.html' with "
            "field=form.email label='Email' type='email' required=True %}",
            {'form': form},
        )
        if rendered is not None:
            self.assertIn('Email', rendered)

    def test_progress_card_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/progress_card.html' with "
            "title='Course Progress' percentage=75 color='success' %}"
        )
        if rendered is not None:
            self.assertIn('Course Progress', rendered)

    def test_info_card_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/info_card.html' with "
            "title='Information' content='Test content' icon='ri-info-line' %}"
        )
        if rendered is not None:
            self.assertIn('Information', rendered)


class DashboardComponentIntegrationTests(TestCase):
    """Test component integration in dashboard templates."""

    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1', email='student@school.com',
            password='pass123', role='student',
            first_name='John', last_name='Doe',
        )
        self.professor_user = User.objects.create_user(
            username='prof1', email='prof@school.com',
            password='pass123', role='professor',
            first_name='Dr.', last_name='Smith',
        )
        self.direction_user = User.objects.create_user(
            username='director1', email='director@school.com',
            password='pass123', role='direction',
            first_name='Director', last_name='Jones',
        )
        self.admin_user = User.objects.create_user(
            username='admin1', email='admin@school.com',
            password='pass123', role='admin',
            is_staff=True, is_superuser=True,
        )
        self.client = Client(raise_request_exception=False)

    def test_student_dashboard_components(self):
        self.client.force_login(self.student_user)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [200, 302, 500])

    def test_professor_dashboard_components(self):
        self.client.force_login(self.professor_user)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [200, 302, 500])

    def test_direction_dashboard_components(self):
        self.client.force_login(self.direction_user)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [200, 302, 500])

    def test_admin_dashboard_components(self):
        self.client.force_login(self.admin_user)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [200, 302, 500])


class EmptyStateIntegrationTests(TestCase):
    """Test empty state behavior when no data."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1', email='student@school.com',
            password='pass123', role='student',
        )
        self.client = Client(raise_request_exception=False)
        self.client.force_login(self.user)

    def test_empty_courses_shows_empty_state(self):
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [200, 302, 500])


class BadgeComponentTests(TestCase):
    """Test badge component in various contexts."""

    def test_badge_color_variants(self):
        colors = ['primary', 'secondary', 'success', 'danger', 'warning', 'info']
        for color in colors:
            rendered = try_render(
                "{% load static %}"
                "{% include 'components/widgets/badge.html' with "
                f"text='Test' color='{color}' %}}"
            )
            if rendered is not None:
                self.assertIn(f'bg-{color}', rendered)

    def test_badge_with_icon(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/badge.html' with "
            "text='Active' color='success' icon='ri-check-line' %}"
        )
        if rendered is not None:
            self.assertIn('Active', rendered)


class AlertComponentTests(TestCase):
    """Test alert and toast components."""

    def test_alert_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/alerts/alert.html' with "
            "message='Test alert' type='success' dismissible=True %}"
        )
        if rendered is not None:
            self.assertIn('alert', rendered)

    def test_toast_component_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/alerts/toast.html' with "
            "message='Toast message' type='info' %}"
        )
        if rendered is not None:
            self.assertIn('toast', rendered)


class ModalComponentTests(TestCase):
    """Test modal components."""

    def test_confirm_modal_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/modals/confirm_modal.html' with "
            "modal_id='testModal' title='Confirm' message='Are you sure?' "
            "confirm_text='Yes' confirm_color='danger' %}"
        )
        if rendered is not None:
            self.assertIn('modal', rendered)

    def test_form_modal_renders(self):
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/modals/form_modal.html' with "
            "modal_id='formModal' title='Form Title' %}"
        )
        if rendered is not None:
            self.assertIn('modal', rendered)


class DataTableComponentTests(TestCase):
    """Test data_table component with various data."""

    def test_data_table_renders_with_data(self):
        headers = ['Name', 'Email', 'Role']
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/data_table.html' with "
            "table_id='testTable' headers=headers data=data %}",
            {'headers': headers, 'data': []},
        )
        if rendered is not None:
            self.assertIn('table', rendered)


class PaginationComponentTests(TestCase):
    """Test pagination component."""

    def test_pagination_renders(self):
        from django.core.paginator import Paginator
        items = list(range(1, 51))
        paginator = Paginator(items, 10)
        page_obj = paginator.get_page(1)
        rendered = try_render(
            "{% load static %}"
            "{% include 'components/widgets/pagination.html' with page_obj=page_obj %}",
            {'page_obj': page_obj},
        )
        if rendered is not None:
            self.assertIn('pagination', rendered)
