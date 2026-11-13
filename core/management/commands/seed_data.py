from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from core.models import (
    Initiative, Event, Trustee, Donor, Donation,
    MaintenanceActivity, MaintenanceExpense, WhatsAppNotification
)
from core.whatsapp_service import whatsapp_service
from core.razorpay_service import razorpay_service


class Command(BaseCommand):
    help = "Seeds comprehensive sample data for Meezan Welfare And Charitable Trust Harapanahalli"

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for Meezan Welfare And Charitable Trust Harapanahalli...")

        # 1. Trustees
        trustees_data = [
            {
                'name': 'Janab Thousif Mohammed D',
                'designation': 'Founder & Managing Trustee',
                'bio': 'Dedicated community leader and social reformer leading grassroots initiatives in Harapanahalli, including interfaith Iftar Koota, free drinking water distribution, and the establishment of city-wide Baitul Maal.',
                'quote': 'Serving humanity with compassion, communal unity, and sincere dedication is the noble mission of Meezan Trust.',
                'order': 1,
                'email': 'thousif.mohammed.d@gmail.com',
                'phone': '+91 87222 11966',
                'linkedin_url': 'https://www.linkedin.com/in/letsbdift',
                'twitter_url': 'https://x.com/MeezanTrustHpli',
                'facebook_url': 'https://facebook.com/MeezanWelfareTrustHpli',
                'instagram_url': 'https://instagram.com/meezan_trust_harapanahalli',
            },
            {
                'name': 'Dr. K. M. Abdul Rasheed',
                'designation': 'Trustee - Healthcare & Meezan Poly Clinic Director',
                'bio': 'Senior medical consultant supervising free health check-up camps, voluntary blood donation drives, and primary care at Meezan Poly Clinic & Pharma.',
                'quote': 'Affordable primary healthcare is a fundamental right. Meezan Clinic ensures no patient goes without medicine.',
                'order': 2,
                'email': 'clinic@meezantrust.org',
                'phone': '+91 87222 11966',
                'linkedin_url': 'https://www.linkedin.com/in/meezan-healthcare',
                'twitter_url': 'https://x.com/MeezanClinic',
                'facebook_url': 'https://facebook.com/MeezanPolyClinic',
                'instagram_url': 'https://instagram.com/meezan_polyclinic',
            },
            {
                'name': 'Janab Mohammed Ilyas, M.Com',
                'designation': 'Treasurer & Baitul Maal Auditor',
                'bio': 'Financial auditor and community treasurer maintaining 100% transparent registers of Zakat, Sadaqah, and public donations for the Baitul Maal and ration distribution.',
                'quote': 'Every rupee entrusted to Meezan Trust reaches deserving widows, orphans, and families with utmost transparency.',
                'order': 3,
                'email': 'treasurer@meezantrust.org',
                'phone': '+91 87222 11966',
                'linkedin_url': 'https://www.linkedin.com/in/meezan-treasury',
                'twitter_url': 'https://x.com/MeezanTrust',
                'facebook_url': 'https://facebook.com/MeezanWelfareTrustHpli',
                'instagram_url': 'https://instagram.com/meezan_trust',
            },
            {
                'name': 'Janab Syed Khaja',
                'designation': 'Trustee - Youth Education & Community Drives',
                'bio': 'Educationist coordinating Free Spoken English coaching classes for students and organizing youth volunteers for city cleanliness and summer water distribution.',
                'quote': 'Empowering our youth with communication skills and civic responsibility builds a brighter tomorrow for Harapanahalli.',
                'order': 4,
                'email': 'education@meezantrust.org',
                'phone': '+91 87222 11966',
                'linkedin_url': 'https://www.linkedin.com/in/meezan-education',
                'twitter_url': 'https://x.com/MeezanYouth',
                'facebook_url': 'https://facebook.com/MeezanWelfareTrustHpli',
                'instagram_url': 'https://instagram.com/meezan_youth_hpli',
            },
        ]

        for t in trustees_data:
            Trustee.objects.update_or_create(name=t['name'], defaults=t)
        self.stdout.write(self.style.SUCCESS("[OK] Trustees seeded"))

        # 2. Maintenance Activities
        activities_data = [
            {'name': 'Meezan Poly Clinic & Pharma Healthcare', 'code': 'clinic-pharma', 'icon': 'fa-notes-medical', 'color_hex': '#ef4444', 'description': 'Affordable primary healthcare, subsidized generic medicines, doctor consultations, and clinic maintenance in Harapanahalli.'},
            {'name': 'Free Drinking Water Distribution (15 Circles)', 'code': 'summer-water', 'icon': 'fa-faucet-drip', 'color_hex': '#06b6d4', 'description': 'Clean, chilled water tanks across 15 major circles in Harapanahalli during the scorching summer months.'},
            {'name': 'Baitul Maal Social Welfare & Destitute Support', 'code': 'baitul-maal', 'icon': 'fa-hand-holding-heart', 'color_hex': '#10b981', 'description': 'Structured monthly financial support for poorest families, emergency widow pensions, and micro relief grants.'},
            {'name': 'Free Food Ration Kits Distribution', 'code': 'ration-distribution', 'icon': 'fa-utensils', 'color_hex': '#f59e0b', 'description': 'Bulk grocery supplies (rice, flour, oil, pulses) for widows, orphans, and distressed households.'},
            {'name': 'Spoken English & Educational Center', 'code': 'spoken-english', 'icon': 'fa-graduation-cap', 'color_hex': '#3b82f6', 'description': 'Free communication skills classes, study materials, projector, and classroom facility maintenance.'},
            {'name': 'Blood Donation & Free Medical Camps', 'code': 'blood-health-camps', 'icon': 'fa-heart-pulse', 'color_hex': '#e11d48', 'description': 'Medical camp diagnostics, blood grouping kits, paramedic honorarium, and donor refreshments.'},
            {'name': 'City Cleanliness & Environmental Drives', 'code': 'city-cleaning', 'icon': 'fa-broom', 'color_hex': '#8b5cf6', 'description': 'Waste collection bins, sanitization materials, safety gloves, and civic cleanliness campaigns during Eid and festivals.'},
        ]

        act_objs = {}
        for a in activities_data:
            obj, _ = MaintenanceActivity.objects.update_or_create(name=a['name'], defaults=a)
            act_objs[a['code']] = obj
        self.stdout.write(self.style.SUCCESS("[OK] Maintenance Activities seeded"))

        # 3. Monthly Maintenance Expenses (November & October 2026)
        expenses_data = [
            # November 2026
            {'activity': act_objs['clinic-pharma'], 'month': 11, 'year': 2026, 'title': 'Essential Generic Medicines Stock for Meezan Pharma & Clinic', 'amount': Decimal('48500.00'), 'date_incurred': date(2026, 11, 2), 'vendor_payee': 'Karnataka Generic Pharma Distributors, Davanagere', 'bill_voucher_number': 'VOUCH/MEEZAN/11/01'},
            {'activity': act_objs['clinic-pharma'], 'month': 11, 'year': 2026, 'title': 'Visiting Doctor & Paramedic Monthly Honorarium', 'amount': Decimal('25000.00'), 'date_incurred': date(2026, 11, 4), 'vendor_payee': 'Meezan Clinic Paramedical Staff', 'bill_voucher_number': 'VOUCH/MEEZAN/11/02'},
            {'activity': act_objs['summer-water'], 'month': 11, 'year': 2026, 'title': 'Maintenance & Descaling of Water Tanks for Public Kiosks', 'amount': Decimal('16200.00'), 'date_incurred': date(2026, 11, 5), 'vendor_payee': 'Sri Manjunatha Water Works Harapanahalli', 'bill_voucher_number': 'VOUCH/MEEZAN/11/03'},
            {'activity': act_objs['baitul-maal'], 'month': 11, 'year': 2026, 'title': 'Monthly Dignified Widow Grants & Destitute Family Assistance (22 families)', 'amount': Decimal('44000.00'), 'date_incurred': date(2026, 11, 1), 'vendor_payee': 'Baitul Maal Verified Beneficiary Direct Fund', 'bill_voucher_number': 'VOUCH/MEEZAN/11/04'},
            {'activity': act_objs['ration-distribution'], 'month': 11, 'year': 2026, 'title': 'Bulk Ration Kits (Rice, Sona Masoori, Toor Dal, Oil) for 75 Families', 'amount': Decimal('62500.00'), 'date_incurred': date(2026, 11, 6), 'vendor_payee': 'APMC Wholesale Grain Mart, Harapanahalli', 'bill_voucher_number': 'VOUCH/MEEZAN/11/05'},
            {'activity': act_objs['spoken-english'], 'month': 11, 'year': 2026, 'title': 'Spoken English Learning Center Rent & Student Workbook Printing', 'amount': Decimal('18000.00'), 'date_incurred': date(2026, 11, 3), 'vendor_payee': 'Shree Balaji Offset Printers & Center Landlord', 'bill_voucher_number': 'VOUCH/MEEZAN/11/06'},
            {'activity': act_objs['blood-health-camps'], 'month': 11, 'year': 2026, 'title': 'Blood Donation Camp Test Kits, Donor Refreshments, Certificates', 'amount': Decimal('12500.00'), 'date_incurred': date(2026, 11, 7), 'vendor_payee': 'District Red Cross Blood Bank & Ananya Caterers', 'bill_voucher_number': 'VOUCH/MEEZAN/11/07'},
            {'activity': act_objs['city-cleaning'], 'month': 11, 'year': 2026, 'title': 'Sanitization Bleaching Powder, Trash Bags & Safety Gear for Eid Cleanliness', 'amount': Decimal('11800.00'), 'date_incurred': date(2026, 11, 8), 'vendor_payee': 'Kaveri Hardware & Sanitation Depot', 'bill_voucher_number': 'VOUCH/MEEZAN/11/08'},

            # October 2026
            {'activity': act_objs['ration-distribution'], 'month': 10, 'year': 2026, 'title': 'Emergency Ration Kits Distribution during Unseasonal Rains', 'amount': Decimal('54000.00'), 'date_incurred': date(2026, 10, 18), 'vendor_payee': 'APMC Merchant Yard', 'bill_voucher_number': 'VOUCH/MEEZAN/10/01'},
            {'activity': act_objs['clinic-pharma'], 'month': 10, 'year': 2026, 'title': 'BP Monitors, Glucometer Strips & Antibiotic Stock for Clinic', 'amount': Decimal('38000.00'), 'date_incurred': date(2026, 10, 12), 'vendor_payee': 'Davanagere Medical Agencies', 'bill_voucher_number': 'VOUCH/MEEZAN/10/02'},
            {'activity': act_objs['baitul-maal'], 'month': 10, 'year': 2026, 'title': 'Baitul Maal Educational Fee Assistance for 14 Poor Students', 'amount': Decimal('35000.00'), 'date_incurred': date(2026, 10, 22), 'vendor_payee': 'Direct School Accounts Harapanahalli', 'bill_voucher_number': 'VOUCH/MEEZAN/10/03'},
        ]

        for exp in expenses_data:
            MaintenanceExpense.objects.update_or_create(
                bill_voucher_number=exp['bill_voucher_number'],
                defaults=exp
            )
        self.stdout.write(self.style.SUCCESS("[OK] Monthly Maintenance Expenses seeded"))

        # 4. Initiatives: The 9 Core Activities of Meezan Trust Harapanahalli
        initiatives_data = [
            {
                'title': '1. Iftar Koota Interfaith Harmony Gathering',
                'category': 'HUNGER',
                'short_description': 'A special interfaith gathering during Ramadan inviting people from all religions to promote unity, peace, and brotherhood in Harapanahalli.',
                'detailed_description': 'The Iftar Koota Program is our flagship communal harmony event in Harapanahalli. During the holy month of Ramadan, we bring together citizens, religious leaders, elders, and youth from Hindu, Muslim, Christian, and Jain communities around a shared banquet. It fosters deep mutual respect, removes barriers, and strengthens communal unity across the taluk.',
                'target_amount': Decimal('350000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '2. Free Ration Kit Distribution for Widows & Needy',
                'category': 'HUNGER',
                'short_description': 'Providing wholesome monthly ration kits (rice, atta, pulses, cooking oil) to widows, orphans, disabled, and destitute families.',
                'detailed_description': 'Meezan Trust identifies the most vulnerable families across Harapanahalli taluk through a dignified verification process. Each kit supplies essential staple food grains to ensure no widow, orphan, or impoverished family goes to bed hungry.',
                'target_amount': Decimal('600000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '3. Free Spoken English & Communication Classes',
                'category': 'EDUCATION',
                'short_description': 'Empowering underprivileged youth and government school students with spoken English skills for brighter future opportunities.',
                'detailed_description': 'Language and confidence should never become obstacles to a student\'s success. We run daily spoken English classes with interactive modules, grammar coaching, public speaking drills, and personality development to enable students to excel in job interviews and higher education.',
                'target_amount': Decimal('250000.00'),
                'is_active': True,
                'is_featured': False,
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '4. Voluntary Blood Donation Camp Drives',
                'category': 'HEALTHCARE',
                'short_description': 'Mobilizing voluntary blood donors to maintain adequate blood bank supplies for medical emergencies and save precious lives.',
                'detailed_description': 'In medical emergencies, timely blood availability saves lives. Meezan Trust organizes periodic mega blood donation camps in Harapanahalli in coordination with licensed district government blood banks, encouraging healthy youth to voluntarily donate blood.',
                'target_amount': Decimal('150000.00'),
                'is_active': True,
                'is_featured': False,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '5. Free Health & Medical Screening Camps',
                'category': 'HEALTHCARE',
                'short_description': 'Comprehensive medical check-ups, BP/diabetes tests, doctor consultations, and hygiene awareness for the underserved.',
                'detailed_description': 'Organizing free diagnostic and health camps in rural and semi-urban pockets of Harapanahalli. Specialist doctors provide checkups, diagnose chronic illnesses, dispense free medicines, and educate families on preventive sanitation and hygiene.',
                'target_amount': Decimal('400000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '6. City Cleaning & Sanitation Campaigns',
                'category': 'ENVIRONMENT',
                'short_description': 'Organizing waste disposal, sanitation, and street cleanliness drives across Harapanahalli during Eid and public festivals.',
                'detailed_description': 'Cleanliness is an integral part of faith and civic responsibility. Our youth volunteers actively clean public streets, manage waste disposal during festival gatherings, disinfect community areas, and distribute awareness pamphlets on civic hygiene.',
                'target_amount': Decimal('120000.00'),
                'is_active': True,
                'is_featured': False,
                'start_date': date(2026, 3, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '7. Free Drinking Water Distribution (15 Major Circles)',
                'category': 'ENVIRONMENT',
                'short_description': 'Supplying clean and safe drinking water kiosks across 15 major circles of Harapanahalli during severe summer months.',
                'detailed_description': 'Harapanahalli experiences harsh summer heat. Meezan Trust deploys clean drinking water tanks, coolers, and earthen pots at 15 prominent traffic junctions and bus circles so daily laborers, pedestrians, and travelers can quench their thirst free of charge.',
                'target_amount': Decimal('300000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 3, 1),
                'end_date': date(2026, 6, 30),
            },
            {
                'title': '8. Meezan Poly Clinic & Meezan Pharma',
                'category': 'HEALTHCARE',
                'short_description': 'Affordable primary healthcare dispensary and pharmacy providing subsidized generic medicines and consultations.',
                'detailed_description': 'Meezan Poly Clinic & Pharma operates as a community healthcare beacon in Harapanahalli, delivering quality primary medical consultations, minor treatments, diabetic monitoring, and essential generic medicines at deeply subsidized, affordable rates for all citizens.',
                'target_amount': Decimal('850000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
            {
                'title': '9. Setting Up Baitul Maal for Harapanahalli City',
                'category': 'GENERAL',
                'short_description': 'A structured, audited financial support system to assist poorest families with dignity, micro-grants, and 100% transparency.',
                'detailed_description': 'The Baitul Maal initiative establishes an institutional community treasury in Harapanahalli to pool Zakat, Sadaqah, and charity funds. The system systematically audits and delivers financial aid for medical emergencies, widow sustenance, basic shelter repairs, and small livelihood micro-grants.',
                'target_amount': Decimal('1200000.00'),
                'is_active': True,
                'is_featured': True,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            },
        ]

        init_objs = {}
        for init in initiatives_data:
            obj, _ = Initiative.objects.update_or_create(title=init['title'], defaults=init)
            init_objs[init['title']] = obj
        self.stdout.write(self.style.SUCCESS("[OK] 9 Core Initiatives seeded"))

        # 5. Events
        now = timezone.now()
        events_data = [
            {
                'title': 'Grand Interfaith Iftar Koota 2026',
                'description': 'Annual interfaith gathering bringing together leaders, citizens, and youth of all religions across Harapanahalli to break bread, foster brotherhood, and celebrate communal harmony.',
                'event_date': now + timedelta(days=12, hours=3),
                'location': 'Meezan Community Grounds, Main Road, Harapanahalli',
                'status': 'UPCOMING',
                'capacity': 800,
                'contact_person': 'Janab Thousif Mohammed D',
                'contact_phone': '+91 87222 11966',
            },
            {
                'title': 'Meezan Mega Blood Donation Camp - Harapanahalli',
                'description': 'Voluntary blood donation camp in association with District Blood Bank to assist regional hospital trauma and maternity wards.',
                'event_date': now + timedelta(days=24, hours=2),
                'location': 'Meezan Poly Clinic Premises, Station Road, Harapanahalli',
                'status': 'UPCOMING',
                'capacity': 200,
                'contact_person': 'Dr. K. M. Abdul Rasheed',
                'contact_phone': '+91 87222 11966',
            },
            {
                'title': 'Free Ration Kits Distribution Drive for 150 Families',
                'description': 'Distribution of monthly grocery packets to verified widows, senior citizens, and needy households.',
                'event_date': now + timedelta(days=35, hours=1),
                'location': 'Baitul Maal Center, Harapanahalli Town',
                'status': 'UPCOMING',
                'capacity': 300,
                'contact_person': 'Janab Mohammed Ilyas',
                'contact_phone': '+91 87222 11966',
            },
            {
                'title': 'Summer Drinking Water Kiosk Inauguration across 15 Circles',
                'description': 'Inaugurating clean chilled drinking water kiosks across 15 major circles of Harapanahalli to provide summer relief.',
                'event_date': now - timedelta(days=18),
                'location': 'Bus Stand Circle, Gandhi Chowk, & 13 other junctions, Harapanahalli',
                'status': 'COMPLETED',
                'capacity': 500,
                'contact_person': 'Janab Syed Khaja',
                'contact_phone': '+91 87222 11966',
            },
        ]

        for ev in events_data:
            Event.objects.update_or_create(title=ev['title'], defaults=ev)
        self.stdout.write(self.style.SUCCESS("[OK] Events seeded"))

        # 6. Donors & Donations (Completed + Pending Pledges with Banking & UPI)
        donors_data = [
            {'name': 'Haji Abdul Sattar', 'email': 'abdul.sattar@gmail.com', 'phone': '+919845112233', 'pan_number': 'AAAPA1234F', 'city': 'Harapanahalli'},
            {'name': 'Shri Manjunatha Swamy', 'email': 'manjunath.swamy@gmail.com', 'phone': '+919845223344', 'pan_number': 'ABCPM5678K', 'city': 'Harapanahalli'},
            {'name': 'Janab Tariq Anwar', 'email': 'tariq.anwar@gmail.com', 'phone': '+919845334455', 'pan_number': 'ACDPT9012M', 'city': 'Davanagere'},
            {'name': 'Smt. Fatima Bi', 'email': 'fatima.bi@gmail.com', 'phone': '+919845445566', 'pan_number': 'ADEFP3456L', 'city': 'Harapanahalli'},
            {'name': 'Shri R. K. Patil', 'email': 'rkpatil.merchant@gmail.com', 'phone': '+919845556677', 'pan_number': 'AFGPP7890N', 'city': 'Ballari'},
            {'name': 'Mohammed Zameer', 'email': 'zameer.m@gmail.com', 'phone': '+919845667788', 'pan_number': 'AGHPZ1234P', 'city': 'Harapanahalli'},
        ]

        donor_objs = []
        for d in donors_data:
            obj, _ = Donor.objects.update_or_create(phone=d['phone'], defaults=d)
            donor_objs.append(obj)

        donations_data = [
            {
                'donor': donor_objs[0],
                'donor_name': donor_objs[0].name,
                'donor_email': donor_objs[0].email,
                'donor_phone': donor_objs[0].phone,
                'pan_number': donor_objs[0].pan_number,
                'initiative': init_objs['9. Setting Up Baitul Maal for Harapanahalli City'],
                'amount': Decimal('200000.00'),
                'status': 'SUCCESS',
                'donation_type': 'CAMPAIGN_SPECIFIC',
                'payment_method': 'UPI',
                'razorpay_payment_id': 'sbi_upi_8722211966_01',
                'receipt_number': 'MEEZAN-202610-01',
                'notes': 'Zakat contribution via SBI UPI ID 8722211966@sbi for Baitul Maal',
            },
            {
                'donor': donor_objs[1],
                'donor_name': donor_objs[1].name,
                'donor_email': donor_objs[1].email,
                'donor_phone': donor_objs[1].phone,
                'pan_number': donor_objs[1].pan_number,
                'initiative': init_objs['1. Iftar Koota Interfaith Harmony Gathering'],
                'amount': Decimal('100000.00'),
                'status': 'SUCCESS',
                'donation_type': 'CAMPAIGN_SPECIFIC',
                'payment_method': 'BANK_TRANSFER',
                'razorpay_payment_id': 'sbi_neft_45000364554_01',
                'receipt_number': 'MEEZAN-202610-02',
                'notes': 'NEFT transfer to SBI A/C 45000364554 for Interfaith Iftar Koota',
            },
            {
                'donor': donor_objs[2],
                'donor_name': donor_objs[2].name,
                'donor_email': donor_objs[2].email,
                'donor_phone': donor_objs[2].phone,
                'pan_number': donor_objs[2].pan_number,
                'initiative': init_objs['8. Meezan Poly Clinic & Meezan Pharma'],
                'amount': Decimal('150000.00'),
                'status': 'SUCCESS',
                'donation_type': 'CAMPAIGN_SPECIFIC',
                'payment_method': 'RAZORPAY_CHECKOUT',
                'razorpay_payment_id': 'pay_meezan_clinic_03',
                'receipt_number': 'MEEZAN-202611-03',
                'notes': 'Subsidized medicines purchase for Meezan Pharma',
            },
            {
                'donor': donor_objs[3],
                'donor_name': donor_objs[3].name,
                'donor_email': donor_objs[3].email,
                'donor_phone': donor_objs[3].phone,
                'pan_number': donor_objs[3].pan_number,
                'initiative': init_objs['2. Free Ration Kit Distribution for Widows & Needy'],
                'amount': Decimal('75000.00'),
                'status': 'SUCCESS',
                'donation_type': 'ONE_TIME',
                'payment_method': 'UPI',
                'razorpay_payment_id': 'sbi_upi_8722211966_04',
                'receipt_number': 'MEEZAN-202611-04',
                'notes': 'Ration kits for 50 destitute families',
            },
            {
                'donor': donor_objs[4],
                'donor_name': donor_objs[4].name,
                'donor_email': donor_objs[4].email,
                'donor_phone': donor_objs[4].phone,
                'pan_number': donor_objs[4].pan_number,
                'initiative': init_objs['7. Free Drinking Water Distribution (15 Major Circles)'],
                'amount': Decimal('50000.00'),
                'status': 'SUCCESS',
                'donation_type': 'ONE_TIME',
                'payment_method': 'BANK_TRANSFER',
                'razorpay_payment_id': 'sbi_neft_45000364554_05',
                'receipt_number': 'MEEZAN-202611-05',
                'notes': 'Summer water distribution at Harapanahalli Bus Stand circle',
            },

            # PLEDGES FOR UPCOMING INITIATIVES
            {
                'donor': donor_objs[5],
                'donor_name': donor_objs[5].name,
                'donor_email': donor_objs[5].email,
                'donor_phone': donor_objs[5].phone,
                'pan_number': donor_objs[5].pan_number,
                'initiative': init_objs['3. Free Spoken English & Communication Classes'],
                'amount': Decimal('25000.00'),
                'status': 'PENDING',
                'donation_type': 'MONTHLY_PLEDGE',
                'is_pledge': True,
                'pledge_due_date': date(2026, 11, 28),
                'payment_method': 'RAZORPAY_LINK',
                'razorpay_payment_link': 'https://rzp.io/i/meezan_pledge_english_25k',
                'notes': 'Pledged student workbooks & teacher honorarium',
            },
        ]

        for dn in donations_data:
            Donation.objects.update_or_create(
                donor_phone=dn['donor_phone'],
                amount=dn['amount'],
                status=dn['status'],
                defaults=dn
            )
        self.stdout.write(self.style.SUCCESS("[OK] Donors & Donations seeded"))

        # 7. WhatsApp notification
        pending_dn = Donation.objects.filter(status='PENDING').first()
        if pending_dn:
            whatsapp_service.send_payment_reminder(pending_dn, base_url="http://127.0.0.1:8000")
            self.stdout.write(self.style.SUCCESS("[OK] Dispatched WhatsApp reminder"))

        upcoming_ev = Event.objects.filter(status='UPCOMING').first()
        first_donor = Donor.objects.first()
        if upcoming_ev and first_donor:
            whatsapp_service.send_event_advertisement(upcoming_ev, first_donor, base_url="http://127.0.0.1:8000")
            self.stdout.write(self.style.SUCCESS("[OK] Dispatched WhatsApp event ad"))

        self.stdout.write(self.style.SUCCESS("Meezan Trust Harapanahalli data seeding completed successfully!"))
