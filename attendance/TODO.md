# Attendance - TODO

## Bugs

- [ ] **`Satus` typo** (models.py:94) -- The `TextChoices` enum is named `Satus` instead of `Status`. This typo propagates to every file that imports it (`views_frontend.py`, `serializers.py`). Renaming requires a migration since the choices are stored as string values in the database.
- [ ] **`tasks.py` imports non-existent model** (tasks.py:10) -- `from .models import AttendanceRecord` fails at runtime because the model is named `AttendanceReport`, not `AttendanceRecord`. This prevents all three Celery tasks from loading.
- [ ] **`StudentSerializer.create()` logic error** (serializers.py:36) -- Uses `group['name']` as the argument to `Group.objects.get(id=...)`. Should use `group['id']` or look up by name with `Group.objects.get(name=group['name'])`. Creating students via the API will raise a `Group.DoesNotExist` or return the wrong group.
- [ ] **`IsTeacher.has_object_permission` compares user to model instance** (permissions.py:29) -- `return request.user == obj` compares the User to whatever object is passed (Attendance, Subject, etc.) instead of comparing to `obj.teacher` or `obj.subject.teacher`. Object-level permission checks always return `False` for lecturers.
- [ ] **`Student.fetch_attendance()` queries wrong model** (models.py:27) -- Filters `Attendance.objects.filter(student=self)` but `Attendance` has no `student` field; it should query `AttendanceReport.objects.filter(student=self)` or use `self.attendance_reports.all()`.
- [ ] **`Student.load_students_from_csv()` decode error** (models.py:30-34) -- Calls `.decode('utf-8')` on a `csv.reader` object (which has no `decode` method). Also hardcodes the filename `student.csv` instead of using the `file` parameter.
- [ ] **`StudentViewSet.attendances` action variable shadowing** (views_api.py:19-29) -- The local variable `status` (from `request.query_params.get('status')`) shadows the imported `status` module from DRF. When `status` is `None`, `status.HTTP_200_OK` on line 29 raises `AttributeError`.
- [ ] **`AttendanceViewSet.reports` paginates wrong queryset** (views_api.py:83-84) -- Calls `self.paginate_queryset(queryset)` but then passes the original `queryset` to the serializer instead of `page`. Paginated responses contain all items instead of the paginated subset.
- [ ] **`attendance.Student` duplicates `accounts.Student`** -- Two separate Student models exist in the system. The `student_attendance_report` view bridges them by email address comparison, which is fragile and can desync.

## Backend

- [ ] Implement `send_attendance_reminders` Celery task (tasks.py:15) -- Stub only; should query professors who haven't marked attendance today and send email reminders
- [ ] Implement `generate_daily_attendance_stats` Celery task (tasks.py:25) -- Stub only; should call `DailyAttendanceStat.generate_for_date()` nightly
- [ ] Implement `send_low_attendance_alerts` Celery task (tasks.py:34) -- Stub only; should use `Student.has_low_attendance()` and notify students/parents
- [ ] Add `AttendanceForm.__init__` subject filtering -- The form accepts a `lecturer` kwarg but never uses it to filter the `subject` queryset; any teacher can select any subject
- [ ] Add duplicate session prevention in `take_attendance` -- No check prevents creating two attendance sessions for the same subject and date via the frontend (the API serializer checks this, but the form does not)
- [ ] Add `@lecturer_required` or `@role_required` to `subject_list` view -- Currently only uses `@login_required` and `@tenant_required`; any authenticated user can view subjects
- [ ] Add module docstring to `models.py` (217 lines, no module docstring)
- [ ] Consider merging `attendance.Student` with `accounts.Student` or adding a foreign key relationship instead of email-based matching

## Frontend

- [ ] Add attendance percentage column to student list page
- [ ] Add date range filter to student attendance report page
- [ ] Add CSV/Excel export for attendance reports
- [ ] Add bulk import UI for `Student.load_students_from_csv()` (after fixing the bug)

## Sidebar

- [ ] Add "Student Reports" link to Attendance submenu -- currently no way to navigate to reports from the sidebar
- [ ] Add "Groups" link to Attendance submenu -- `group_list` exists but is not in the sidebar
- [ ] Add "Subjects" link to Attendance submenu -- `subject_list` exists but is not in the sidebar

## Security

- [ ] Rate limiting on `take_attendance` (views_frontend.py:77) only protects POST, not GET -- add `@ratelimit` to GET as well or move decorator above `method='POST'`
- [ ] `AttendanceReportViewSet` uses `IsAuthenticatedOrReadOnly` -- unauthenticated users can read all attendance reports via the API; consider restricting to `IsAuthenticated`
- [ ] `SubjectViewSet` uses `IsAdminUser` but `StudentViewSet` and `GroupViewSet` have no permission classes -- any authenticated user can read all students and groups via the API
- [ ] `student_attendance_report` has no `@role_required` decorator -- relies on manual role checking inside the view body; should use the decorator for consistency
- [ ] `attendance_detail` uses `@lecturer_required` instead of `@role_required` -- prefet, secretary, and direction users who can create sessions cannot view them via this view

## Tests

- [ ] Add test coverage for `DailyAttendanceStat.calculate_stats()` and `generate_for_date()`
- [ ] Add test for student attendance report permission check (student viewing another student's report)
- [ ] Add API tests for `AttendanceViewSet.date` action with malformed date input
- [ ] Add test for `StudentViewSet.attendances` action with status filter (currently broken by variable shadowing bug)

## Unnecessary Files

- [ ] None identified
