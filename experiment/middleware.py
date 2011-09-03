# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------

from django.shortcuts import render_to_response
import re

is_msie = lambda ua: re.search('MSIE', ua) != None
is_firefox = lambda ua: re.search('Firefox', ua) != None

def get_firefox_version(ua):
    m = re.search('Version/([0-9]+\.){2}[0-9]+', ua)
    if m:
        version = ua[slice(m.start(),m.end())][8:].split('.')
        version = tuple(map(int,version))
        return version

class BrowserDetectionMiddleware:
    def process_request(self, request):
        user_agent = request.META['HTTP_USER_AGENT']
        if is_msie(user_agent):
            return render_to_response('experiment/bad_browser.html', {})
        if is_firefox(user_agent):
            version = get_firefox_version(user_agent)
            if version is not None:
                if version[0] < 3:
                    return render_to_response('experiment/bad_browser.html', {})
