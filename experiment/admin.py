# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------


from django.db.models import Q
from experiment.models import Session, Game, Participant, Trial, Feedback
from django.contrib import admin
from django.forms import ModelForm, ValidationError
from datetime import timedelta

# class GameInline(admin.TabularInline):
#       model = Game
#       extra = 10

class SessionAdminForm(ModelForm):
    class Meta:
        model = Session
    def clean(self):
        cd = self.cleaned_data
        sd = cd.get('start_date')
        ed = cd.get('end_date')
        if sd is None or ed is None:
            raise ValidationError('session must have start and end date')
        if cd['start_date'] >= cd['end_date']:
            raise ValidationError('start date cannot be after end date')
        code = cd.get('login_code')
        overlapping = Session.objects.filter(Q(start_date__range=(sd,ed))\
                | Q(end_date__range=(sd,ed))).exclude(login_code=code)
        if len(overlapping) > 0:
            raise ValidationError('multiple sessions cannot overlap.')
        b = cd.get('boundary')
        if b <= 0 or b >= 1:
            raise ValidationError('boundary must be within (0,1) (excluded)')
        s = cd.get('scale')
        if s < 1:
            raise ValidationError('scale must be greater or equal than 1')
        return cd

class SessionAdmin(admin.ModelAdmin):
    def num_games(self, obj):
        return len(Game.objects.filter(session=obj))
    num_games.short_description = 'played games'
    form = SessionAdminForm
    fieldsets = [
            ('Time window', { 'fields': ['start_date', 'end_date'] }),
            ('Login information', { 'fields': ['login_code'] }),
            ('Experimental parameters', { 'fields': [ 'scale', 'boundary'  ] }),
            ('Payment information', { 'fields' : ['payment', 'payment_currency'] }),
            ]
    list_display = ('login_code', 'start_date', 'end_date', 'is_ongoing', 'num_games' )
    list_filter = ['start_date', 'end_date']
    date_hierarchy = 'start_date'
#       inlines = [ GameInline ]

admin.site.register(Session, SessionAdmin)

class ParticipantAdminForm(ModelForm):
    def clean_amount_paid(self):
        val = self.cleaned_data.get('amount_paid')
        if val is None:
            return val
        if val < 0:
            raise ValidationError('amount of money paid cannot be negative')
    def clean_amount_donated(self):
        val = self.cleaned_data.get('amount_donated')
        if val is None:
            return val
        if val < 0:
            raise ValidationError('amount of money donated cannot be negative')

class ParticipantAdmin(admin.ModelAdmin):
    def get_game(self, obj):
        try:
            return Game.game_of(obj).id
        except:
            pass
    def progress(self, obj):
        try:
            g = Game.game_of(obj)
        except:
            return 'n.a.'
        if obj.stage not in [ 'G', 'D' ]:
            return 'n.a.'
        proposal = map(int,g.proposed_trials.split(','))
        if obj.is_proposer:
            if g.proposal_accepted:
                tot = proposal[0]
            else:
                tot = proposal[2]
        else: 
            if g.proposal_accepted:
                tot = proposal[1]
            else:
                tot = proposal[3]
        num_ok = len(filter(Trial.is_correct, obj.trial_set.all()))
        return '%d / %d' % (num_ok, tot)
    get_game.short_description = 'Game'
    form = ParticipantAdminForm
    list_display = [ 'id', 'user', 'get_game', 'is_proposer', 'stage', 'progress', 'payment_code' ]

admin.site.register(Participant, ParticipantAdmin)

class GameAdminForm(ModelForm):
    def clean_initial_tasks(self):
        val = self.cleaned_data.get('initial_tasks')
        if val is not None and val <= 0:
            raise ValidationError('initial tasks must be a positive number')
        return val
    def clean_proposed_tasks(self):
        propval = self.cleaned_data.get('proposed_tasks')
        inival = self.cleaned_data.get('initial_tasks')
        if propval is not None and (propval > inival):
            raise ValidationError(
                    'proposed tasks cannot be greater than initial tasks')
            if propval is not None and (propval < 0):
                raise ValidationError('proposed tasks cannot be negative')
        return propval

class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = [
            'id',
            'player_a',
            'player_b',
            'treatment',
            'is_active',
            'is_over',
            'proposal_accepted' 
            ]
    list_filter = [ 'session' ] 

admin.site.register(Game, GameAdmin) 

class TrialAdmin(admin.ModelAdmin):
    def pprint(self, obj):
        return unicode(obj)
    pprint.short_description = 'Trial'
    list_display = ( 'pprint', 'is_correct', 'participant', 'submission_date' )
    list_filter = ['participant',]

admin.site.register(Trial, TrialAdmin)

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'stage', 'message', 'timestamp')
    list_filter = ['user', 'stage']

admin.site.register(Feedback, FeedbackAdmin)
