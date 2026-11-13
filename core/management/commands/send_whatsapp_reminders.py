from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Donation
from core.whatsapp_service import whatsapp_service
from core.razorpay_service import razorpay_service


class Command(BaseCommand):
    help = "Automated worker to send WhatsApp payment reminders for pending pledges and donations"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-overdue',
            type=int,
            default=0,
            help='Filter pledges created or due more than X days ago'
        )

    def handle(self, *args, **options):
        days = options['days_overdue']
        self.stdout.write(self.style.NOTICE(f"Scanning for pending pledges... (Filter: {days} days)"))

        pending_donations = Donation.objects.filter(status='PENDING')
        
        sent_count = 0
        for donation in pending_donations:
            if not donation.donor_phone:
                continue

            # Ensure RazorPay payment link exists
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

            notification = whatsapp_service.send_payment_reminder(donation)
            self.stdout.write(self.style.SUCCESS(
                f"Dispatched reminder to {donation.donor_name} ({donation.donor_phone}) - INR {donation.amount} [Status: {notification.status}]"
            ))
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished sending {sent_count} WhatsApp payment reminders."))
