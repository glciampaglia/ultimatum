#!/usr/bin/env python
# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------


from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
