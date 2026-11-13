import json
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.urls import reverse

from .models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification, ActivityPhoto
)
from .forms import (
    DonationForm, InitiativeForm, EventForm,
    MaintenanceExpenseForm, TrusteeForm, ActivityPhotoForm
)
from .razorpay_service import razorpay_service
from .whatsapp_service import whatsapp_service


def staff_required(view_func):
    """Decorator ensuring user is authenticated and has staff or superuser privileges."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with trustee/admin credentials to access this management feature.")
            return redirect(f"{reverse('admin_login')}?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access restricted. You need trustee or staff permissions.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_donation_metrics():
    """
    Computes real-time donation metrics:
    - Expected Amount: Sum of active initiative target amounts + outstanding pledged donations
    - Raised Amount: Total successful donations
    - Pending Amount: Remaining target needed + outstanding pledges
    - Pending Pledges: Sum of committed pending pledges
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
    """Public home page with broadened humanitarian mission, metrics, activities, and banking."""
    metrics = get_donation_metrics()
    featured_initiatives = Initiative.objects.filter(is_active=True).order_by('-is_featured', 'id')[:6]
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
        'activity_photos': ActivityPhoto.objects.select_related('initiative').all()[:6],
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
    """
    metrics = get_donation_metrics()
    initiatives = Initiative.objects.all().order_by('-is_active', '-target_amount')
    
    # Chart 1: Expected vs Raised vs Pending
    chart_metric_labels = ['Raised Amount (₹)', 'Pending Pledges (₹)', 'Expected Budget (₹)']
    chart_metric_data = [
        float(metrics['total_raised']),
        float(metrics['pending_pledges']),
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

    pending_donations = Donation.objects.filter(status='PENDING').order_by('-created_at')[:10]
    recent_donations = Donation.objects.filter(status='SUCCESS').order_by('-created_at')[:10]
    upcoming_events = Event.objects.filter(status='UPCOMING').order_by('event_date')

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
        'activity_photos': ActivityPhoto.objects.select_related('initiative').all()[:8],
        'wa_stats': wa_stats,
    }
    return render(request, 'core/dashboard.html', context)


# ---------------- Authentication & Admin Access ---------------- #

def admin_login_view(request):
    """Admin login page for trustees and staff."""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_portal')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! You are logged into the Trustee Admin Portal.")
            next_url = request.GET.get('next') or request.POST.get('next') or 'admin_portal'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def admin_logout_view(request):
    """Logs out admin user and redirects to home."""
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('home')


# ---------------- Frontend Admin Management Portal ---------------- #

@staff_required
def admin_portal_view(request):
    """
    Comprehensive UI-based admin management portal:
    Allows logged-in admins to add, edit, and update:
    - Financial figures & target budgets
    - Activities / Initiatives
    - Events
    - Monthly Maintenance Expenses
    - Trustee Profiles
    """
    metrics = get_donation_metrics()
    initiatives = Initiative.objects.all().order_by('id')
    events = Event.objects.all().order_by('-event_date')
    expenses = MaintenanceExpense.objects.select_related('activity').order_by('-date_incurred', '-created_at')[:30]
    trustees = Trustee.objects.all().order_by('order', 'name')
    pending_donations = Donation.objects.filter(status='PENDING').order_by('-created_at')
    recent_donations = Donation.objects.filter(status='SUCCESS').order_by('-created_at')[:20]

    context = {
        'metrics': metrics,
        'initiatives': initiatives,
        'events': events,
        'expenses': expenses,
        'trustees': trustees,
        'pending_donations': pending_donations,
        'recent_donations': recent_donations,
        'activity_photos': ActivityPhoto.objects.select_related('initiative').all().order_by('-date_taken', '-created_at'),
        'photo_form': ActivityPhotoForm(),
        'activities': MaintenanceActivity.objects.all(),
    }
    return render(request, 'core/admin_portal.html', context)


@staff_required
def update_financial_target(request, pk):
    """Quick inline/modal update for an initiative's target budget."""
    initiative = get_object_or_404(Initiative, pk=pk)
    if request.method == 'POST':
        new_target = request.POST.get('target_amount')
        is_active = request.POST.get('is_active') == 'on'
        if new_target:
            try:
                initiative.target_amount = Decimal(new_target)
                initiative.is_active = is_active
                initiative.save()
                messages.success(request, f"Financial target for '{initiative.title}' updated to ₹{initiative.target_amount:,.2f}!")
            except Exception as e:
                messages.error(request, f"Failed to update target: {e}")
    return redirect('admin_portal')


# ---------------- Public Content Pages ---------------- #

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
        'activity_photos': ActivityPhoto.objects.select_related('initiative').all().order_by('-date_taken', '-created_at')[:12],
    })


def initiative_detail(request, slug):
    """Detailed view of a single initiative with photo gallery, progress, and donation box."""
    initiative = get_object_or_404(Initiative, slug=slug)
    recent_donations = initiative.donations.filter(status='SUCCESS').order_by('-created_at')[:6]
    photos = initiative.photos.all().order_by('-date_taken', '-created_at')
    form = DonationForm(initial={'initiative': initiative})
    return render(request, 'core/initiative_detail.html', {
        'initiative': initiative,
        'recent_donations': recent_donations,
        'photos': photos,
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


# ---------------- RazorPay Integration & Donation Endpoints ---------------- #

def donate(request):
    """General donation page with RazorPay payment initiation and direct SBI details."""
    initiative_id = request.GET.get('initiative')
    initial = {}
    selected_initiative = None
    if initiative_id:
        try:
            selected_initiative = Initiative.objects.get(id=initiative_id)
            initial['initiative'] = selected_initiative
        except Initiative.DoesNotExist:
            pass

    # Traditional form POST fallback
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            custom_amt = form.cleaned_data.get('custom_amount')
            if custom_amt and custom_amt > 0:
                donation.amount = custom_amt

            donor, _ = Donor.objects.get_or_create(
                phone=donation.donor_phone,
                defaults={
                    'name': donation.donor_name,
                    'email': donation.donor_email,
                    'pan_number': donation.pan_number,
                }
            )
            donation.donor = donor

            if donation.is_pledge:
                donation.status = 'PENDING'
                donation.payment_method = 'RAZORPAY_LINK'
                base_url = request.build_absolute_uri('/')[:-1]
                link_res = razorpay_service.create_payment_link(
                    amount=donation.amount,
                    description=f"Pledge for {donation.initiative.title if donation.initiative else 'Meezan Trust'}",
                    customer_name=donation.donor_name,
                    customer_email=donation.donor_email,
                    customer_phone=donation.donor_phone
                )
                donation.razorpay_payment_link = link_res.get('short_url', '')
                donation.razorpay_link_id = link_res.get('link_id', '')
                donation.save()

                try:
                    whatsapp_service.send_payment_reminder(donation, base_url=base_url)
                except Exception:
                    pass

                messages.success(request, f"Thank you {donation.donor_name}! Your pledge of ₹{donation.amount:,.2f} has been registered. A payment reminder with the RazorPay payment link has been dispatched to your WhatsApp (+{donation.donor_phone}).")
                return redirect('dashboard')

            # Instant Order
            receipt_code = f"order_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            order_res = razorpay_service.create_order(
                amount=donation.amount,
                receipt=receipt_code,
                notes={
                    'donor_name': donation.donor_name,
                    'donor_phone': donation.donor_phone,
                    'initiative': donation.initiative.title if donation.initiative else "General Welfare"
                }
            )

            donation.razorpay_order_id = order_res.get('order_id')
            donation.status = 'PENDING'
            donation.save()

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
def api_create_order(request):
    """
    Backend order creation endpoint:
    - Generates Razorpay order_id and returns credentials for Razorpay popup.
    - If is_pledge is checked, saves pledge directly to database and sends WhatsApp reminder.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        amount = Decimal(str(data.get('amount', 0)))
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Please enter a valid donation amount.'}, status=400)

        donor_name = data.get('donor_name', '').strip()
        donor_phone = data.get('donor_phone', '').strip()
        donor_email = data.get('donor_email', '').strip()
        pan_number = data.get('pan_number', '').strip()
        initiative_id = data.get('initiative')
        is_pledge = str(data.get('is_pledge', '')).lower() in ('true', '1', 'on', 'yes')
        pledge_due_date = data.get('pledge_due_date') or None

        if not donor_name or not donor_phone:
            return JsonResponse({'success': False, 'error': 'Full name and WhatsApp number are required.'}, status=400)

        initiative = None
        if initiative_id:
            try:
                initiative = Initiative.objects.get(id=initiative_id)
            except Initiative.DoesNotExist:
                pass

        donor, _ = Donor.objects.get_or_create(
            phone=donor_phone,
            defaults={
                'name': donor_name,
                'email': donor_email,
                'pan_number': pan_number,
            }
        )

        donation = Donation.objects.create(
            donor=donor,
            donor_name=donor_name,
            donor_phone=donor_phone,
            donor_email=donor_email,
            pan_number=pan_number,
            initiative=initiative,
            amount=amount,
            status='PENDING',
            is_pledge=is_pledge,
            pledge_due_date=pledge_due_date,
            donation_type='MONTHLY_PLEDGE' if is_pledge else 'ONE_TIME',
            payment_method='RAZORPAY_LINK' if is_pledge else 'RAZORPAY_CHECKOUT'
        )

        base_url = request.build_absolute_uri('/')[:-1]

        # Case 1: Pledge-only submission (save directly to database, do not trigger payment popup)
        if is_pledge:
            link_res = razorpay_service.create_payment_link(
                amount=donation.amount,
                description=f"Pledge for {donation.initiative.title if donation.initiative else 'Meezan Community Welfare'}",
                customer_name=donation.donor_name,
                customer_email=donation.donor_email,
                customer_phone=donation.donor_phone
            )
            donation.razorpay_payment_link = link_res.get('short_url', '')
            donation.razorpay_link_id = link_res.get('link_id', '')
            donation.save()

            try:
                whatsapp_service.send_payment_reminder(donation, base_url=base_url)
            except Exception:
                pass

            return JsonResponse({
                'success': True,
                'is_pledge': True,
                'donation_id': donation.id,
                'message': f"Pledge of ₹{donation.amount:,.2f} recorded successfully! A WhatsApp reminder with RazorPay link has been dispatched.",
                'redirect_url': reverse('dashboard')
            })

        # Case 2: Immediate Payment -> Generate RazorPay order for popup checkout
        receipt_code = f"order_{donation.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        order_res = razorpay_service.create_order(
            amount=donation.amount,
            receipt=receipt_code,
            notes={
                'donor_name': donation.donor_name,
                'donor_phone': donation.donor_phone,
                'initiative': donation.initiative.title if donation.initiative else "General Welfare"
            }
        )

        donation.razorpay_order_id = order_res.get('order_id')
        donation.save()

        return JsonResponse({
            'success': True,
            'is_pledge': False,
            'order_id': order_res.get('order_id'),
            'amount': float(donation.amount),
            'amount_paise': order_res.get('amount_paise'),
            'currency': order_res.get('currency', 'INR'),
            'key_id': razorpay_service.key_id,
            'donation_id': donation.id,
            'donor_name': donation.donor_name,
            'donor_email': donation.donor_email,
            'donor_phone': donation.donor_phone,
            'initiative_title': donation.initiative.title if donation.initiative else "Meezan Community Welfare",
            'is_simulated': order_res.get('is_simulated', False)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def payment_verify(request):
    """
    Handles RazorPay payment verification webhook/callback.
    Marks donation as SUCCESS, issues official receipt number, updates metrics,
    and triggers instant WhatsApp confirmation.
    """
    if request.method == 'POST':
        donation_id = request.POST.get('donation_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature', '')

        # Also support JSON body if posted via fetch
        if not donation_id and request.content_type == 'application/json':
            try:
                body_data = json.loads(request.body)
                donation_id = body_data.get('donation_id')
                razorpay_order_id = body_data.get('razorpay_order_id')
                razorpay_payment_id = body_data.get('razorpay_payment_id')
                razorpay_signature = body_data.get('razorpay_signature', '')
            except Exception:
                pass

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
            except Exception:
                pass

            receipt_url = reverse('receipt_detail', kwargs={'receipt_number': donation.receipt_number})
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'success',
                    'receipt_number': donation.receipt_number,
                    'receipt_url': receipt_url,
                    'message': 'Payment confirmed successfully!'
                })
            messages.success(request, f"Heartfelt gratitude! Your contribution of ₹{donation.amount:,.2f} is verified. Receipt #{donation.receipt_number} issued.")
            return redirect('receipt_detail', receipt_number=donation.receipt_number)
        else:
            donation.status = 'FAILED'
            donation.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'message': 'Payment signature validation failed.'}, status=400)
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

@staff_required
def send_whatsapp_reminder(request, donation_id):
    """Trustee/Admin action: Dispatch payment reminder for pending pledge via WhatsApp."""
    donation = get_object_or_404(Donation, id=donation_id)
    base_url = request.build_absolute_uri('/')[:-1]
    
    if not donation.razorpay_payment_link:
        link_res = razorpay_service.create_payment_link(
            amount=donation.amount,
            description=f"Pledge for {donation.initiative.title if donation.initiative else 'Meezan Community Welfare'}",
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
    return redirect(request.META.get('HTTP_REFERER', 'admin_portal'))


@staff_required
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
    return redirect(request.META.get('HTTP_REFERER', 'admin_portal'))


def whatsapp_logs(request):
    """View log of all WhatsApp notifications sent, with direct wa.me fallback links."""
    logs = WhatsAppNotification.objects.all().order_by('-created_at')[:100]
    return render(request, 'core/whatsapp_logs.html', {
        'logs': logs,
    })


# ---------------- Content Management Views (Restricted to Staff/Admin) ---------------- #

@staff_required
def manage_initiative(request, pk=None):
    """Create or edit an initiative with image upload."""
    initiative = get_object_or_404(Initiative, pk=pk) if pk else None
    if request.method == 'POST':
        form = InitiativeForm(request.POST, request.FILES, instance=initiative)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Initiative '{saved.title}' saved successfully!")
            return redirect('admin_portal')
    else:
        form = InitiativeForm(instance=initiative)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Initiative' if pk else 'Add New Initiative',
        'subtitle': 'Manage community welfare initiative, set target budget, and upload banner.',
    })


@staff_required
def manage_event(request, pk=None):
    """Create or edit an event with banner image upload."""
    event = get_object_or_404(Event, pk=pk) if pk else None
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Event '{saved.title}' saved successfully!")
            return redirect('admin_portal')
    else:
        form = EventForm(instance=event)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Event' if pk else 'Add New Event',
        'subtitle': 'Upload event details, venue, date, and coordinate WhatsApp invitations.',
    })


@staff_required
def manage_expense(request, pk=None):
    """Log or update itemized monthly maintenance expense with receipt voucher upload."""
    expense = get_object_or_404(MaintenanceExpense, pk=pk) if pk else None
    if request.method == 'POST':
        form = MaintenanceExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Maintenance expense '{saved.title}' recorded!")
            return redirect('admin_portal')
    else:
        form = MaintenanceExpenseForm(instance=expense)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Maintenance Expense' if pk else 'Log New Maintenance Expense',
        'subtitle': 'Track monthly operational costs per activity for full financial transparency.',
    })


@staff_required
def manage_trustee(request, pk=None):
    """Add or edit trustee profile with photo and social media links."""
    trustee = get_object_or_404(Trustee, pk=pk) if pk else None
    if request.method == 'POST':
        form = TrusteeForm(request.POST, request.FILES, instance=trustee)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Trustee profile '{saved.name}' updated successfully!")
            return redirect('admin_portal')
    else:
        form = TrusteeForm(instance=trustee)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Trustee Profile' if pk else 'Add New Trustee',
        'subtitle': 'Manage board member profiles, biographical notes, and social media handles.',
    })


@staff_required
def manage_activity_photo(request, pk=None):
    """Upload or edit an activity / field photo and write impact story details about it."""
    photo = get_object_or_404(ActivityPhoto, pk=pk) if pk else None
    if request.method == 'POST':
        form = ActivityPhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Photo update '{saved.title}' published successfully! It is now live across the dashboard and activities pages.")
            return redirect('admin_portal')
    else:
        form = ActivityPhotoForm(instance=photo)
    return render(request, 'core/manage_form.html', {
        'form': form,
        'title': 'Edit Activity Photo & Story' if pk else 'Upload New Activity Photo & Story',
        'subtitle': 'Upload field photographs of trust initiatives, camps, and drives and write impact stories about them.',
    })


@staff_required
def delete_activity_photo(request, pk):
    """Remove an activity photo update."""
    photo = get_object_or_404(ActivityPhoto, pk=pk)
    title = photo.title
    photo.delete()
    messages.info(request, f"Photo update '{title}' was removed.")
    return redirect('admin_portal')
