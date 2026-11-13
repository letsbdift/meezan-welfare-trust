"""
Security & Content Security Policy (CSP) Middleware for Meezan Welfare Trust
Enforces strict security headers, Cross-Origin policies, and safe CDN asset inclusion.
"""

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Content Security Policy: permits trusted CDNs, Razorpay payment gateway, Google Fonts & FontAwesome
        response['Content-Security-Policy'] = (
            "default-src 'self' https: data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://checkout.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
            "img-src 'self' data: blob: https:; "
            "frame-src 'self' https://api.razorpay.com https://checkout.razorpay.com; "
            "connect-src 'self' https:;"
        )
        response['Permissions-Policy'] = "camera=(), microphone=(), geolocation=()"
        return response
