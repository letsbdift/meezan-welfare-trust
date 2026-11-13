from django.conf import settings

def trust_settings(request):
    return {
        'TRUST_NAME': getattr(settings, 'TRUST_NAME', 'Meezan Welfare And Charitable Trust Harapanahalli'),
        'TRUST_SHORT_NAME': getattr(settings, 'TRUST_SHORT_NAME', 'Meezan Welfare & Charitable Trust'),
        'TRUST_TAGLINE': getattr(settings, 'TRUST_TAGLINE', 'Serving the community with compassion, unity, and social responsibility'),
        'TRUST_REGISTRATION_NO': getattr(settings, 'TRUST_REGISTRATION_NO', 'MEEZAN/HPLI/TRUST/2021/80G'),
        'TRUST_PAN': getattr(settings, 'TRUST_PAN', 'AAATM9981K'),
        'TRUST_PHONE': getattr(settings, 'TRUST_PHONE', '+91 87222 11966'),
        'TRUST_WHATSAPP_NUMBER': getattr(settings, 'TRUST_WHATSAPP_NUMBER', '+918722211966'),
        'TRUST_EMAIL': getattr(settings, 'TRUST_EMAIL', 'meezantrust.hpli@gmail.com'),
        'TRUST_ADDRESS': getattr(settings, 'TRUST_ADDRESS', 'Meezan Welfare and Charitable Trust, Main Road, Harapanahalli - 583131, Karnataka'),
        'TRUST_BANK_NAME': getattr(settings, 'TRUST_BANK_NAME', 'State Bank of India (SBI)'),
        'TRUST_BANK_ACCOUNT_NAME': getattr(settings, 'TRUST_BANK_ACCOUNT_NAME', 'MEEZAN WELFARE AND CHARITABLE TRUST'),
        'TRUST_BANK_ACCOUNT_NO': getattr(settings, 'TRUST_BANK_ACCOUNT_NO', '45000364554'),
        'TRUST_BANK_IFSC': getattr(settings, 'TRUST_BANK_IFSC', 'SBIN0017847'),
        'TRUST_UPI_ID': getattr(settings, 'TRUST_UPI_ID', '8722211966@sbi'),
        'TRUST_QR_IMAGE_URL': getattr(settings, 'TRUST_QR_IMAGE_URL', '/static/img/meezan_sbi_qr.jpg'),
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_MeezanTrustDemoKey'),
    }
