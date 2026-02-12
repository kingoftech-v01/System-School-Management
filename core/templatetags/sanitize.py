import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = {
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr',
    'strong', 'em', 'u', 's', 'sub', 'sup', 'blockquote', 'pre',
    'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span', 'div',
}

ALLOWED_ATTRIBUTES = {
    'a': {'href', 'target', 'rel'},
    'img': {'src', 'alt', 'width', 'height'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
    'span': {'style'},
    'div': {'style'},
}


@register.filter(name='sanitize')
def sanitize_html(value):
    """Sanitize HTML content using nh3, then mark safe for rendering."""
    if not value:
        return ''
    clean = nh3.clean(
        str(value),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel='noopener noreferrer',
    )
    return mark_safe(clean)
