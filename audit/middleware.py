import threading

from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()


def get_current_user():
    """Get the current request user from thread-local storage."""
    user = getattr(_thread_locals, 'user', None)
    if user and user.is_authenticated:
        return user
    return None


class AuditUserMiddleware(MiddlewareMixin):
    """
    Stores the current request user in thread-local storage
    so AuditedModelMixin can access it without explicit user passing.

    Add to MIDDLEWARE after AuthenticationMiddleware.
    """

    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

    def process_response(self, request, response):
        _thread_locals.user = None
        return response
