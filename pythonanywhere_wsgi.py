"""
PythonAnywhere WSGI configuration file for letsbdift.pythonanywhere.com
Copy this into /var/www/letsbdift_pythonanywhere_com_wsgi.py on PythonAnywhere.
"""

import os
import sys

# Assume the repository was cloned to /home/letsbdift/trust_web_app or /home/letsbdift/meezan_trust
path = '/home/letsbdift/meezan_trust_web_app'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'trust_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
