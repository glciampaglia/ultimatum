# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------

from os.path import abspath
from django.conf.urls.defaults import *

# enables the admin interface
from django.contrib import admin
admin.autodiscover()


# localization within javascript code
js_info_dict = {
        'packages' : ( 'experiment', )
}

urlpatterns = patterns('',
        (r'^i18n/$', 'django.views.i18n.javascript_catalog', js_info_dict ),
        (r'^login/$', 'django.contrib.auth.views.login', 
            {'template_name' : 'login.html'}),
        (r'^admin/', include(admin.site.urls)),
        (r'^experiment/', include('experiment.urls')),
# This line allows serving static files directly through Django. Remove this
# line in a production environment and configure Apache in order to serve the
# files under static/
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root' : abspath('./static/')}),
)
