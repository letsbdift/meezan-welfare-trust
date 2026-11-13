from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from core.models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification
)
from core.whatsapp_service import whatsapp_service
from core.razorpay_service import razorpay_service


class MeezanTrustComprehensiveTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Trustee
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
            detailed_description='Promoting brotherhood across Harapanahalli.',
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

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meezan Welfare And Charitable Trust')
        self.assertContains(response, 'Harapanahalli')
        self.assertContains(response, '45000364554') # SBI Account
        self.assertContains(response, 'SBIN0017847') # SBI IFSC
        self.assertContains(response, '8722211966@sbi') # UPI ID

    def test_dashboard_metrics(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        metrics = response.context['metrics']
        self.assertGreaterEqual(metrics['total_raised'], Decimal('50000.00'))
        self.assertGreaterEqual(metrics['total_expected'], Decimal('365000.00'))
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
        self.assertContains(response, 'Meezan Poly Clinic & Pharma Healthcare')
        self.assertContains(response, '25,000.00')

    def test_donate_page_has_sbi_banking_and_qr(self):
        response = self.client.get(reverse('donate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '45000364554')
        self.assertContains(response, 'SBIN0017847')
        self.assertContains(response, '8722211966@sbi')
        self.assertContains(response, 'meezan_sbi_qr.jpg')

    def test_initiatives_list_and_detail(self):
        res_list = self.client.get(reverse('initiatives_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Iftar Koota')

        res_detail = self.client.get(reverse('initiative_detail', kwargs={'slug': self.initiative.slug}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'Iftar Koota')

    def test_receipt_detail(self):
        res = self.client.get(reverse('receipt_detail', kwargs={'receipt_number': self.completed_donation.receipt_number}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Haji Abdul Sattar')
        self.assertContains(res, '50,000.00')
        self.assertContains(res, 'Meezan Welfare And Charitable Trust')
