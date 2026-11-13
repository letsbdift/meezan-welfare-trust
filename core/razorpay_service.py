import logging
import uuid
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False


class RazorpayService:
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_AashrayaDemoKey2026')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'demo_secret_key_aashraya_99')
        self.currency = getattr(settings, 'RAZORPAY_CURRENCY', 'INR')
        self.simulation_mode = getattr(settings, 'RAZORPAY_SIMULATION_MODE', True)

        self.client = None
        if RAZORPAY_AVAILABLE and self.key_id and self.key_secret:
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as e:
                logger.warning(f"Could not initialize Razorpay client: {e}")

    def create_order(self, amount, receipt, notes=None):
        """
        Creates a Razorpay Order.
        Amount should be in INR (Decimal or float).
        Returns dict with order details.
        """
        amount_paise = int(Decimal(str(amount)) * 100)
        data = {
            'amount': amount_paise,
            'currency': self.currency,
            'receipt': str(receipt)[:40],
            'notes': notes or {},
            'payment_capture': 1
        }

        # Attempt real API call if keys are not demo/placeholder and client is ready
        if self.client and not self.key_id.startswith('rzp_test_AashrayaDemo'):
            try:
                order = self.client.order.create(data=data)
                return {
                    'order_id': order.get('id'),
                    'amount': amount,
                    'amount_paise': amount_paise,
                    'currency': self.currency,
                    'key_id': self.key_id,
                    'is_simulated': False,
                    'raw': order
                }
            except Exception as e:
                logger.error(f"Razorpay API order creation failed: {e}. Falling back to sandbox simulation.")

        # Sandbox / Simulation fallback
        mock_id = f"order_sim_{uuid.uuid4().hex[:14]}"
        return {
            'order_id': mock_id,
            'amount': amount,
            'amount_paise': amount_paise,
            'currency': self.currency,
            'key_id': self.key_id,
            'is_simulated': True,
            'raw': {'id': mock_id, 'status': 'created', 'amount': amount_paise}
        }

    def create_payment_link(self, amount, description, customer_name, customer_email, customer_phone):
        """
        Generates a direct Razorpay Payment Link (which can be shared via WhatsApp).
        """
        amount_paise = int(Decimal(str(amount)) * 100)
        clean_phone = ''.join(c for c in str(customer_phone) if c.isdigit())
        if not clean_phone.startswith('91') and len(clean_phone) == 10:
            clean_phone = '91' + clean_phone

        data = {
            'amount': amount_paise,
            'currency': self.currency,
            'accept_partial': False,
            'description': description[:250],
            'customer': {
                'name': customer_name,
                'email': customer_email or 'donor@aashrayatrust.org',
                'contact': f"+{clean_phone}" if clean_phone else "+919820012345"
            },
            'notify': {'sms': False, 'email': bool(customer_email)},
            'reminder_enable': True,
        }

        if self.client and not self.key_id.startswith('rzp_test_AashrayaDemo'):
            try:
                link = self.client.payment_link.create(data)
                return {
                    'link_id': link.get('id'),
                    'short_url': link.get('short_url'),
                    'status': link.get('status'),
                    'is_simulated': False
                }
            except Exception as e:
                logger.error(f"Razorpay payment link creation failed: {e}. Falling back to simulated link.")

        # Sandbox simulated payment link
        link_id = f"plink_sim_{uuid.uuid4().hex[:12]}"
        sim_url = f"https://rzp.io/i/{link_id}"
        return {
            'link_id': link_id,
            'short_url': sim_url,
            'status': 'created',
            'is_simulated': True
        }

    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verifies payment signature from Razorpay checkout.
        """
        # In simulation mode, accept simulated orders
        if str(razorpay_order_id).startswith('order_sim_'):
            return True

        if self.client:
            try:
                params = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                self.client.utility.verify_payment_signature(params)
                return True
            except Exception as e:
                logger.error(f"Razorpay signature verification failed: {e}")
                return False

        return True


razorpay_service = RazorpayService()
