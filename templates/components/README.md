# Reusable Django Template Components

This directory contains reusable template components for the School Management System. All components are Bootstrap 5 compatible and use RemixIcon for icons.

## Directory Structure

```
components/
├── widgets/          # Display components (cards, charts, tables, badges, etc.)
├── forms/            # Form input components
├── modals/           # Modal dialog components
├── alerts/           # Alert and notification components
└── README.md         # This file
```

## Widget Components

### 1. Stat Card (`widgets/stat_card.html`)
Display statistical information with icons and optional trends.

**Usage:**
```django
{% include "components/widgets/stat_card.html" with
    label="Total Students"
    value="1,234"
    icon="ri-user-line"
    color="primary"
    trend="+12%"
    trend_direction="up"
    link="/students/"
%}
```

**Parameters:**
- `label` (required): Card label/title
- `value` (required): Main value to display
- `icon` (optional): RemixIcon class
- `color` (default: primary): primary|success|info|warning|danger
- `trend` (optional): Trend percentage
- `trend_direction` (optional): up|down
- `link` (optional): URL to navigate to on click

---

### 2. Info Card (`widgets/info_card.html`)
General-purpose card with header, body, and optional footer.

**Usage:**
```django
{% include "components/widgets/info_card.html" with
    title="Course Information"
    icon="ri-book-line"
    color="primary"
    collapsible=True
%}
```

---

### 3. Progress Card (`widgets/progress_card.html`)
Display progress with visual progress bar.

**Usage:**
```django
{% include "components/widgets/progress_card.html" with
    title="Course Completion"
    current=75
    total=100
    unit="%"
    color="success"
%}
```

---

### 4. Chart Card (`widgets/chart_card.html`)
ApexCharts integration for data visualization.

**Usage:**
```django
{% include "components/widgets/chart_card.html" with
    chart_id="attendance_chart"
    title="Attendance Overview"
    chart_type="donut"
    series="[75, 25]"
    labels="['Present', 'Absent']"
    colors="['#28a745', '#dc3545']"
%}
```

**Chart Types:**
- `line`: Line chart
- `bar`: Bar chart
- `area`: Area chart
- `donut`: Donut chart
- `pie`: Pie chart
- `radialBar`: Radial bar chart

---

### 5. Data Table (`widgets/data_table.html`)
DataTables.js integration with search, sort, and pagination.

**Usage:**
```django
{% include "components/widgets/data_table.html" with
    table_id="students_table"
    headers=headers_list
    searchable=True
    sortable=True
%}
```

---

### 6. Badge (`widgets/badge.html`)
Status badges and labels.

**Usage:**
```django
{% include "components/widgets/badge.html" with
    text="Active"
    color="success"
    icon="ri-checkbox-circle-line"
    pill=True
%}
```

---

### 7. Pagination (`widgets/pagination.html`)
Django paginator integration.

**Usage:**
```django
{% include "components/widgets/pagination.html" with
    page_obj=page_obj
    size="md"
    alignment="center"
%}
```

---

### 8. Empty State (`widgets/empty_state.html`)
Display when no data is available.

**Usage:**
```django
{% include "components/widgets/empty_state.html" with
    icon="ri-inbox-line"
    title="No Results Found"
    message="Try adjusting your search criteria"
    action_text="Create New"
    action_url="/create/"
%}
```

---

## Form Components

### 1. Text Input (`forms/text_input.html`)
Standard text input field.

**Usage:**
```django
{% include "components/forms/text_input.html" with
    name="email"
    label="Email Address"
    type="email"
    placeholder="Enter your email"
    required=True
    icon="ri-mail-line"
%}
```

**Input Types:**
- `text`: Plain text
- `email`: Email address
- `password`: Password field
- `number`: Numeric input
- `tel`: Telephone number
- `url`: URL field

---

### 2. Select Input (`forms/select_input.html`)
Dropdown select field.

**Usage:**
```django
{% include "components/forms/select_input.html" with
    name="level"
    label="Student Level"
    options=levels
    selected=student.level
    required=True
%}
```

---

### 3. Textarea Input (`forms/textarea_input.html`)
Multi-line text input.

**Usage:**
```django
{% include "components/forms/textarea_input.html" with
    name="description"
    label="Description"
    rows=5
    max_length=500
    show_counter=True
%}
```

---

### 4. Checkbox Input (`forms/checkbox_input.html`)
Checkbox or switch input.

**Usage:**
```django
{% include "components/forms/checkbox_input.html" with
    name="agree_terms"
    label="I agree to the terms"
    switch=True
    required=True
%}
```

---

## Modal Components

### 1. Confirm Modal (`modals/confirm_modal.html`)
Confirmation dialog for destructive actions.

**Usage:**
```django
{% include "components/modals/confirm_modal.html" with
    modal_id="deleteConfirm"
    title="Confirm Deletion"
    message="Are you sure you want to delete this item?"
    confirm_text="Delete"
    confirm_color="danger"
    action_url="/delete/123/"
%}
```

**Trigger Button:**
```html
<button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#deleteConfirm">
    Delete
</button>
```

---

### 2. Form Modal (`modals/form_modal.html`)
Modal with form for creating/editing records.

**Usage:**
```django
{% include "components/modals/form_modal.html" with
    modal_id="addStudent"
    title="Add New Student"
    form_action="/students/add/"
    submit_text="Add Student"
    size="lg"
%}
```

---

## Alert Components

### 1. Alert (`alerts/alert.html`)
Bootstrap alert messages.

**Usage:**
```django
{% include "components/alerts/alert.html" with
    type="success"
    title="Success"
    message="Operation completed successfully!"
    dismissible=True
    icon="ri-checkbox-circle-line"
    auto_dismiss=5000
%}
```

**Alert Types:**
- `success`: Green success message
- `info`: Blue informational message
- `warning`: Yellow warning message
- `danger`: Red error message
- `primary`: Primary color message

---

### 2. Toast (`alerts/toast.html`)
Temporary toast notifications.

**Usage:**
```django
{% include "components/alerts/toast.html" with
    toast_id="successToast"
    type="success"
    title="Success"
    message="Changes saved!"
    auto_hide=True
    delay=5000
    position="top-end"
%}
```

**Toast Positions:**
- `top-start`: Top left
- `top-center`: Top center
- `top-end`: Top right
- `bottom-start`: Bottom left
- `bottom-center`: Bottom center
- `bottom-end`: Bottom right

---

## Color Options

All components support Bootstrap 5 color variants:

- `primary`: Blue (#0d6efd)
- `secondary`: Gray (#6c757d)
- `success`: Green (#198754)
- `danger`: Red (#dc3545)
- `warning`: Yellow (#ffc107)
- `info`: Cyan (#0dcaf0)
- `light`: Light gray (#f8f9fa)
- `dark`: Dark gray (#212529)

---

## Icon System

Components use **RemixIcon** for icons. Common icons:

### Interface Icons
- `ri-home-line`: Home
- `ri-dashboard-line`: Dashboard
- `ri-settings-line`: Settings
- `ri-search-line`: Search
- `ri-close-line`: Close
- `ri-menu-line`: Menu

### User Icons
- `ri-user-line`: User
- `ri-user-add-line`: Add user
- `ri-group-line`: Group
- `ri-account-circle-line`: Account

### Education Icons
- `ri-book-line`: Book
- `ri-book-open-line`: Open book
- `ri-graduation-cap-line`: Graduation
- `ri-presentation-line`: Presentation

### Status Icons
- `ri-checkbox-circle-line`: Success
- `ri-error-warning-line`: Error/Warning
- `ri-information-line`: Information
- `ri-close-circle-line`: Close/Cancel

### Action Icons
- `ri-add-line`: Add
- `ri-delete-bin-line`: Delete
- `ri-edit-line`: Edit
- `ri-save-line`: Save
- `ri-download-line`: Download
- `ri-upload-line`: Upload

See full icon list at: https://remixicon.com/

---

## Best Practices

1. **Always include required parameters** - Components will not render properly without them
2. **Use consistent colors** - Stick to Bootstrap color variants for consistency
3. **Add meaningful icons** - Icons improve UX and visual hierarchy
4. **Provide helpful error messages** - Use the `error` parameter for form validation
5. **Test responsiveness** - All components are mobile-responsive by default
6. **Use semantic HTML** - Components generate accessible, semantic markup
7. **Combine components** - Mix and match components to build complex interfaces

---

## Examples

### Example 1: Student List Page
```django
{% extends "base_dashboard.html" %}
{% load i18n %}

{% block dashboard_content %}
<div class="container-fluid px-4 py-4">
    <!-- Page Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>{% trans "Students" %}</h2>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addStudent">
            <i class="ri-add-line me-2"></i>{% trans "Add Student" %}
        </button>
    </div>

    <!-- Statistics -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            {% include "components/widgets/stat_card.html" with
                label="Total Students"
                value=total_students
                icon="ri-user-line"
                color="primary"
            %}
        </div>
        <div class="col-md-3">
            {% include "components/widgets/stat_card.html" with
                label="Active"
                value=active_students
                icon="ri-checkbox-circle-line"
                color="success"
            %}
        </div>
    </div>

    <!-- Students Table -->
    <div class="card">
        <div class="card-body">
            {% include "components/widgets/data_table.html" with
                table_id="students_table"
                headers=headers
                data=students
            %}
        </div>
    </div>
</div>

<!-- Add Student Modal -->
{% include "components/modals/form_modal.html" with
    modal_id="addStudent"
    title="Add New Student"
    form_action="/students/add/"
%}
{% endblock %}
```

### Example 2: Course Detail Page
```django
{% extends "base_dashboard.html" %}

{% block dashboard_content %}
<div class="container-fluid px-4 py-4">
    <!-- Course Info Card -->
    {% include "components/widgets/info_card.html" with
        title=course.title
        icon="ri-book-open-line"
        color="primary"
    %}

    <!-- Progress -->
    {% include "components/widgets/progress_card.html" with
        title="Course Completion"
        current=completed_modules
        total=total_modules
        color="success"
    %}

    <!-- Attendance Chart -->
    {% include "components/widgets/chart_card.html" with
        chart_id="attendance_chart"
        title="Attendance"
        chart_type="donut"
        series=attendance_data
    %}
</div>
{% endblock %}
```

---

## Support

For questions or issues with components, please refer to:
- Bootstrap 5 Documentation: https://getbootstrap.com/docs/5.0
- RemixIcon: https://remixicon.com/
- ApexCharts: https://apexcharts.com/
- DataTables: https://datatables.net/
