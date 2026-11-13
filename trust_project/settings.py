"""
Django settings for trust_project project.
Meezan Welfare And Charitable Trust Harapanahalli
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-eif^%ghq^6d0t3db^!ab_^_+ooy+r_7_465bn21q(cz9fc*2wp')

DEBUG = True

ALLOWED_HOSTS = ['*', 'letsbdift.pythonanywhere.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trust_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.trust_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'trust_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Trust Details - Meezan Welfare And Charitable Trust Harapanahalli
TRUST_NAME = os.getenv('TRUST_NAME', 'Meezan Welfare And Charitable Trust Harapanahalli')
TRUST_SHORT_NAME = os.getenv('TRUST_SHORT_NAME', 'Meezan Welfare & Charitable Trust')
TRUST_TAGLINE = os.getenv('TRUST_TAGLINE', 'Serving the community with compassion, unity, and social responsibility')
TRUST_REGISTRATION_NO = os.getenv('TRUST_REGISTRATION_NO', 'MEEZAN/HPLI/TRUST/2021/80G')
TRUST_PAN = os.getenv('TRUST_PAN', 'AAATM9981K')
TRUST_PHONE = os.getenv('TRUST_PHONE', '+91 87222 11966')
TRUST_WHATSAPP_NUMBER = os.getenv('TRUST_WHATSAPP_NUMBER', '+918722211966')
TRUST_EMAIL = os.getenv('TRUST_EMAIL', 'meezantrust.hpli@gmail.com')
TRUST_ADDRESS = os.getenv('TRUST_ADDRESS', 'Meezan Welfare and Charitable Trust, Main Road, Harapanahalli - 583131, Vijayanagara Dist, Karnataka')

# Official Banking & Direct UPI Information
TRUST_BANK_NAME = 'State Bank of India (SBI)'
TRUST_BANK_ACCOUNT_NAME = 'MEEZAN WELFARE AND CHARITABLE TRUST'
TRUST_BANK_ACCOUNT_NO = '45000364554'
TRUST_BANK_IFSC = 'SBIN0017847'
TRUST_UPI_ID = '8722211966@sbi'
TRUST_QR_IMAGE_URL = '/static/img/meezan_sbi_qr.jpg'

# RazorPay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_MeezanTrustDemoKey')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'demo_secret_key_meezan_99')
RAZORPAY_CURRENCY = 'INR'
RAZORPAY_SIMULATION_MODE = os.getenv('RAZORPAY_SIMULATION_MODE', 'True').lower() in ('true', '1', 't')

# WhatsApp Notification Configuration
WHATSAPP_PROVIDER = os.getenv('WHATSAPP_PROVIDER', 'mock')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
WHATSAPP_CLOUD_TOKEN = os.getenv('WHATSAPP_CLOUD_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
