from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
import uuid
import urllib.parse


class Initiative(models.Model):
    CATEGORY_CHOICES = [
        ('HEALTHCARE', 'Healthcare & Medical Aid'),
        ('EDUCATION', 'Child Education & Scholarships'),
        ('HUNGER', 'Hunger Relief & Annadanam'),
        ('SHELTER', 'Elderly Care & Orphanage Support'),
        ('DISASTER', 'Emergency & Disaster Relief'),
        ('WOMEN', 'Women Empowerment & Skill Training'),
        ('ENVIRONMENT', 'Environment & Green Drive'),
        ('GENERAL', 'General Trust Welfare Fund'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    short_description = models.CharField(max_length=300, help_text="Brief summary for cards")
    detailed_description = models.TextField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Expected donation goal in INR")
    image = models.ImageField(upload_to='initiatives/', blank=True, null=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "initiative"
            unique_slug = base_slug
            num = 1
            while Initiative.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def total_raised(self):
        """Sum of completed successful donations for this initiative."""
        from django.db.models import Sum
        completed = self.donations.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total']
        return completed or Decimal('0.00')

    @property
    def pending_amount(self):
        """Remaining amount to reach target goal."""
        remaining = self.target_amount - self.total_raised
        return max(Decimal('0.00'), remaining)

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 100
        pct = (self.total_raised / self.target_amount) * 100
        return min(round(float(pct), 1), 100.0)

    @property
    def is_goal_reached(self):
        return self.total_raised >= self.target_amount

    def get_absolute_url(self):
        return reverse('initiative_detail', kwargs={'slug': self.slug})


class ActivityPhoto(models.Model):
    title = models.CharField(max_length=200, help_text="Photo title or activity headline")
    initiative = models.ForeignKey(
        Initiative,
        on_delete=models.CASCADE,
        related_name='photos',
        blank=True,
        null=True,
        help_text="Related initiative / activity (leave blank for general)"
    )
    image = models.ImageField(upload_to='activity_photos/', help_text="Field / event photo")
    caption = models.TextField(help_text="Write details / caption / impact story about this photo")
    location = models.CharField(max_length=200, default='Harapanahalli', blank=True, help_text="Location / circle where photo was taken")
    date_taken = models.DateField(default=timezone.now, help_text="Date the activity was conducted")
    is_featured = models.BooleanField(default=True, help_text="Show in home & dashboard photo highlights")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_taken', '-created_at']
        verbose_name = "Activity Photo & Update"
        verbose_name_plural = "Activity Photos & Updates"

    def __str__(self):
        return f"{self.title} ({self.initiative.title if self.initiative else 'General'})"


class Event(models.Model):
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    event_date = models.DateTimeField(help_text="Date and start time of the event")
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, help_text="Venue / Address / Online link")
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    capacity = models.PositiveIntegerField(default=100, help_text="Max expected attendees")
    rsvp_count = models.PositiveIntegerField(default=0)
    contact_person = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=25, blank=True)
    whatsapp_broadcast_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "event"
            unique_slug = base_slug
            num = 1
            while Event.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.event_date.strftime('%d %b %Y')})"

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    @property
    def is_past(self):
        return self.event_date < timezone.now()


class Trustee(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, help_text="e.g. Managing Trustee, Founder & Chairperson, Treasurer")
    bio = models.TextField(help_text="Detailed profile and contribution")
    quote = models.CharField(max_length=300, blank=True, help_text="Short vision statement or quote")
    photo = models.ImageField(upload_to='trustees/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Display priority (lower is first)")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25, blank=True)
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn Profile")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter / X Profile")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook Profile")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram Profile")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.designation}"


class Donor(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25, help_text="Phone number with country code for WhatsApp (e.g. +919820012345)")
    pan_number = models.CharField(max_length=15, blank=True, verbose_name="PAN (for 80G Tax Exemption)")
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_anonymous = models.BooleanField(default=False)
    opt_in_whatsapp = models.BooleanField(default=True, help_text="Agreed to receive WhatsApp updates")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name if not self.is_anonymous else f"Anonymous ({self.phone})"

    @property
    def total_donated(self):
        from django.db.models import Sum
        val = self.donations.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total']
        return val or Decimal('0.00')

    @property
    def pending_pledges(self):
        from django.db.models import Sum
        val = self.donations.filter(status='PENDING').aggregate(total=Sum('amount'))['total']
        return val or Decimal('0.00')


class Donation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending / Pledged'),
        ('SUCCESS', 'Completed / Received'),
        ('FAILED', 'Failed / Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    DONATION_TYPE_CHOICES = [
        ('ONE_TIME', 'One-Time Donation'),
        ('MONTHLY_PLEDGE', 'Monthly Pledge'),
        ('CAMPAIGN_SPECIFIC', 'Campaign Contribution'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('RAZORPAY_CHECKOUT', 'RazorPay Gateway'),
        ('RAZORPAY_LINK', 'RazorPay Payment Link'),
        ('UPI', 'Direct UPI'),
        ('BANK_TRANSFER', 'NEFT / RTGS'),
        ('CASH_CHEQUE', 'Offline Cheque / Cash'),
    ]

    donor = models.ForeignKey(Donor, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    donor_name = models.CharField(max_length=150)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=25, help_text="Phone with country code (e.g. +91XXXXXXXXXX)")
    pan_number = models.CharField(max_length=15, blank=True)

    initiative = models.ForeignKey(Initiative, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    donation_type = models.CharField(max_length=25, choices=DONATION_TYPE_CHOICES, default='ONE_TIME')
    is_pledge = models.BooleanField(default=False, help_text="Mark True if this is an expected/pending pledge")
    pledge_due_date = models.DateField(blank=True, null=True)

    # RazorPay fields
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    razorpay_payment_link = models.URLField(max_length=500, blank=True, help_text="Generated RazorPay Payment Link")
    razorpay_link_id = models.CharField(max_length=100, blank=True)

    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='RAZORPAY_CHECKOUT')
    receipt_number = models.CharField(max_length=40, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.status == 'SUCCESS' and not self.receipt_number:
            # Generate official receipt number e.g. MEEZAN-REC-202611-ABCD
            today_str = timezone.now().strftime('%Y%m')
            code = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"MEEZAN-REC-{today_str}-{code}"
        elif self.status != 'SUCCESS' and not self.receipt_number:
            self.receipt_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"₹{self.amount} by {self.donor_name} ({self.get_status_display()})"


class MaintenanceActivity(models.Model):
    name = models.CharField(max_length=150, unique=True, help_text="Activity / Cost Category Name")
    code = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=60, default='fa-hand-holding-heart', help_text="FontAwesome icon class, e.g. fa-utensils, fa-hospital, fa-graduation-cap")
    color_hex = models.CharField(max_length=20, default='#2563eb', help_text="Hex color code for charts, e.g. #2563eb")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Maintenance Activities"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MaintenanceExpense(models.Model):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]

    activity = models.ForeignKey(MaintenanceActivity, on_delete=models.CASCADE, related_name='expenses')
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, default=11)
    year = models.PositiveIntegerField(default=2026)
    title = models.CharField(max_length=255, help_text="Specific maintenance expense description")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount in INR")
    date_incurred = models.DateField(default=timezone.now)
    vendor_payee = models.CharField(max_length=180, blank=True, help_text="Vendor / Service provider / Payee")
    bill_voucher_number = models.CharField(max_length=100, blank=True, help_text="Invoice / Voucher reference")
    receipt_voucher = models.FileField(upload_to='expenses/vouchers/', blank=True, null=True, help_text="Upload bill/receipt voucher")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_incurred', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.get_month_display()} {self.year})"


class WhatsAppNotification(models.Model):
    TYPE_CHOICES = [
        ('PAYMENT_REMINDER', 'Payment & Pledge Reminder'),
        ('EVENT_ADVERTISEMENT', 'Event Advertisement & Invitation'),
        ('DONATION_RECEIPT', 'Donation Confirmation & Receipt'),
        ('GENERAL_UPDATE', 'General Trust Update & Newsletter'),
    ]

    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed'),
    ]

    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    recipient_name = models.CharField(max_length=150)
    recipient_phone = models.CharField(max_length=25, help_text="WhatsApp number with country code")
    donor = models.ForeignKey(Donor, on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_messages')
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    donation = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)
    message_body = models.TextField()
    direct_wa_link = models.URLField(max_length=1000, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='QUEUED')
    provider_message_id = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Clean phone number (strip spaces, dashes)
        clean_phone = ''.join(c for c in self.recipient_phone if c.isdigit() or c == '+')
        if clean_phone.startswith('+'):
            clean_digits = clean_phone[1:]
        else:
            clean_digits = clean_phone
        encoded_text = urllib.parse.quote(self.message_body)
        self.direct_wa_link = f"https://wa.me/{clean_digits}?text={encoded_text}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.recipient_phone} ({self.status})"
