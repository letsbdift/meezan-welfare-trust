from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification
)


@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'target_amount', 'get_total_raised', 'get_pending', 'progress_bar', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'created_at')
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}

    def get_total_raised(self, obj):
        return f"₹{obj.total_raised:,.2f}"
    get_total_raised.short_description = "Raised (₹)"

    def get_pending(self, obj):
        return f"₹{obj.pending_amount:,.2f}"
    get_pending.short_description = "Pending (₹)"

    def progress_bar(self, obj):
        pct = obj.progress_percentage
        color = '#10b981' if pct >= 100 else '#2563eb'
        return format_html(
            f'<div style="width:100px; background:#e2e8f0; border-radius:4px; overflow:hidden;">'
            f'<div style="width:{min(pct, 100)}%; background:{color}; height:14px; font-size:10px; color:#fff; text-align:center; line-height:14px;">{pct}%</div>'
            f'</div>'
        )
    progress_bar.short_description = "Goal Progress"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location', 'status', 'capacity', 'whatsapp_broadcast_sent')
    list_filter = ('status', 'event_date', 'whatsapp_broadcast_sent')
    search_fields = ('title', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Trustee)
class TrusteeAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'order', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'designation', 'bio')


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'pan_number', 'get_total_donated', 'opt_in_whatsapp', 'created_at')
    search_fields = ('name', 'phone', 'email', 'pan_number')
    list_filter = ('opt_in_whatsapp', 'created_at')

    def get_total_donated(self, obj):
        return f"₹{obj.total_donated:,.2f}"
    get_total_donated.short_description = "Lifetime Donated"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'donor_name', 'amount', 'initiative', 'status', 'is_pledge', 'payment_method', 'created_at')
    list_filter = ('status', 'is_pledge', 'payment_method', 'created_at')
    search_fields = ('donor_name', 'donor_phone', 'receipt_number', 'razorpay_payment_id')


@admin.register(MaintenanceActivity)
class MaintenanceActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color_hex', 'code')
    prepopulated_fields = {'code': ('name',)}


@admin.register(MaintenanceExpense)
class MaintenanceExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity', 'month', 'year', 'amount', 'date_incurred', 'vendor_payee')
    list_filter = ('month', 'year', 'activity')
    search_fields = ('title', 'vendor_payee', 'bill_voucher_number')


@admin.register(WhatsAppNotification)
class WhatsAppNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'recipient_phone', 'notification_type', 'status', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('recipient_name', 'recipient_phone', 'message_body')
    readonly_fields = ('direct_wa_link',)
