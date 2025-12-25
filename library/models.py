from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class Book(models.Model):
    """Book inventory."""

    tenant = models.ForeignKey('core.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=300, verbose_name=_('Title'))
    author = models.CharField(max_length=200, verbose_name=_('Author'))
    isbn = models.CharField(max_length=20, unique=True, verbose_name=_('ISBN'))
    filiere = models.ForeignKey('filieres.Filiere', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=100, verbose_name=_('Category'))
    publisher = models.CharField(max_length=200, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=1, verbose_name=_('Total Quantity'))
    available = models.IntegerField(default=1, verbose_name=_('Available Copies'))
    shelf_location = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    def __str__(self):
        return f"{self.title} by {self.author}"


class BorrowRecord(models.Model):
    """Book borrowing records."""

    STATUS_CHOICES = (
        ('borrowed', _('Borrowed')),
        ('returned', _('Returned')),
        ('overdue', _('Overdue')),
        ('lost', _('Lost')),
    )

    tenant = models.ForeignKey('core.School', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-borrowed_at']
        verbose_name = _('Borrow Record')
        verbose_name_plural = _('Borrow Records')

    def __str__(self):
        return f"{self.student} - {self.book.title}"

    def is_overdue(self):
        if self.status == 'borrowed' and self.due_date < datetime.now().date():
            return True
        return False
