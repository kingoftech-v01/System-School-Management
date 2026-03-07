import logging
from django import template
from django.urls import resolve
from django.urls.exceptions import Resolver404

logger = logging.getLogger(__name__)
register = template.Library()


@register.filter('getdata')
def getdata(json_data, args):
    """Resolve URL path to view function name and look up page-level assets."""
    func_name = ''
    try:
        myfunc, myargs, mykwargs = resolve(args)
        if myfunc:
            func_name = myfunc.__name__
    except Resolver404:
        pass

    return json_data.get(func_name, [])
