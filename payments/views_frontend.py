import stripe
import uuid
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

try:
    import gopay
    from gopay.enums import Recurrence, PaymentInstrument, BankSwiftCode, Currency, Language
    GOPAY_AVAILABLE = True
except ImportError:
    GOPAY_AVAILABLE = False

from .models import Invoice


@login_required
def payment_paypal(request):
    return render(request, "payments/paypal.html", context={})


@login_required
def payment_stripe(request):
    return render(request, "payments/stripe.html", context={})


@login_required
def payment_coinbase(request):
    return render(request, "payments/coinbase.html", context={})


@login_required
def payment_paylike(request):
    return render(request, "payments/paylike.html", context={})


@login_required
def payment_succeed(request):
    return render(request, "payments/payment_succeed.html", context={})


@method_decorator(login_required, name='dispatch')
class PaymentGetwaysView(TemplateView):
    template_name = "payments/payment_gateways.html"

    def get_context_data(self, **kwargs):
        context = super(PaymentGetwaysView, self).get_context_data(**kwargs)
        context["key"] = settings.STRIPE_PUBLISHABLE_KEY
        invoice_code = self.request.session.get("invoice_session")
        invoice = None
        if invoice_code:
            invoice = Invoice.objects.filter(invoice_code=invoice_code).first()
        context["amount"] = int(invoice.amount * 100) if invoice and invoice.amount else 0
        context["description"] = "Stripe Payment"
        context["invoice_session"] = self.request.session.get("invoice_session", {})
        return context


@login_required
def stripe_charge(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        invoice_code = request.session.get("invoice_session")
        invoice = get_object_or_404(Invoice, invoice_code=invoice_code)
        # Verify the user owns this invoice or is a parent of the student
        if invoice.user != request.user and not request.user.is_superuser:
            from accounts.models import Parent
            is_parent_of_student = Parent.objects.filter(
                user=request.user, student__student=invoice.user
            ).exists()
            if not is_parent_of_student:
                messages.error(request, "You are not authorized to pay this invoice.")
                return redirect("frontend:payments:student_invoices")
        amount = int(invoice.amount * 100) if invoice.amount else 0
        charge = stripe.Charge.create(
            amount=amount,
            currency="eur",
            description=f"Payment for invoice {invoice.invoice_code}",
            source=request.POST["stripeToken"],
        )
        invoice.payment_complete = True
        invoice.save()
        return redirect("frontend:payments:completed")


@login_required
def gopay_charge(request):
    if not GOPAY_AVAILABLE:
        return JsonResponse({"error": "GoPay payment gateway is not configured"}, status=501)

    if request.method == "POST":
        user = request.user

        payments = gopay.payments(
            {
                "goid": "[PAYMENT_ID]",
                "clientId": "[GOPAY_CLIENT_ID]",
                "clientSecret": "[GOPAY_CLIENT_SECRET]",
                "isProductionMode": False,
                "scope": gopay.TokenScope.ALL,
                "language": gopay.Language.ENGLISH,
                "timeout": 30,
            }
        )

        recurrentPayment = {
            "recurrence": {
                "recurrence_cycle": Recurrence.DAILY,
                "recurrence_period": "7",
                "recurrence_date_to": "2015-12-31",
            }
        }

        preauthorizedPayment = {"preauthorization": True}

        response = payments.create_payment(
            {
                "payer": {
                    "default_payment_instrument": PaymentInstrument.BANK_ACCOUNT,
                    "allowed_payment_instruments": [PaymentInstrument.BANK_ACCOUNT],
                    "default_swift": BankSwiftCode.FIO_BANKA,
                    "allowed_swifts": [BankSwiftCode.FIO_BANKA, BankSwiftCode.MBANK],
                    "contact": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone,
                        "city": "example city",
                        "street": "Plana 67",
                        "postal_code": "373 01",
                        "country_code": "CZE",
                    },
                },
                "amount": 150,
                "currency": Currency.CZECH_CROWNS,
                "order_number": "001",
                "order_description": "pojisteni01",
                "items": [
                    {"name": "item01", "amount": 50},
                    {"name": "item02", "amount": 100},
                ],
                "additional_params": [{"name": "invoicenumber", "value": "2015001003"}],
                "callback": {
                    "return_url": "http://www.your-url.tld/return",
                    "notification_url": "http://www.your-url.tld/notify",
                },
                "lang": Language.CZECH,
            }
        )

        if response.has_succeed():
            pass
        return JsonResponse({"message": str(response)})

    return JsonResponse({"message": "GET requested"})


@login_required
def paymentComplete(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax or request.method == "POST":
        invoice_id = request.session["invoice_session"]
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.payment_complete = True
        invoice.save()
    body = json.loads(request.body)
    return JsonResponse("Payment completed!", safe=False)


@login_required
def create_invoice(request):
    if request.method == "POST":
        amount = request.POST.get("amount", 0)
        invoice = Invoice.objects.create(
            user=request.user,
            amount=amount,
            total=amount,
            invoice_code=str(uuid.uuid4()),
        )
        request.session["invoice_session"] = invoice.invoice_code
        return redirect("frontend:payments:payment_gateways")

    return render(
        request,
        "invoices.html",
        context={"invoices": Invoice.objects.filter(user=request.user)},
    )


@login_required
def invoice_detail(request, slug):
    return render(
        request,
        "invoice_detail.html",
        context={"invoice": get_object_or_404(Invoice, invoice_code=slug)},
    )


# ============================================================================
# Fee Structure CRUD (direction only)
# ============================================================================

from django.core.paginator import Paginator
from accounts.decorators import direction_only
from .models import FeeStructure, Payment
from .forms import FeeStructureForm


@login_required
@direction_only
def fee_structure_list(request):
    """List all fee structures (direction only)."""
    fee_structures = FeeStructure.objects.all().select_related('program').order_by(
        '-academic_year', 'program', 'level'
    )

    # Filter by active status
    active_filter = request.GET.get('active', '').strip()
    if active_filter == 'true':
        fee_structures = fee_structures.filter(is_active=True)
    elif active_filter == 'false':
        fee_structures = fee_structures.filter(is_active=False)

    # Search by academic year or program
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        fee_structures = fee_structures.filter(
            Q(academic_year__icontains=search) |
            Q(program__title__icontains=search)
        )

    paginator = Paginator(fee_structures, 20)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)

    return render(request, 'payments/fee_structure_list.html', {
        'fee_structures': page,
        'total_count': paginator.count,
        'search': search,
        'active_filter': active_filter,
        'page_title': _('Fee Structures'),
    })


@login_required
@direction_only
def fee_structure_create(request):
    """Create a new fee structure (direction only)."""
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Fee structure created successfully.'))
            return redirect('frontend:payments:fee_structure_list')
    else:
        form = FeeStructureForm()

    return render(request, 'payments/fee_structure_form.html', {
        'form': form,
        'form_title': _('Create Fee Structure'),
        'submit_text': _('Create'),
    })


@login_required
@direction_only
def fee_structure_edit(request, pk):
    """Edit an existing fee structure (direction only)."""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, _('Fee structure updated successfully.'))
            return redirect('frontend:payments:fee_structure_list')
    else:
        form = FeeStructureForm(instance=fee_structure)

    return render(request, 'payments/fee_structure_form.html', {
        'form': form,
        'fee_structure': fee_structure,
        'form_title': _('Edit Fee Structure'),
        'submit_text': _('Save Changes'),
    })


@login_required
@direction_only
def fee_structure_delete(request, pk):
    """Delete a fee structure (direction only). GET shows confirm, POST deletes."""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)

    if request.method == 'POST':
        fee_structure_name = str(fee_structure)
        fee_structure.delete()
        messages.success(
            request,
            _('Fee structure "%(name)s" deleted successfully.') % {'name': fee_structure_name}
        )
        return redirect('frontend:payments:fee_structure_list')

    return render(request, 'payments/fee_structure_confirm_delete.html', {
        'fee_structure': fee_structure,
        'page_title': _('Delete Fee Structure'),
    })


# ============================================================================
# Student Views
# ============================================================================

@login_required
def student_invoices(request):
    """List current user's invoices."""
    invoices = Invoice.objects.filter(
        user=request.user
    ).select_related('fee_structure', 'semester').order_by('-created_at')

    # Filter by payment status
    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'paid':
        invoices = invoices.filter(payment_complete=True)
    elif status_filter == 'unpaid':
        invoices = invoices.filter(payment_complete=False)

    paginator = Paginator(invoices, 20)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)

    return render(request, 'payments/student_invoices.html', {
        'invoices': page,
        'total_count': paginator.count,
        'status_filter': status_filter,
        'page_title': _('My Invoices'),
    })


@login_required
def student_payment_history(request):
    """List current user's completed payment transactions."""
    payments = Payment.objects.filter(
        invoice__user=request.user,
        status='completed'
    ).select_related('invoice').order_by('-payment_date')

    paginator = Paginator(payments, 20)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)

    return render(request, 'payments/payment_history.html', {
        'payments': page,
        'total_count': paginator.count,
        'page_title': _('Payment History'),
    })
