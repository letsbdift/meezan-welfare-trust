import json
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.urls import reverse

from .models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification
)
from .forms import (
    DonationForm, InitiativeForm, EventForm,
    MaintenanceExpenseForm, TrusteeForm
)
from .razorpay_service import razorpay_service
from .whatsapp_service import whatsapp_service


def get_donation_metrics():
    """
    Computes real-time donation metrics:
    - Expected Amount: Sum of active initiative target amounts + outstanding pledged donations
    - Raised Amount: Total successful donations
    - Pending Amount: Remaining target needed + outstanding pledges
    """
    total_raised_agg = Donation.objects.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total']
    total_raised = total_raised_agg or Decimal('0.00')

    active_initiatives = Initiative.objects.filter(is_active=True)
    initiative_target_agg = active_initiatives.aggregate(total=Sum('target_amount'))['total']
    initiative_targets = initiative_target_agg or Decimal('0.00')

    pending_pledges_agg = Donation.objects.filter(status='PENDING', is_pledge=True).aggregate(total=Sum('amount'))['total']
    pending_pledges = pending_pledges_agg or Decimal('0.00')

    all_pending_donations_agg = Donation.objects.filter(status='PENDING').aggregate(total=Sum('amount'))['total']
    all_pending_donations = all_pending_donations_agg or Decimal('0.00')

    # Total Expected = Total targets set for current initiatives + pending pledges
    total_expected = initiative_targets + pending_pledges

    # Total Pending = Gap between initiative targets & raised + pending pledges
    target_gap = max(Decimal('0.00'), initiative_targets - total_raised)
    total_pending = target_gap + pending_pledges

    progress_percentage = 0.0
    if total_expected > 0:
        progress_percentage = min(round(float((total_raised / total_expected) * 100), 1), 100.0)

    return {
        'total_expected': total_expected,
        'total_raised': total_raised,
        'total_pending': total_pending,
        'pending_pledges': pending_pledges,
        'all_pending_donations': all_pending_donations,
        'progress_percentage': progress_percentage,
        'active_initiatives_count': active_initiatives.count(),
        'donor_count': Donor.objects.count(),
        'total_donations_count': Donation.objects.filter(status='SUCCESS').count(),
    }


def home(request):
    """Public home page with mission, metrics ticker, featured campaigns, events, and trustees."""
    metrics = get_donation_metrics()
    featured_initiatives = Initiative.objects.filter(is_active=True).order_by('-is_featured', '-created_at')[:3]
    upcoming_events = Event.objects.filter(event_date__gte=timezone.now()).order_by('event_date')[:3]
    trustees = Trustee.objects.filter(is_active=True).order_by('order', 'name')[:4]
    
    # Recent maintenance activity teaser (current month)
    current_month = timezone.now().month
    current_year = timezone.now().year
    current_expenses = MaintenanceExpense.objects.filter(month=current_month, year=current_year)
    current_month_total = current_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    recent_donors = Donation.objects.filter(status='SUCCESS').order_by('-created_at')[:5]

    context = {
        'metrics': metrics,
        'featured_initiatives': featured_initiatives,
        'upcoming_events': upcoming_events,
        'trustees': trustees,
        'current_month_total': current_month_total,
        'current_month_name': timezone.now().strftime('%B %Y'),
        'recent_donors': recent_donors,
        'donation_form': DonationForm(),
    }
    return render(request, 'core/home.html', context)


def dashboard(request):
    """
    Dynamic Trust Dashboard tracking donation metrics:
    - Expected, Raised, and Pending amounts
    - Visual Chart.js analytics
    - Maintenance expense breakdowns
    - Pending donations with WhatsApp Reminder trigger
    - WhatsApp broadcast controls
    """
    metrics = get_donation_metrics()

    # Initiatives breakdown
    initiatives = Initiative.objects.all().order_by('-is_active', '-target_amount')
    
    # Chart 1: Expected vs Raised vs Pending
    chart_metric_labels = ['Raised Amount (₹)', 'Pending Amount (₹)', 'Expected Target (₹)']
    chart_metric_data = [
        float(metrics['total_raised']),
        float(metrics['total_pending']),
        float(metrics['total_expected'])
    ]

    # Chart 2: Monthly donation trend (last 12 months)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_year = timezone.now().year
    monthly_raised = []
    for m in range(1, 13):
        raised_m = Donation.objects.filter(
            status='SUCCESS',
            created_at__year=current_year,
            created_at__month=m
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_raised.append(float(raised_m))

    # Chart 3: Maintenance expenses by category for current month
    curr_month = timezone.now().month
    categories = MaintenanceActivity.objects.all()
    expense_categories = []
    expense_category_amounts = []
    expense_category_colors = []

    for cat in categories:
        cat_sum = MaintenanceExpense.objects.filter(
            activity=cat,
            month=curr_month,
            year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        if cat_sum > 0:
            expense_categories.append(cat.name)
            expense_category_amounts.append(float(cat_sum))
            expense_category_colors.append(cat.color_hex)

    # If current month has no expenses yet, load from any latest month with data
    if not expense_categories:
        latest_expense = MaintenanceExpense.objects.order_by('-year', '-month').first()
        if latest_expense:
            curr_month = latest_expense.month
            current_year = latest_expense.year
            for cat in categories:
                cat_sum = MaintenanceExpense.objects.filter(
                    activity=cat,
                    month=curr_month,
                    year=current_year
                ).aggregate(total=Sum('amount'))['total'] or 0
                if cat_sum > 0:
                    expense_categories.append(cat.name)
                    expense_category_amounts.append(float(cat_sum))
                    expense_category_colors.append(cat.color_hex)

    # Pending donations / pledges for automated follow-up
    pending_donations = Donation.objects.filter(status='PENDING').order_by('-created_at')[:10]

    # Recent successful donations
    recent_donations = Donation.objects.filter(status='SUCCESS').order_by('-created_at')[:10]

    # Upcoming events for quick broadcast
    upcoming_events = Event.objects.filter(status='UPCOMING').order_by('event_date')

    # WhatsApp Notifications stats
    wa_stats = {
        'total_sent': WhatsAppNotification.objects.filter(status='SENT').count(),
        'reminders_sent': WhatsAppNotification.objects.filter(notification_type='PAYMENT_REMINDER').count(),
        'ads_sent': WhatsAppNotification.objects.filter(notification_type='EVENT_ADVERTISEMENT').count(),
    }

    context = {
        'metrics': metrics,
        'initiatives': initiatives,
        'chart_metric_labels': json.dumps(chart_metric_labels),
        'chart_metric_data': json.dumps(chart_metric_data),
        'month_names': json.dumps(month_names),
        'monthly_raised': json.dumps(monthly_raised),
        'expense_categories': json.dumps(expense_categories),
        'expense_category_amounts': json.dumps(expense_category_amounts),
        'expense_category_colors': json.dumps(expense_category_colors),
        'curr_month_name': datetime(2000, curr_month, 1).strftime('%B'),
        'curr_year': current_year,
        'pending_donations': pending_donations,
        'recent_donations': recent_donations,
        'upcoming_events': upcoming_events,
        'wa_stats': wa_stats,
    }
    return render(request, 'core/dashboard.html', context)


def initiatives_list(request):
    """Browse all charitable initiatives and causes with filter by category."""
    category = request.GET.get('category', '')
    initiatives = Initiative.objects.all()
    if category:
        initiatives = initiatives.filter(category=category)

    categories = Initiative.CATEGORY_CHOICES
    return render(request, 'core/initiatives_list.html', {
        'initiatives': initiatives,
        'categories': categories,
        'selected_category': category,
        'metrics': get_donation_metrics(),
    })


def initiative_detail(request, slug):
    """Detailed view of a single initiative with photo gallery, progress, and donation box."""
    initiative = get_object_or_404(Initiative, slug=slug)
    recent_donations = initiative.donations.filter(status='SUCCESS').order_by('-created_at')[:6]
    form = DonationForm(initial={'initiative': initiative})
    return render(request, 'core/initiative_detail.html', {
        'initiative': initiative,
        'recent_donations': recent_donations,
        'form': form,
    })


def events_list(request):
    """List upcoming and past trust events."""
    now = timezone.now()
    upcoming = Event.objects.filter(event_date__gte=now).order_by('event_date')
    past = Event.objects.filter(event_date__lt=now).order_by('-event_date')
    return render(request, 'core/events_list.html', {
        'upcoming_events': upcoming,
        'past_events': past,
    })


def event_detail(request, slug):
    """Event detail view with RSVP, venue details, and WhatsApp sharing."""
    event = get_object_or_404(Event, slug=slug)
    donors_count = Donor.objects.count()
    return render(request, 'core/event_detail.html', {
        'event': event,
        'donors_count': donors_count,
    })


def trustees_list(request):
    """Dedicated section for Trustee Profiles with bios, photos, and social media links."""
    trustees = Trustee.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'core/trustees_list.html', {
        'trustees': trustees,
    })


def maintenance_costs(request):
    """
    Monthly maintenance cost breakdowns per activity:
    - Filterable by month and year
    - Itemized expenses per activity
    - Chart breakdown showing expenditure distribution
    """
    current_date = timezone.now()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))

    activities = MaintenanceActivity.objects.all()
    expenses = MaintenanceExpense.objects.filter(month=selected_month, year=selected_year).select_related('activity')
    
    total_month_spent = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Activity breakdown data
    breakdown = []
    chart_labels = []
    chart_amounts = []
    chart_colors = []

    for act in activities:
        act_expenses = expenses.filter(activity=act)
        act_sum = act_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        percentage = 0.0
        if total_month_spent > 0:
            percentage = round(float((act_sum / total_month_spent) * 100), 1)

        breakdown.append({
            'activity': act,
            'amount': act_sum,
            'percentage': percentage,
            'expense_count': act_expenses.count(),
        })

        if act_sum > 0:
            chart_labels.append(act.name)
            chart_amounts.append(float(act_sum))
            chart_colors.append(act.color_hex)

    months_list = MaintenanceExpense.MONTH_CHOICES
    years_list = [2024, 2025, 2026, 2027]

    context = {
        'selected_month': selected_month,
        'selected_month_name': datetime(2000, selected_month, 1).strftime('%B'),
        'selected_year': selected_year,
        'months_list': months_list,
        'years_list': years_list,
        'total_month_spent': total_month_spent,
        'breakdown': breakdown,
        'expenses': expenses,
        'chart_labels': json.dumps(chart_labels),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_colors': json.dumps(chart_colors),
    }
    return render(request, 'core/maintenance_costs.html', context)


def donate(request):
    """General donation page with RazorPay payment initiation."""
    initiative_id = request.GET.get('initiative')
    initial = {}
    selected_initiative = None
    if initiative_id:
        try:
            selected_initiative = Initiative.objects.get(id=initiative_id)
            initial['initiative'] = selected_initiative
        except Initiative.DoesNotExist:
            pass

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            
            # Handle custom amount if selected
            custom_amt = form.cleaned_data.get('custom_amount')
            if custom_amt and custom_amt > 0:
                donation.amount = custom_amt

            # Link or create donor record
            donor, created = Donor.objects.get_or_create(
                phone=donation.donor_phone,
                defaults={
                    'name': donation.donor_name,
                    'email': donation.donor_email,
                    'pan_number': donation.pan_number,
                }
            )
            donation.donor = donor

            # If it's a pledge (not paying right now)
            if donation.is_pledge:
                donation.status = 'PENDING'
                donation.payment_method = 'RAZORPAY_LINK'
                
                # Generate RazorPay payment link for the pledge
                base_url = request.build_absolute_uri('/')[:-1]
                link_res = razorpay_service.create_payment_link(
                    amount=donation.amount,
                    description=f"Pledge for {donation.initiative.title if donation.initiative else 'Trust Fund'}",
                    customer_name=donation.donor_name,
                    customer_email=donation.donor_email,
                    customer_phone=donation.donor_phone
                )
                donation.razorpay_payment_link = link_res.get('short_url', '')
                donation.razorpay_link_id = link_res.get('link_id', '')
                donation.save()

                # Automatically send WhatsApp reminder with payment link!
                try:
                    whatsapp_service.send_payment_reminder(donation, base_url=base_url)
                except Exception as e:
                    pass

                messages.success(request, f"Thank you {donation.donor_name}! Your pledge of ₹{donation.amount} has been registered. A payment reminder with the RazorPay payment link has been dispatched to your WhatsApp (+{donation.donor_phone}).")
                return redirect('dashboard')

            # Otherwise, create Razorpay Order for instant checkout
            receipt_code = f"order_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            order_res = razorpay_service.create_order(
                amount=donation.amount,
                receipt=receipt_code,
                notes={
                    'donor_name': donation.donor_name,
                    'donor_phone': donation.donor_phone,
                    'initiative': donation.initiative.title if donation.initiative else "General Fund"
                }
            )

            donation.razorpay_order_id = order_res.get('order_id')
            donation.status = 'PENDING'
            donation.save()

            # Render checkout page with Razorpay popup
            return render(request, 'core/razorpay_checkout.html', {
                'donation': donation,
                'order': order_res,
                'key_id': razorpay_service.key_id,
                'is_simulated': order_res.get('is_simulated', False),
            })
    else:
        form = DonationForm(initial=initial)

    return render(request, 'core/donate.html', {
        'form': form,
        'selected_initiative': selected_initiative,
        'metrics': get_donation_metrics(),
    })


@csrf_exempt
def payment_verify(request):
    """
    Handles RazorPay payment verification webhook/callback.
    Marks donation as SUCCESS, issues 80G receipt number, and triggers WhatsApp confirmation.
    """
    if request.method == 'POST':
        donation_id = request.POST.get('donation_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature', '')

        try:
            donation = Donation.objects.get(id=donation_id)
        except Donation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Donation not found'}, status=404)

        # Verify signature
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )

        if is_valid:
            donation.status = 'SUCCESS'
            donation.razorpay_order_id = razorpay_order_id
            donation.razorpay_payment_id = razorpay_payment_id or f"pay_sim_{donation.id}"
            donation.razorpay_signature = razorpay_signature or "simulated_valid_sig"
            donation.payment_method = 'RAZORPAY_CHECKOUT'
            donation.save()

            # Trigger automated WhatsApp confirmation & 80G receipt download
            base_url = request.build_absolute_uri('/')[:-1]
            try:
                whatsapp_service.send_donation_receipt_notification(donation, base_url=base_url)
            except Exception as e:
                pass

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'success',
                    'receipt_url': reverse('receipt_detail', kwargs={'receipt_number': donation.receipt_number})
                })
            return redirect('receipt_detail', receipt_number=donation.receipt_number)
        else:
            donation.status = 'FAILED'
            donation.save()
            messages.error(request, "Payment verification could not be validated. Please contact trust support.")
            return redirect('home')

    return redirect('home')


def receipt_detail(request, receipt_number):
    """Displays the formal, printable 80G tax exemption receipt."""
    donation = get_object_or_404(Donation, receipt_number=receipt_number)
    return render(request, 'core/receipt_detail.html', {
        'donation': donation,
        'generated_date': timezone.now(),
    })


# ---------------- WhatsApp Automation Action Views ---------------- #

def send_whatsapp_reminder(request, donation_id):
    """Trustee/Admin action: Dispatch payment reminder for pending pledge via WhatsApp."""
    donation = get_object_or_404(Donation, id=donation_id)
    base_url = request.build_absolute_uri('/')[:-1]
    
    # Generate payment link if not already existing
    if not donation.razorpay_payment_link:
        link_res = razorpay_service.create_payment_link(
            amount=donation.amount,
            description=f"Pledge for {donation.initiative.title if donation.initiative else 'Trust Fund'}",
            customer_name=donation.donor_name,
            customer_email=donation.donor_email,
            customer_phone=donation.donor_phone
        )
        donation.razorpay_payment_link = link_res.get('short_url', '')
        donation.razorpay_link_id = link_res.get('link_id', '')
        donation.save()

    notification = whatsapp_service.send_payment_reminder(donation, base_url=base_url)
    
    messages.success(
        request, 
        f"✅ WhatsApp Payment Reminder dispatched to {donation.donor_name} (+{donation.donor_phone}). Status: {notification.get_status_display()}."
    )
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def broadcast_event_whatsapp(request, event_id):
    """Trustee/Admin action: Broadcast event advertisement to all donors via WhatsApp."""
    event = get_object_or_404(Event, id=event_id)
    base_url = request.build_absolute_uri('/')[:-1]
    
    donors = Donor.objects.filter(opt_in_whatsapp=True)
    dispatched_count = 0

    for donor in donors:
        whatsapp_service.send_event_advertisement(event, donor, base_url=base_url)
        dispatched_count += 1

    event.whatsapp_broadcast_sent = True
    event.save()

    messages.success(
        request, 
        f"📢 Event advertisement for \"{event.title}\" successfully broadcasted to {dispatched_count} donors via WhatsApp!"
    )
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def whatsapp_logs(request):
    """View log of all WhatsApp notifications sent, with direct wa.me fallback links."""
    logs = WhatsAppNotification.objects.all().order_by('-created_at')[:100]
    return render(request, 'core/whatsapp_logs.html', {
        'logs': logs,
    })


# ---------------- Content Management Views (Initiatives, Events, Expenses) ---------------- #

def manage_initiative(request, pk=None):
    """Create or edit an initiative with image upload."""
    initiative = get_object_or_404(Initiative, pk=pk) if pk else None
    if request.method == 'POST':
        form = InitiativeForm(request.POST, request.FILES, instance=initiative)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Initiative '{saved.title}' saved successfully!")
            return redirect('dashboard')
    else:
        form = InitiativeForm(instance=initiative)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Initiative' if pk else 'Add New Initiative',
        'subtitle': 'Manage charity campaign, upload banner, set target expected amount.',
    })


def manage_event(request, pk=None):
    """Create or edit an event with banner image upload."""
    event = get_object_or_404(Event, pk=pk) if pk else None
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Event '{saved.title}' saved successfully!")
            return redirect('dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Event' if pk else 'Add New Event',
        'subtitle': 'Upload event details, venue, date, and coordinate WhatsApp announcements.',
    })


def manage_expense(request, pk=None):
    """Log or update itemized monthly maintenance expense with receipt voucher upload."""
    expense = get_object_or_404(MaintenanceExpense, pk=pk) if pk else None
    if request.method == 'POST':
        form = MaintenanceExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Maintenance expense '{saved.title}' recorded!")
            return redirect('maintenance_costs')
    else:
        form = MaintenanceExpenseForm(instance=expense)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Maintenance Expense' if pk else 'Log New Maintenance Expense',
        'subtitle': 'Track monthly operational costs per activity for full financial transparency.',
    })


def manage_trustee(request, pk=None):
    """Add or edit trustee profile with photo and social media links."""
    trustee = get_object_or_404(Trustee, pk=pk) if pk else None
    if request.method == 'POST':
        form = TrusteeForm(request.POST, request.FILES, instance=trustee)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Trustee profile '{saved.name}' updated successfully!")
            return redirect('trustees_list')
    else:
        form = TrusteeForm(instance=trustee)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Trustee Profile' if pk else 'Add New Trustee',
        'subtitle': 'Manage board member profiles, biographical notes, and social media handles.',
    })
