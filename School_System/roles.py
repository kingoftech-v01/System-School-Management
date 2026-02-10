"""
Role-based permissions configuration using django-role-permissions.
This module defines the permission hierarchy for the school management system.
"""

from rolepermissions.roles import AbstractUserRole


class Student(AbstractUserRole):
    """Student role with basic read permissions."""
    available_permissions = {
        # Course & Academic
        'view_own_courses': True,
        'view_course_materials': True,
        'download_course_files': True,

        # Grades & Results
        'view_own_grades': True,
        'view_own_result': True,
        'view_own_transcript': True,
        'request_grade_appeal': True,

        # Attendance
        'view_own_attendance': True,

        # Quizzes & Assignments
        'take_quizzes': True,
        'submit_assignments': True,
        'view_quiz_results': True,

        # Payments
        'view_own_invoices': True,
        'make_payments': True,

        # Library
        'borrow_books': True,
        'view_library_catalog': True,

        # Articles & Notices
        'view_published_articles': True,
        'comment_on_articles': True,
        'view_notices': True,
        'acknowledge_notices': True,

        # Profile
        'update_own_profile': True,
        'view_own_profile': True,
    }


class Parent(AbstractUserRole):
    """Parent role with read-only access to their child's information."""
    available_permissions = {
        # Student monitoring
        'view_child_grades': True,
        'view_child_attendance': True,
        'view_child_courses': True,
        'view_child_invoices': True,
        'view_child_result': True,

        # Communication
        'view_published_articles': True,
        'view_notices': True,
        'acknowledge_notices': True,

        # Payments
        'make_payments_for_child': True,

        # Profile
        'update_own_profile': True,
        'view_own_profile': True,
    }


class Professor(AbstractUserRole):
    """Professor role with course management and grading permissions."""
    available_permissions = {
        # Course Management
        'manage_assigned_courses': True,
        'upload_course_materials': True,
        'upload_course_videos': True,
        'edit_course_content': True,

        # Grading & Assessment
        'grade_students': True,
        'create_quizzes': True,
        'create_assignments': True,
        'enter_grades': True,
        'submit_grades': True,
        'view_all_student_results': True,
        'review_grade_appeals': True,

        # Attendance
        'mark_attendance': True,
        'view_attendance_reports': True,
        'generate_attendance_stats': True,

        # Student Management
        'view_assigned_students': True,
        'view_student_profiles': True,

        # Articles & Content
        'create_articles': True,
        'edit_own_articles': True,
        'publish_articles': True,

        # Notices
        'view_notices': True,
        'create_notices': True,

        # Library
        'view_library_catalog': True,
        'borrow_books': True,

        # Profile
        'update_own_profile': True,
        'view_own_profile': True,
    }


class Direction(AbstractUserRole):
    """Direction/management role with administrative oversight."""
    available_permissions = {
        # Academic Administration
        'manage_departments': True,
        'manage_programs': True,
        'manage_courses': True,
        'assign_courses_to_professors': True,
        'view_all_courses': True,

        # Student Administration
        'view_all_students': True,
        'approve_registrations': True,
        'manage_enrollments': True,
        'transfer_students': True,
        'mark_students_as_alumni': True,
        'manage_admissions': True,
        'assign_student_ids': True,

        # Faculty Management
        'view_all_faculty': True,
        'manage_faculty_assignments': True,

        # Reports & Analytics
        'view_all_reports': True,
        'generate_financial_reports': True,
        'generate_academic_reports': True,
        'view_dashboards': True,
        'export_data': True,

        # Grading & Results
        'view_all_grades': True,
        'approve_grades': True,
        'resolve_grade_appeals': True,
        'generate_transcripts': True,

        # Attendance
        'view_all_attendance': True,
        'generate_attendance_reports': True,

        # Payments & Finance
        'view_all_invoices': True,
        'manage_fee_structures': True,
        'verify_payments': True,
        'create_payment_plans': True,
        'generate_receipts': True,

        # Library Management
        'manage_library': True,
        'add_books': True,
        'view_borrow_records': True,

        # Content Management
        'create_articles': True,
        'edit_all_articles': True,
        'publish_articles': True,
        'moderate_comments': True,
        'manage_categories': True,

        # Notice Management
        'create_notices': True,
        'edit_all_notices': True,
        'delete_notices': True,
        'view_notice_acknowledgments': True,

        # Admissions
        'manage_admissions': True,
        'review_applications': True,
        'assign_counselors': True,
        'approve_admissions': True,

        # Alumni Management
        'manage_alumni': True,
        'create_alumni_events': True,
        'track_alumni_donations': True,

        # Discipline
        'view_disciplinary_records': True,
        'create_disciplinary_actions': True,

        # Events
        'manage_events': True,

        # Profile
        'update_own_profile': True,
        'view_own_profile': True,
        'view_all_profiles': True,
    }


class Secretary(AbstractUserRole):
    """Secretary role with direction-level access except financial features."""
    available_permissions = {
        # Academic Administration
        'manage_departments': True,
        'manage_programs': True,
        'manage_courses': True,
        'assign_courses_to_professors': True,
        'view_all_courses': True,

        # Student Administration
        'view_all_students': True,
        'approve_registrations': True,
        'manage_enrollments': True,
        'transfer_students': True,
        'mark_students_as_alumni': True,
        'manage_admissions': True,
        'assign_student_ids': True,

        # Faculty Management
        'view_all_faculty': True,
        'manage_faculty_assignments': True,

        # Reports & Analytics (no financial reports)
        'view_all_reports': True,
        'generate_academic_reports': True,
        'view_dashboards': True,
        'export_data': True,

        # Grading & Results
        'view_all_grades': True,
        'approve_grades': True,
        'resolve_grade_appeals': True,
        'generate_transcripts': True,

        # Attendance
        'view_all_attendance': True,
        'generate_attendance_reports': True,

        # Library Management
        'manage_library': True,
        'add_books': True,
        'view_borrow_records': True,

        # Content Management
        'create_articles': True,
        'edit_all_articles': True,
        'publish_articles': True,
        'moderate_comments': True,
        'manage_categories': True,

        # Notice Management
        'create_notices': True,
        'edit_all_notices': True,
        'delete_notices': True,
        'view_notice_acknowledgments': True,

        # Admissions
        'manage_admissions': True,
        'review_applications': True,
        'assign_counselors': True,
        'approve_admissions': True,

        # Alumni Management
        'manage_alumni': True,
        'create_alumni_events': True,
        'track_alumni_donations': True,

        # Discipline
        'view_disciplinary_records': True,
        'create_disciplinary_actions': True,

        # Events
        'manage_events': True,

        # Profile
        'update_own_profile': True,
        'view_own_profile': True,
        'view_all_profiles': True,
    }


class Admin(AbstractUserRole):
    """System administrator with full access."""
    available_permissions = {
        # Full system access
        'full_access': True,

        # User Management
        'create_users': True,
        'edit_users': True,
        'delete_users': True,
        'approve_user_accounts': True,
        'assign_roles': True,
        'reset_passwords': True,

        # System Configuration
        'configure_system': True,
        'manage_settings': True,
        'manage_tenants': True,
        'view_logs': True,

        # All permissions from Direction role
        **Direction.available_permissions,

        # Additional admin-only permissions
        'manage_celery_tasks': True,
        'view_error_logs': True,
        'execute_migrations': True,
        'backup_database': True,
        'restore_database': True,
    }
