from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from mptt.models import MPTTModel, TreeForeignKey


def validate_isbn(value):
    """Validate ISBN-10 or ISBN-13."""
    # Remove hyphens and spaces
    isbn = value.replace('-', '').replace(' ', '')

    if len(isbn) == 10:
        # ISBN-10 validation
        if not isbn[:-1].isdigit():
            raise ValidationError(_('ISBN-10 must contain only digits except for the last character'))
        try:
            check_sum = sum((i + 1) * int(digit) for i, digit in enumerate(isbn[:-1]))
            check_digit = (11 - (check_sum % 11)) % 11
            if check_digit == 10:
                check_char = 'X'
            else:
                check_char = str(check_digit)
            if isbn[-1].upper() != check_char:
                raise ValidationError(_('Invalid ISBN-10 check digit'))
        except (ValueError, IndexError):
            raise ValidationError(_('Invalid ISBN-10 format'))

    elif len(isbn) == 13:
        # ISBN-13 validation
        if not isbn.isdigit():
            raise ValidationError(_('ISBN-13 must contain only digits'))
        try:
            check_sum = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(isbn[:-1]))
            check_digit = (10 - (check_sum % 10)) % 10
            if int(isbn[-1]) != check_digit:
                raise ValidationError(_('Invalid ISBN-13 check digit'))
        except (ValueError, IndexError):
            raise ValidationError(_('Invalid ISBN-13 format'))
    else:
        raise ValidationError(_('ISBN must be 10 or 13 characters long'))


class BookCategory(MPTTModel):
    """Hierarchical book categorization using MPTT."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Category Name'))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Parent Category')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('Book Category')
        verbose_name_plural = _('Book Categories')

    def __str__(self):
        return self.name

    def get_book_count(self):
        """Get total books in this category and subcategories."""
        return Book.objects.filter(category=self).count() + \
            sum(sub.get_book_count() for sub in self.subcategories.all())


class Publisher(models.Model):
    """Publisher database for better organization."""
    name = models.CharField(max_length=200, unique=True, verbose_name=_('Publisher Name'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('Country'))
    website = models.URLField(blank=True, verbose_name=_('Website'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Publisher')
        verbose_name_plural = _('Publishers')

    def __str__(self):
        return self.name


class Book(models.Model):
    """Book inventory."""

    tenant = models.ForeignKey('core.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=300, verbose_name=_('Title'))
    author = models.CharField(max_length=200, verbose_name=_('Author'))

    # Enhanced ISBN with validation
    isbn = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('ISBN'),
        validators=[validate_isbn],
        help_text=_('ISBN-10 or ISBN-13')
    )

    filiere = models.ForeignKey('filieres.Filiere', on_delete=models.SET_NULL, null=True, blank=True)

    # Changed to ForeignKey for hierarchical categories
    category = TreeForeignKey(
        BookCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name=_('Category')
    )

    # Enhanced publisher as ForeignKey
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name=_('Publisher')
    )

    publication_year = models.IntegerField(null=True, blank=True)

    # NEW: Edition tracking
    edition = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Edition'),
        help_text=_('e.g., 1st, 2nd, Revised, etc.')
    )
    language = models.CharField(
        max_length=50,
        blank=True,
        default='English',
        verbose_name=_('Language')
    )
    pages = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Number of Pages')
    )

    # NEW: Barcode/RFID support
    barcode = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Barcode'),
        help_text=_('Barcode or RFID tag number')
    )

    quantity = models.IntegerField(default=1, verbose_name=_('Total Quantity'))
    available = models.IntegerField(default=1, verbose_name=_('Available Copies'))
    shelf_location = models.CharField(max_length=50, blank=True)

    # Additional metadata
    cover_image = models.ImageField(
        upload_to='library/covers/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Cover Image')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Comma-separated tags for searching')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('Book')
        verbose_name_plural = _('Books')
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['barcode']),
            models.Index(fields=['category', 'title']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    def is_available(self):
        """Check if book has available copies."""
        return self.available > 0

    def borrow(self):
        """Decrease available copies when borrowed."""
        if self.available > 0:
            self.available -= 1
            self.save(update_fields=['available'])
            return True
        return False

    def return_book(self):
        """Increase available copies when returned."""
        if self.available < self.quantity:
            self.available += 1
            self.save(update_fields=['available'])
            return True
        return False


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
