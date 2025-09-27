# icfda_conference/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'icfda_conference.settings')
application = get_wsgi_application()