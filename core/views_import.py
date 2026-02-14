"""
Generic data import views for direction/admin users.
Uses django-import-export for CSV/Excel data import with preview.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from import_export.formats.base_formats import CSV, XLSX
from tablib import Dataset

from accounts.decorators import direction_only

logger = logging.getLogger(__name__)

# Map of import types to their resource classes
IMPORT_RESOURCES = {
    'students': {
        'label': 'Students',
        'resource_class': 'accounts.resources.StudentResource',
        'sample_headers': 'registration_number,first_name,last_name,email,level,program',
    },
    'courses': {
        'label': 'Courses',
        'resource_class': 'course.resources.CourseResource',
        'sample_headers': 'code,title,credit,program,level,year,semester,is_elective',
    },
    'programs': {
        'label': 'Programs',
        'resource_class': 'course.resources.ProgramResource',
        'sample_headers': 'title,summary',
    },
}


def _get_resource(import_type):
    """Dynamically import and return the resource class."""
    config = IMPORT_RESOURCES.get(import_type)
    if not config:
        return None
    module_path, class_name = config['resource_class'].rsplit('.', 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


@login_required
@direction_only
def import_select(request):
    """Step 1: Select what to import."""
    return render(request, 'import/import_wizard.html', {
        'step': 'select',
        'import_types': IMPORT_RESOURCES,
    })


@login_required
@direction_only
def import_upload(request, import_type):
    """Step 2: Upload file and preview."""
    config = IMPORT_RESOURCES.get(import_type)
    if not config:
        messages.error(request, _('Invalid import type.'))
        return redirect('frontend:core:import_select')

    if request.method == 'POST' and request.FILES.get('import_file'):
        uploaded_file = request.FILES['import_file']
        file_name = uploaded_file.name.lower()

        try:
            if file_name.endswith('.csv'):
                data = uploaded_file.read().decode('utf-8')
                dataset = Dataset().load(data, format='csv')
            elif file_name.endswith(('.xlsx', '.xls')):
                data = uploaded_file.read()
                dataset = Dataset().load(data, format='xlsx')
            else:
                messages.error(request, _('Unsupported file format. Use CSV or XLSX.'))
                return redirect('frontend:core:import_upload', import_type=import_type)

            resource = _get_resource(import_type)
            result = resource.import_data(dataset, dry_run=True)

            # Store dataset in session for confirmation
            request.session['import_data'] = dataset.export('json')
            request.session['import_type'] = import_type

            return render(request, 'import/import_wizard.html', {
                'step': 'preview',
                'import_type': import_type,
                'config': config,
                'result': result,
                'dataset': dataset,
                'headers': dataset.headers,
                'total_rows': len(dataset),
                'new_count': result.totals.get('new', 0),
                'update_count': result.totals.get('update', 0),
                'skip_count': result.totals.get('skip', 0),
                'error_count': result.totals.get('error', 0),
                'has_errors': result.has_errors(),
            })

        except Exception as e:
            logger.exception("Import preview failed")
            messages.error(request, _(f'Error reading file: {e}'))
            return redirect('frontend:core:import_upload', import_type=import_type)

    return render(request, 'import/import_wizard.html', {
        'step': 'upload',
        'import_type': import_type,
        'config': config,
    })


@login_required
@direction_only
def import_confirm(request, import_type):
    """Step 3: Confirm and execute import."""
    if request.method != 'POST':
        return redirect('frontend:core:import_select')

    stored_type = request.session.get('import_type')
    stored_data = request.session.get('import_data')

    if stored_type != import_type or not stored_data:
        messages.error(request, _('Import session expired. Please start over.'))
        return redirect('frontend:core:import_select')

    try:
        dataset = Dataset().load(stored_data, format='json')
        resource = _get_resource(import_type)
        result = resource.import_data(dataset, dry_run=False)

        # Clean up session
        del request.session['import_data']
        del request.session['import_type']

        if result.has_errors():
            messages.warning(request, _(
                f'Import completed with errors. '
                f'New: {result.totals.get("new", 0)}, '
                f'Updated: {result.totals.get("update", 0)}, '
                f'Errors: {result.totals.get("error", 0)}'
            ))
        else:
            messages.success(request, _(
                f'Import successful! '
                f'New: {result.totals.get("new", 0)}, '
                f'Updated: {result.totals.get("update", 0)}'
            ))

    except Exception as e:
        logger.exception("Import execution failed")
        messages.error(request, _(f'Import failed: {e}'))

    return redirect('frontend:core:import_select')
