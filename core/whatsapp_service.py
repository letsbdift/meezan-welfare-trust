import logging
import urllib.parse
from django.conf import settings
from django.utils import timezone
import requests

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.provider = getattr(settings, 'WHATSAPP_PROVIDER', 'mock')
        self.trust_name = getattr(settings, 'TRUST_NAME', 'Meezan Welfare and Charitable Trust')
        self.trust_phone = getattr(settings, 'TRUST_PHONE', '+91 87222 11966')
        self.trust_reg = getattr(settings, 'TRUST_REGISTRATION_NO', '4-00103-2025-26')
        self.trust_upi = getattr(settings, 'TRUST_UPI_ID', '8722211966@sbi')

    def clean_phone(self, phone):
        """Standardize phone to international format without plus sign for wa.me."""
        digits = ''.join(c for c in str(phone) if c.isdigit())
        if len(digits) == 10:
            digits = '91' + digits
        return digits

    def build_direct_link(self, phone, message_text):
        """Generate click-to-chat WhatsApp link."""
        digits = self.clean_phone(phone)
        encoded = urllib.parse.quote(message_text)
        return f"https://wa.me/{digits}?text={encoded}"

    def send_message(self, phone, message_text, recipient_name="Supporter", notification_type="GENERAL_UPDATE", donation=None, event=None, donor=None):
        """
        Dispatches WhatsApp notification and records history in WhatsAppNotification model.
        """
        from .models import WhatsAppNotification

        clean_num = self.clean_phone(phone)
        direct_link = self.build_direct_link(clean_num, message_text)

        notification = WhatsAppNotification.objects.create(
            notification_type=notification_type,
            recipient_name=recipient_name,
            recipient_phone=f"+{clean_num}" if not str(phone).startswith('+') else phone,
            donor=donor,
            event=event,
            donation=donation,
            message_body=message_text,
            direct_wa_link=direct_link,
            status='QUEUED'
        )

        success = False
        provider_id = ''
        error_msg = ''

        # Dispatch based on configured provider
        if self.provider == 'twilio' and getattr(settings, 'TWILIO_ACCOUNT_SID', None):
            success, provider_id, error_msg = self._send_via_twilio(clean_num, message_text)
        elif self.provider == 'cloud_api' and getattr(settings, 'WHATSAPP_CLOUD_TOKEN', None):
            success, provider_id, error_msg = self._send_via_cloud_api(clean_num, message_text)
        else:
            # Mock / Simulated Sandbox Dispatcher
            success = True
            provider_id = f"mock_wa_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"[WhatsApp Mock Dispatch] To: +{clean_num} | Msg: {message_text[:80]}...")

        if success:
            notification.status = 'SENT'
            notification.provider_message_id = provider_id
            notification.sent_at = timezone.now()
        else:
            notification.status = 'FAILED'
            notification.error_message = error_msg

        notification.save()
        return notification

    def _send_via_twilio(self, clean_num, message_text):
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            from_whatsapp = settings.TWILIO_WHATSAPP_FROM
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            payload = {
                'From': from_whatsapp,
                'To': f'whatsapp:+{clean_num}',
                'Body': message_text
            }
            res = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=10)
            if res.status_code in (200, 201):
                return True, res.json().get('sid', ''), ''
            else:
                return False, '', res.text
        except Exception as e:
            return False, '', str(e)

    def _send_via_cloud_api(self, clean_num, message_text):
        try:
            token = settings.WHATSAPP_CLOUD_TOKEN
            phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
            url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'messaging_product': 'whatsapp',
                'to': clean_num,
                'type': 'text',
                'text': {'body': message_text}
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code in (200, 201):
                data = res.json()
                msg_id = data.get('messages', [{}])[0].get('id', '')
                return True, msg_id, ''
            else:
                return False, '', res.text
        except Exception as e:
            return False, '', str(e)

    # ------------------ High-Impact Message Templates ------------------ #

    def send_payment_reminder(self, donation, base_url=""):
        """
        Sends an automated WhatsApp payment / pledge reminder to a donor.
        """
        donor_name = donation.donor_name or "Generous Donor"
        amount = f"₹{donation.amount:,.2f}"
        initiative_title = donation.initiative.title if donation.initiative else "General Welfare Fund"
        
        # Payment link
        pay_url = donation.razorpay_payment_link
        if not pay_url and base_url:
            pay_url = f"{base_url}/donations/pay/{donation.id}/"
        elif not pay_url:
            pay_url = "https://rzp.io/l/aashraya-trust"

        message = (
            f"🙏 *Namaste {donor_name} ji*,\n\n"
            f"Greetings from *{self.trust_name}* (Reg: {self.trust_reg}).\n\n"
            f"This is a gentle reminder regarding your pledged contribution of *{amount}* "
            f"towards our mission: *\"{initiative_title}\"*.\n\n"
            f"✨ *Your support directly impacts lives on the ground!*\n\n"
            f"💳 *Click here to fulfill your pledge securely via RazorPay/UPI:*\n"
            f"👉 {pay_url}\n\n"
            f"📄 *Tax Benefit:* All donations are 50% exempt under Section 80G of the Indian Income Tax Act. "
            f"Your instant 80G receipt will be sent upon completion.\n\n"
            f"For queries or offline transfer, please reply to this message or call us at {self.trust_phone}.\n\n"
            f"With warm gratitude,\n"
            f"Board of Trustees\n"
            f"*{self.trust_name}*"
        )

        return self.send_message(
            phone=donation.donor_phone,
            message_text=message,
            recipient_name=donor_name,
            notification_type='PAYMENT_REMINDER',
            donation=donation,
            donor=donation.donor
        )

    def send_event_advertisement(self, event, donor, base_url=""):
        """
        Sends an automated WhatsApp event advertisement / invitation to a donor.
        """
        donor_name = donor.name if donor else "Valued Supporter"
        event_date_str = event.event_date.strftime("%A, %d %B %Y at %I:%M %p")
        
        event_link = f"{base_url}/events/{event.slug}/" if base_url else ""

        message = (
            f"🌟 *Exclusive Invitation: You are cordially invited!* 🌟\n\n"
            f"Dear *{donor_name}*,\n\n"
            f"We are excited to announce our upcoming trust initiative event:\n\n"
            f"🎪 *{event.title}*\n"
            f"📅 *Date & Time:* {event_date_str}\n"
            f"📍 *Venue:* {event.location}\n\n"
            f"📝 *About the Event:*\n"
            f"{event.description[:280]}...\n\n"
            f"🤝 Come witness first-hand the joy and positive change your support creates!\n\n"
            f"🔗 *View Event Details & RSVP:*\n"
            f"{event_link or 'Visit our website or reply YES to this message to RSVP'}\n\n"
            f"📞 Contact Coordinator: {event.contact_person or 'Trust Office'} ({event.contact_phone or self.trust_phone})\n\n"
            f"Looking forward to welcoming you,\n"
            f"*{self.trust_name}*"
        )

        return self.send_message(
            phone=donor.phone,
            message_text=message,
            recipient_name=donor_name,
            notification_type='EVENT_ADVERTISEMENT',
            event=event,
            donor=donor
        )

    def send_donation_receipt_notification(self, donation, base_url=""):
        """
        Sends WhatsApp confirmation with 80G receipt download link right after successful payment.
        """
        donor_name = donation.donor_name
        amount = f"₹{donation.amount:,.2f}"
        receipt_num = donation.receipt_number
        initiative_title = donation.initiative.title if donation.initiative else "General Welfare Fund"
        receipt_url = f"{base_url}/receipt/{receipt_num}/" if base_url else f"https://trust.org/receipt/{receipt_num}/"

        message = (
            f"🎉 *Donation Received with Heartfelt Gratitude!* 🙏\n\n"
            f"Dear *{donor_name}*,\n\n"
            f"We gratefully acknowledge receipt of your donation of *{amount}* towards *\"{initiative_title}\"*.\n\n"
            f"🧾 *Official Receipt No:* {receipt_num}\n"
            f"🏛 *Trust Reg No:* {self.trust_reg}\n"
            f"📜 *Tax Status:* Eligible for 50% deduction under Section 80G.\n\n"
            f"📥 *Download Your Official 80G Receipt here:*\n"
            f"👉 {receipt_url}\n\n"
            f"Thank you for being a beacon of hope and kindness in our community.\n\n"
            f"Warm regards,\n"
            f"*{self.trust_name}*"
        )

        return self.send_message(
            phone=donation.donor_phone,
            message_text=message,
            recipient_name=donor_name,
            notification_type='DONATION_RECEIPT',
            donation=donation,
            donor=donation.donor
        )

    def send_campaign_appeal(self, donor, initiative=None, custom_message="", base_url=""):
        """
        Sends an activity-targeted or general donation appeal to a donor with personalized greeting and payment details.
        """
        donor_name = donor.name if donor else "Respected Supporter"
        cause_title = initiative.title if initiative else "Community Welfare and Needy Support Drives"
        donate_url = f"{base_url}/donate/" if base_url else "https://meezantrust.in/donate/"

        if custom_message:
            message = custom_message.replace('{donor_name}', donor_name).replace('{name}', donor_name)
            message = message.replace('{cause}', cause_title).replace('{cause_title}', cause_title)
            message = message.replace('{upi_id}', self.trust_upi).replace('{link}', donate_url)
        else:
            message = (
                f"🌟 *Namaste / Assalamu Alaikum {donor_name} ji*,\n\n"
                f"Greetings from *{self.trust_name}* (Reg No: {self.trust_reg}).\n\n"
                f"We are reaching out regarding our critical grassroots mission: *\"{cause_title}\"*.\n\n"
                f"🤝 *Your kind generosity transforms lives on the ground:*\n"
                f"• Clean drinking water, hospital screening, and free generic medicines\n"
                f"• Spoken English & skill coaching for underserved youth\n"
                f"• Monthly dry ration kits for widows and poverty-stricken families\n\n"
                f"💳 *Quick Direct UPI Donation:* `{self.trust_upi}`\n"
                f"🌐 *Online Razorpay / Card / NetBanking:* {donate_url}\n\n"
                f"📄 *All contributions are 50% Tax Exempt under Section 80G.*\n\n"
                f"May your kindness bring blessings and relief to many!\n\n"
                f"With heartfelt regards,\n"
                f"Board of Trustees\n"
                f"*{self.trust_name}* | Harapanahalli\n"
                f"📞 {self.trust_phone}"
            )

        return self.send_message(
            phone=donor.phone,
            message_text=message,
            recipient_name=donor_name,
            notification_type='CAMPAIGN_APPEAL',
            donor=donor
        )


whatsapp_service = WhatsAppService()
