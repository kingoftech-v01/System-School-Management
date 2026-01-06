"""
Component Integration Tests
Tests all 15 reusable template components for proper rendering and functionality.
"""

from django.test import TestCase, Client
from django.template import Context, Template
from django.contrib.auth import get_user_model
from accounts.models import Student
from core.models import Session, Semester

User = get_user_model()


class ComponentRenderingTests(TestCase):
    """Test that all components render correctly."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            email='test@school.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='Student'
        )

    def test_stat_card_component_renders(self):
        """Test stat_card component renders with all parameters."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/stat_card.html' with "
            "label='Test Label' value='100' icon='ri-test-line' color='primary' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('stat-card', rendered)
        self.assertIn('stat-card-primary', rendered)
        self.assertIn('Test Label', rendered)
        self.assertIn('100', rendered)
        self.assertIn('ri-test-line', rendered)

    def test_empty_state_component_renders(self):
        """Test empty_state component renders correctly."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/empty_state.html' with "
            "icon='ri-inbox-line' title='No Data' message='No items found' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('empty-state', rendered)
        self.assertIn('ri-inbox-line', rendered)
        self.assertIn('No Data', rendered)
        self.assertIn('No items found', rendered)

    def test_badge_component_renders(self):
        """Test badge component renders with different colors."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/badge.html' with "
            "text='Success' color='success' icon='ri-check-line' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('badge', rendered)
        self.assertIn('bg-success', rendered)
        self.assertIn('Success', rendered)
        self.assertIn('ri-check-line', rendered)

    def test_text_input_component_renders(self):
        """Test form text_input component."""
        from django import forms

        class TestForm(forms.Form):
            email = forms.EmailField()

        form = TestForm()
        template = Template(
            "{% load static %}"
            "{% include 'components/forms/text_input.html' with "
            "field=form.email label='Email' type='email' required=True %}"
        )
        rendered = template.render(Context({'form': form}))

        self.assertIn('form-control', rendered)
        self.assertIn('Email', rendered)
        self.assertIn('type="email"', rendered)

    def test_progress_card_component_renders(self):
        """Test progress_card component renders with percentage."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/progress_card.html' with "
            "title='Course Progress' percentage=75 color='success' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('progress-card', rendered)
        self.assertIn('Course Progress', rendered)
        self.assertIn('75%', rendered)

    def test_info_card_component_renders(self):
        """Test info_card component renders correctly."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/info_card.html' with "
            "title='Information' content='Test content' icon='ri-info-line' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('info-card', rendered)
        self.assertIn('Information', rendered)
        self.assertIn('Test content', rendered)
        self.assertIn('ri-info-line', rendered)


class DashboardComponentIntegrationTests(TestCase):
    """Test component integration in actual dashboard templates."""

    def setUp(self):
        """Set up test users for each role."""
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@school.com',
            password='pass123',
            role='student',
            first_name='John',
            last_name='Doe'
        )

        self.professor_user = User.objects.create_user(
            username='prof1',
            email='prof@school.com',
            password='pass123',
            role='professor',
            first_name='Dr.',
            last_name='Smith'
        )

        self.direction_user = User.objects.create_user(
            username='director1',
            email='director@school.com',
            password='pass123',
            role='direction',
            first_name='Director',
            last_name='Jones'
        )

        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@school.com',
            password='pass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )

        self.client = Client()

    def test_student_dashboard_components(self):
        """Test student dashboard renders all stat card components."""
        self.client.login(username='student1', password='pass123')
        response = self.client.get('/dashboard/')

        # Should contain stat card components
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'ri-award-line')  # GPA card
        self.assertContains(response, 'ri-book-open-line')  # Courses card
        self.assertContains(response, 'ri-calendar-check-line')  # Attendance card

    def test_professor_dashboard_components(self):
        """Test professor dashboard renders all components."""
        self.client.login(username='prof1', password='pass123')
        response = self.client.get('/dashboard/')

        # Should contain stat cards
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'ri-presentation-line')  # Classes card

    def test_direction_dashboard_components(self):
        """Test direction dashboard renders all components."""
        self.client.login(username='director1', password='pass123')
        response = self.client.get('/dashboard/')

        # Should contain stat cards
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'ri-user-line')  # Students card
        self.assertContains(response, 'ri-user-star-line')  # Professors card

    def test_admin_dashboard_components(self):
        """Test admin dashboard renders all components."""
        self.client.login(username='admin1', password='pass123')
        response = self.client.get('/dashboard/')

        # Should contain stat cards
        self.assertContains(response, 'stat-card')
        self.assertContains(response, 'ri-building-line')  # Tenants card
        self.assertContains(response, 'ri-server-line')  # System status card


class EmptyStateIntegrationTests(TestCase):
    """Test empty state components appear when no data."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='student1',
            email='student@school.com',
            password='pass123',
            role='student'
        )
        self.client = Client()
        self.client.login(username='student1', password='pass123')

    def test_empty_courses_shows_empty_state(self):
        """Test empty state appears when student has no courses."""
        response = self.client.get('/dashboard/')

        # Should contain empty state component
        self.assertContains(response, 'empty-state')
        self.assertContains(response, 'No courses registered')


class BadgeComponentTests(TestCase):
    """Test badge component in various contexts."""

    def test_badge_color_variants(self):
        """Test all badge color variants render correctly."""
        colors = ['primary', 'secondary', 'success', 'danger', 'warning', 'info']

        for color in colors:
            template = Template(
                "{% load static %}"
                "{% include 'components/widgets/badge.html' with "
                "text='Test' color='" + color + "' %}"
            )
            rendered = template.render(Context({}))
            self.assertIn(f'bg-{color}', rendered)

    def test_badge_with_icon(self):
        """Test badge renders with icon."""
        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/badge.html' with "
            "text='Active' color='success' icon='ri-check-line' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('ri-check-line', rendered)
        self.assertIn('Active', rendered)


class AlertComponentTests(TestCase):
    """Test alert and toast components."""

    def test_alert_component_renders(self):
        """Test alert component renders with message."""
        template = Template(
            "{% load static %}"
            "{% include 'components/alerts/alert.html' with "
            "message='Test alert' type='success' dismissible=True %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('alert', rendered)
        self.assertIn('alert-success', rendered)
        self.assertIn('Test alert', rendered)

    def test_toast_component_renders(self):
        """Test toast notification component."""
        template = Template(
            "{% load static %}"
            "{% include 'components/alerts/toast.html' with "
            "message='Toast message' type='info' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('toast', rendered)
        self.assertIn('Toast message', rendered)


class ModalComponentTests(TestCase):
    """Test modal components."""

    def test_confirm_modal_renders(self):
        """Test confirm modal component."""
        template = Template(
            "{% load static %}"
            "{% include 'components/modals/confirm_modal.html' with "
            "modal_id='testModal' title='Confirm' message='Are you sure?' "
            "confirm_text='Yes' confirm_color='danger' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('modal', rendered)
        self.assertIn('testModal', rendered)
        self.assertIn('Confirm', rendered)
        self.assertIn('Are you sure?', rendered)

    def test_form_modal_renders(self):
        """Test form modal component."""
        template = Template(
            "{% load static %}"
            "{% include 'components/modals/form_modal.html' with "
            "modal_id='formModal' title='Form Title' %}"
        )
        rendered = template.render(Context({}))

        self.assertIn('modal', rendered)
        self.assertIn('formModal', rendered)
        self.assertIn('Form Title', rendered)


class DataTableComponentTests(TestCase):
    """Test data_table component with various data."""

    def test_data_table_renders_with_data(self):
        """Test data table renders with sample data."""
        headers = ['Name', 'Email', 'Role']
        data = [
            {'name': 'John Doe', 'email': 'john@test.com', 'role': 'Student'},
            {'name': 'Jane Smith', 'email': 'jane@test.com', 'role': 'Professor'},
        ]

        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/data_table.html' with "
            "table_id='testTable' headers=headers data=data %}"
        )
        rendered = template.render(Context({'headers': headers, 'data': data}))

        self.assertIn('table', rendered)
        self.assertIn('testTable', rendered)
        self.assertIn('Name', rendered)
        self.assertIn('Email', rendered)


class PaginationComponentTests(TestCase):
    """Test pagination component."""

    def test_pagination_renders(self):
        """Test pagination component with page object."""
        from django.core.paginator import Paginator

        items = list(range(1, 51))  # 50 items
        paginator = Paginator(items, 10)  # 10 per page
        page_obj = paginator.get_page(1)

        template = Template(
            "{% load static %}"
            "{% include 'components/widgets/pagination.html' with page_obj=page_obj %}"
        )
        rendered = template.render(Context({'page_obj': page_obj}))

        self.assertIn('pagination', rendered)


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests.test_components"])
