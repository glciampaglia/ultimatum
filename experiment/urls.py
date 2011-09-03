# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------

from django.conf.urls.defaults import *

urlpatterns = patterns('experiment.views',
        (r'^$', 'enter'),
        (r'^login/$', 'login_participant'),
        (r'^logout/$', 'logout_view'),
        (r'^payment/$', 'payment'),
        (r'^feedback/$', 'feedback'),
        (r'^(?P<game_id>\d+)/start/$', 'start'),
        (r'^(?P<game_id>\d+)/instructions/$', 'instructions'),
        (r'^(?P<game_id>\d+)/store/$', 'store_trial'),
        (r'^(?P<game_id>\d+)/coupon/$', 'coupon'),
        (r'^(?P<game_id>\d+)/(?P<participant_id>\d+)/trials/$', 'get_trials'),
        (r'^(?P<game_id>\d+)/trial/$', 'trial'),
        (r'^(?P<game_id>\d+)/wait/$', 'wait'),
        (r'^(?P<game_id>\d+)/set_proposal/$', 'set_proposal'),
        (r'^(?P<game_id>\d+)/proposal/$', 'proposal'),
        (r'^(?P<game_id>\d+)/proposal_poll/$', 'proposal_poll'),
        (r'^(?P<game_id>\d+)/reply/$', 'reply'),
        (r'^(?P<game_id>\d+)/reply_poll/$', 'reply_poll'),
        (r'^(?P<game_id>\d+)/game/$', 'game'),
        (r'^(?P<game_id>\d+)/donation/$', 'donation'),
        (r'^(?P<game_id>\d+)/set_donation/$', 'set_donation'),
)
