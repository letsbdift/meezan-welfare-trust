from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
import json

from core.models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification
)
from core.whatsapp_service import whatsapp_service
from core.razorpay_service import razorpay_service
from core.views import get_donation_metrics


class MeezanTrustComprehensiveTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Admin / Staff User
        self.staff_user = User.objects.create_user(
            username='trustee_admin',
            password='testpassword123',
            is_staff=True,
            first_name='Admin',
            last_name='Trustee'
        )

        # Create Trustee Profile
        self.trustee = Trustee.objects.create(
            name='Janab Thousif Mohammed D',
            designation='Founder & Managing Trustee',
            bio='Dedicated to community welfare in Harapanahalli.',
            linkedin_url='https://linkedin.com/in/letsbdift',
            twitter_url='https://x.com/MeezanTrustHpli'
        )

        # Create Initiative
        self.initiative = Initiative.objects.create(
            title='1. Iftar Koota Interfaith Harmony Gathering',
            category='HUNGER',
            short_description='Interfaith gathering during Ramadan',
            detailed_description='Promoting brotherhood across Harapanahalli and all communities in need.',
            target_amount=Decimal('350000.00'),
            is_active=True
        )

        # Create Event
        self.event = Event.objects.create(
            title='Grand Interfaith Iftar Koota 2026',
            description='Community interfaith banquet.',
            event_date=timezone.now() + timezone.timedelta(days=12),
            location='Meezan Community Grounds, Harapanahalli',
            status='UPCOMING'
        )

        # Create Donor
        self.donor = Donor.objects.create(
            name='Haji Abdul Sattar',
            phone='+919845112233',
            email='abdul.sattar@gmail.com',
            opt_in_whatsapp=True
        )

        # Create Completed Donation
        self.completed_donation = Donation.objects.create(
            donor=self.donor,
            donor_name='Haji Abdul Sattar',
            donor_phone='+919845112233',
            initiative=self.initiative,
            amount=Decimal('50000.00'),
            status='SUCCESS',
            payment_method='UPI',
            receipt_number='MEEZAN-TEST-01'
        )

        # Create Pending Pledge
        self.pending_pledge = Donation.objects.create(
            donor=self.donor,
            donor_name='Haji Abdul Sattar',
            donor_phone='+919845112233',
            initiative=self.initiative,
            amount=Decimal('15000.00'),
            status='PENDING',
            is_pledge=True,
            razorpay_payment_link='https://rzp.io/i/testlink_meezan'
        )

        # Create Maintenance Activity and Expense
        self.activity = MaintenanceActivity.objects.create(
            name='Meezan Poly Clinic & Pharma Healthcare',
            code='clinic-pharma',
            icon='fa-notes-medical',
            color_hex='#ef4444'
        )
        self.expense = MaintenanceExpense.objects.create(
            activity=self.activity,
            month=11,
            year=2026,
            title='Essential Generic Medicines Stock for Meezan Pharma',
            amount=Decimal('25000.00'),
            vendor_payee='Karnataka Generic Pharma Distributors'
        )

    def test_home_page_branding_and_three_metrics(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # 1. Branding Name
        self.assertContains(response, 'Meezan Welfare and Charitable Trust')
        # 2. Broadened Copy
        self.assertContains(response, 'Serving All Needy Individuals & Communities')
        # 3. Three Key Financial Metrics together
        self.assertContains(response, 'Total Expected Budget')
        self.assertContains(response, 'Total Raised in Trust')
        self.assertContains(response, 'Pending Pledges')
        # 4. SBI Banking details
        self.assertContains(response, '45000364554')
        self.assertContains(response, 'SBIN0017847')
        self.assertContains(response, '8722211966@sbi')

    def test_admin_access_control_and_portal(self):
        # Unauthenticated access to /portal/ should redirect to /login/
        portal_url = reverse('admin_portal')
        res_unauth = self.client.get(portal_url)
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn(reverse('admin_login'), res_unauth.url)

        # Login as staff user
        login_res = self.client.login(username='trustee_admin', password='testpassword123')
        self.assertTrue(login_res)

        # Authenticated staff access to /portal/
        res_auth = self.client.get(portal_url)
        self.assertEqual(res_auth.status_code, 200)
        self.assertContains(res_auth, 'Meezan Trust Management Portal')
        self.assertContains(res_auth, 'Financial Figures & Targets')
        self.assertContains(res_auth, 'Activities & Initiatives')
        self.assertContains(res_auth, 'Maintenance Expenses')
        self.assertContains(res_auth, 'Trustees')

        # Update target budget directly from admin portal
        update_url = reverse('update_financial_target', kwargs={'pk': self.initiative.pk})
        res_update = self.client.post(update_url, {
            'target_amount': '450000',
            'is_active': 'on'
        })
        self.assertEqual(res_update.status_code, 302)
        self.initiative.refresh_from_db()
        self.assertEqual(self.initiative.target_amount, Decimal('450000.00'))

    def test_api_create_order_pledge_mode(self):
        """Pledges save directly to DB without launching payment popup."""
        payload = {
            'amount': '5000',
            'donor_name': 'Zameer Ahmed',
            'donor_phone': '+919988776655',
            'donor_email': 'zameer@example.com',
            'initiative': str(self.initiative.id),
            'is_pledge': True,
            'pledge_due_date': '2026-12-31'
        }
        res = self.client.post(
            reverse('api_create_order'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_pledge'])

        # Verify donation created with PENDING status and is_pledge=True
        donation = Donation.objects.get(id=data['donation_id'])
        self.assertEqual(donation.status, 'PENDING')
        self.assertTrue(donation.is_pledge)
        self.assertEqual(donation.amount, Decimal('5000.00'))
        self.assertTrue(donation.razorpay_payment_link.startswith('https://rzp.io/i/'))

    def test_api_create_order_payment_mode(self):
        """Immediate payment creates RazorPay order."""
        payload = {
            'amount': '10000',
            'donor_name': 'Farooq Basha',
            'donor_phone': '+919876543210',
            'donor_email': 'farooq@example.com',
            'initiative': str(self.initiative.id),
            'is_pledge': False
        }
        res = self.client.post(
            reverse('api_create_order'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_pledge'])
        self.assertTrue(data['order_id'].startswith('order_'))
        self.assertEqual(data['amount'], 10000.0)

    def test_payment_verify_and_auto_update_totals(self):
        """Verifying payment updates donation to SUCCESS, issues receipt, and updates totals."""
        initial_metrics = get_donation_metrics()
        initial_raised = initial_metrics['total_raised']

        donation = Donation.objects.create(
            donor=self.donor,
            donor_name='Munawar Khan',
            donor_phone='+919876500000',
            initiative=self.initiative,
            amount=Decimal('8000.00'),
            status='PENDING',
            is_pledge=False,
            razorpay_order_id='order_sim_test_001'
        )

        verify_payload = {
            'donation_id': donation.id,
            'razorpay_order_id': donation.razorpay_order_id,
            'razorpay_payment_id': 'pay_sim_success_123',
            'razorpay_signature': 'simulated_valid_sig'
        }
        res = self.client.post(
            reverse('api_verify_payment'),
            data=json.dumps(verify_payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['receipt_number'].startswith('MEEZAN-REC-'))

        # Confirm donation updated to SUCCESS
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'SUCCESS')
        self.assertEqual(donation.razorpay_payment_id, 'pay_sim_success_123')

        # Confirm Total Raised updated automatically
        updated_metrics = get_donation_metrics()
        self.assertEqual(updated_metrics['total_raised'], initial_raised + Decimal('8000.00'))

    def test_dashboard_metrics(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        metrics = response.context['metrics']
        self.assertGreaterEqual(metrics['total_raised'], Decimal('50000.00'))
        self.assertContains(response, 'Charitable Trust Dynamics Dashboard')
        self.assertContains(response, 'Pending Pledges & Automated WhatsApp Reminders')

    def test_trustees_list(self):
        response = self.client.get(reverse('trustees_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Janab Thousif Mohammed D')
        self.assertContains(response, 'Managing Trustee')
        self.assertContains(response, 'https://linkedin.com/in/letsbdift')

    def test_maintenance_costs(self):
        response = self.client.get(reverse('maintenance_costs'), {'month': 11, 'year': 2026})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meezan Poly Clinic &amp; Pharma Healthcare')
        self.assertContains(response, '25,000.00')

    def test_donate_page_has_sbi_banking_and_qr(self):
        response = self.client.get(reverse('donate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '45000364554')
        self.assertContains(response, 'SBIN0017847')
        self.assertContains(response, '8722211966@sbi')
        self.assertContains(response, 'meezan_sbi_qr.jpg')

    def test_receipt_detail(self):
        res = self.client.get(reverse('receipt_detail', kwargs={'receipt_number': self.completed_donation.receipt_number}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Haji Abdul Sattar')
        self.assertContains(res, '50,000.00')
        self.assertContains(res, 'Meezan Welfare And Charitable Trust')

    def test_activity_photo_management_and_display(self):
        from core.models import ActivityPhoto
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Unauthenticated upload attempt should redirect to login
        res = self.client.get(reverse('photo_create'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_login'), res.url)

        # Login as staff user
        self.client.login(username='trustee_admin', password='testpassword123')

        # Create dummy image file for test upload
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        test_file = SimpleUploadedFile('test_camp.gif', small_gif, content_type='image/gif')

        post_res = self.client.post(reverse('photo_create'), {
            'title': 'Test Free Health Camp in Harapanahalli',
            'initiative': self.initiative.id,
            'image': test_file,
            'caption': 'Volunteers conducting free health checkups and medicine distribution.',
            'location': 'Harapanahalli Main Road',
            'date_taken': '2026-11-13',
            'is_featured': True
        })
        self.assertEqual(post_res.status_code, 302)

        # Confirm photo exists in DB
        photo = ActivityPhoto.objects.filter(title='Test Free Health Camp in Harapanahalli').first()
        self.assertIsNotNone(photo)
        self.assertEqual(photo.location, 'Harapanahalli Main Road')

        # Confirm it renders on the dashboard, initiatives list, and home
        dash_res = self.client.get(reverse('dashboard'))
        self.assertContains(dash_res, 'Test Free Health Camp in Harapanahalli')

        init_res = self.client.get(reverse('initiatives_list'))
        self.assertContains(init_res, 'Test Free Health Camp in Harapanahalli')

        home_res = self.client.get(reverse('home'))
        self.assertContains(home_res, 'Test Free Health Camp in Harapanahalli')
