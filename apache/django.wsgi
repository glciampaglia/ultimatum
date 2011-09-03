import os
import sys

sys.path.append('/instances/home/hermes/local/lib/python2.4/site-packages')
sys.path.append('/instances/home/hermes/ultimatum')
sys.path.append('/instances/home/hermes')

os.environ['DJANGO_SETTINGS_MODULE'] = 'ultimatum.settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
