"""WSGI config for RecipeRelay."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reciperelay.settings")
application = get_wsgi_application()
