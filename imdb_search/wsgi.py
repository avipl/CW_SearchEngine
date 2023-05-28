"""
WSGI config for imdb_search project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

os.environ['TRANSFORMERS_CACHE'] = '/var/www/special/.cache/huggingface/hub'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imdb_search.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
