"""Custom context processor for W3CRM theme variables."""


def dz_static(request):
    """Return theme configuration for templates."""
    return {'dz_array': {}}
