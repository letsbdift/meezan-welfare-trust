# Aashraya Seva Charitable Trust Web Application

A full-featured, responsive Django web application designed for charitable trusts and non-profits, featuring dynamic donation metric tracking (Expected, Raised, Pending amounts), transparent monthly maintenance cost breakdowns per activity, trustee leadership directory with social links, RazorPay gateway integration, and automated WhatsApp notifications for payment reminders and event advertisements.

---

## Key Features

1. **Dynamic Trust & Donation Dashboard**
   - **Real-Time Metrics Ticker**:
     - **Expected Amount**: Total financial goals across all active campaigns + outstanding pledges.
     - **Raised Amount**: Sum of all completed, verified contributions received.
     - **Pending Amount**: Remaining funds required to achieve targets + overdue pledges.
     - **Goal Fulfillment Ratio**: Interactive gauge and progress visualization.
   - **Dynamic Chart.js Visualizations**:
     - Fund Fulfillment Comparison Doughnut Chart (Raised vs Pending vs Target).
     - 12-Month Donation Growth Trend (Verified monthly influx).
     - Monthly Maintenance Cost Distribution across 7 charitable activity categories.
   - **Pending Pledges Action Register**:
     - Follow-up table with 1-click **"Send WhatsApp Reminder"** buttons containing direct RazorPay links.
   - **Recent Donations Feed**:
     - Real-time stream of verified donors with one-click access to download formal 80G receipts.

2. **Content Management for Initiatives & Events**
   - **Initiatives / Causes Directory**:
     - Category filter (Healthcare, Education, Hunger Relief, Shelter, Environment, Disaster Relief).
     - Target goals, real-time progress bars, backer counts, and banner uploads.
   - **Events & Volunteer Drives**:
     - Upcoming vs completed event schedules with date, venue, capacity, and RSVP integration.
     - Built-in **"Broadcast Event Advertisement"** action sending WhatsApp invitations to registered donors.
   - **Trustee Admin Upload Portal**:
     - Simple web forms to publish new initiatives, schedule events, upload media, and manage board member profiles.

3. **Monthly Maintenance Cost Breakdowns per Activity**
   - **100% Financial Transparency & Accountability**:
     - Dedicated monthly audit explorer with month & year filter.
     - Operational breakdown across 7 primary activities:
       1. Nutrition & Community Kitchen (Annadanam)
       2. Mobile Medical Camps & Free Medicines
       3. Child Education & Learning Center Supplies
       4. Shelter Home & Old Age Care Upkeep
       5. Utilities, Clean Drinking Water & Solar Facilities
       6. Emergency Ambulance & Field Logistics
       7. Administrative, Audit & Staff Honorarium
     - Itemized audit log table with bill voucher numbers, vendor payees, date incurred, amounts, and receipt voucher uploads.
     - Printable audit report with one-click PDF print view.

4. **Dedicated Board of Trustees Directory with Social Media Links**
   - Elegant, responsive profile cards for leadership and board members.
   - Full biographies, humanitarian contributions, and vision quotes.
   - Direct, clickable social media profile buttons:
     - LinkedIn
     - Twitter / X
     - Facebook
     - Instagram
     - Direct Email and WhatsApp messaging
   - Fiduciary code of conduct declaration (zero remuneration/dividend policy).

5. **RazorPay Payment Gateway Integration**
   - Standard Razorpay Checkout modal (supporting Cards, UPI, NetBanking, GPay, PhonePe, Paytm).
   - Razorpay Payment Link generation (`https://rzp.io/i/...`) for pledge fulfillment.
   - Configurable live API keys or sandbox test mode with simulated checkout for immediate local testing.
   - Automatic Section 80G Donation Receipt generation with unique alphanumeric receipt ID (e.g. `TR-202611-ABCD`).
   - Printable 80G tax receipt view complete with registration number, PAN, and digital seal.

6. **Automated WhatsApp Notification Engine**
   - **Automated Payment & Pledge Reminders**:
     - Personalized salutations, contribution amount, campaign details, and direct RazorPay payment links.
   - **Automated Event Advertisements & Invitations**:
     - Broadcasts event date, venue, description, and RSVP links to all trust supporters.
   - **Instant Donation Receipts**:
     - Automated WhatsApp acknowledgment with 80G receipt download link dispatched right after successful payment.
   - **Delivery Backends**:
     - Supports Twilio WhatsApp API, Meta WhatsApp Cloud API, and local Mock Sandbox.
     - Built-in `https://wa.me/...` direct click-to-chat fallback links for instant browser/app dispatch.
   - **Background Worker**:
     - CLI command `python manage.py send_whatsapp_reminders` for cron jobs or scheduled tasks.

---

## Project Structure

```
trust_web_app/
├── manage.py
├── db.sqlite3
├── .env.example
├── README.md
├── trust_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── models.py                   # Initiatives, Events, Trustees, Donors, Donations, Expenses, WhatsApp
│   ├── views.py                    # Dashboard, Public views, Razorpay verify, WhatsApp actions
│   ├── forms.py                    # Forms for donations, initiatives, events, expenses, trustees
│   ├── urls.py                     # Route mappings
│   ├── admin.py                    # Custom Django admin interface
│   ├── razorpay_service.py         # Razorpay Python SDK integration & sandbox fallback
│   ├── whatsapp_service.py         # WhatsApp messaging dispatcher (Twilio, Cloud API, Mock, wa.me)
│   ├── context_processors.py       # Exposes trust info globally to templates
│   ├── tests.py                    # Comprehensive test suite (9 unit tests)
│   └── management/
│       └── commands/
│           ├── seed_data.py                # Pre-populates realistic data
│           └── send_whatsapp_reminders.py  # Automated cron worker for pending pledges
├── templates/
│   ├── base.html                   # Master layout with responsive navbar, footer & WhatsApp button
│   └── core/
│       ├── home.html               # Public landing page with live ticker, causes & events
│       ├── dashboard.html          # Dynamic Dashboard tracking Expected, Raised, and Pending amounts
│       ├── initiatives_list.html   # Causes directory with category filters
│       ├── initiative_detail.html  # Initiative page with goals & Razorpay checkout
│       ├── events_list.html        # Upcoming & past events directory
│       ├── event_detail.html       # Event page with RSVP & WhatsApp broadcast trigger
│       ├── trustees_list.html      # Dedicated section for Trustee profiles with social links
│       ├── maintenance_costs.html  # Monthly maintenance cost breakdowns per activity
│       ├── donate.html             # Donation page with preset amounts & pledge toggle
│       ├── razorpay_checkout.html  # Interactive RazorPay checkout & sandbox test simulator
│       ├── receipt_detail.html     # Formal printable 80G tax exemption receipt
│       ├── whatsapp_logs.html      # WhatsApp notification history and direct wa.me fallback
│       └── manage_form.html        # Unified content upload form for trustees
└── static/
    └── css/
        └── trust.css               # Clean responsive theme styles
```

---

## Quickstart & Running the Application

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Dependencies: `django`, `razorpay`, `pillow`, `requests`

### 2. Run Database Migrations
```bash
python manage.py migrate
```

### 3. Seed Realistic Sample Data
Populates sample trustees, initiatives, events, maintenance expenses, donors, and pending pledges:
```bash
python manage.py seed_data
```

### 4. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
# Or use the pre-configured admin account:
# Username: admin
# Password: trustee2026
```

### 5. Launch the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## Automated WhatsApp Cron Worker

To trigger automated reminders for overdue or pending pledges via cron or scheduled task:
```bash
python manage.py send_whatsapp_reminders
```
Optionally specify minimum days:
```bash
python manage.py send_whatsapp_reminders --days-overdue 3
```

---

## Running Automated Tests

Run the test suite verifying all 9 core workflows:
```bash
python manage.py test core
```
Output:
```
Ran 9 tests in 0.88s
OK
```
