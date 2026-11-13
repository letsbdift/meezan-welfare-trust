from django import forms
from .models import Initiative, Event, Trustee, Donation, MaintenanceExpense, MaintenanceActivity, Donor, ActivityPhoto


class DonationForm(forms.ModelForm):
    custom_amount = forms.DecimalField(
        required=False, 
        min_value=10, 
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Enter other amount in ₹'})
    )

    class Meta:
        model = Donation
        fields = ['donor_name', 'donor_email', 'donor_phone', 'pan_number', 'initiative', 'amount', 'donation_type', 'is_pledge', 'pledge_due_date']
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name', 'required': 'required'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'donor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210', 'required': 'required'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABCDE1234F (for 80G tax receipt)'}),
            'initiative': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '₹ Amount'}),
            'donation_type': forms.Select(attrs={'class': 'form-select'}),
            'is_pledge': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is_pledge_check'}),
            'pledge_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class InitiativeForm(forms.ModelForm):
    class Meta:
        model = Initiative
        fields = ['title', 'category', 'short_description', 'detailed_description', 'target_amount', 'image', 'start_date', 'end_date', 'is_active', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Initiative title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short summary for cards'}),
            'detailed_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Full mission details and objectives'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₹ Target Amount'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'end_date', 'location', 'image', 'status', 'capacity', 'contact_person', 'contact_phone']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Event program, schedule, and purpose'}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hall / Ground / Address / Virtual Link'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event coordinator name'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXXXXXXX'}),
        }


class MaintenanceExpenseForm(forms.ModelForm):
    class Meta:
        model = MaintenanceExpense
        fields = ['activity', 'month', 'year', 'title', 'amount', 'date_incurred', 'vendor_payee', 'bill_voucher_number', 'receipt_voucher', 'notes']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expense description / purpose'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₹ Incurred amount'}),
            'date_incurred': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vendor_payee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor or service provider name'}),
            'bill_voucher_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voucher / Bill # (e.g. VOUCH-2026-110)'}),
            'receipt_voucher': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional justification or verification notes'}),
        }


class TrusteeForm(forms.ModelForm):
    class Meta:
        model = Trustee
        fields = ['name', 'designation', 'bio', 'quote', 'photo', 'order', 'email', 'phone', 'linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quote': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ActivityPhotoForm(forms.ModelForm):
    class Meta:
        model = ActivityPhoto
        fields = ['title', 'initiative', 'image', 'caption', 'location', 'date_taken', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Free Ration Kit Distribution for Widows & Needy'}),
            'initiative': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write details, impact notes, and describe what took place in this photo...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Harapanahalli Circle 5, Vijayanagara'}),
            'date_taken': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
