# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------


from django.contrib.auth.models import User
from django.db import models, IntegrityError
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from datetime import datetime
import random
from os.path import join,dirname,abspath
import numpy as np
from numpy import base_repr
from numpy.random import randint

codelen = 25
wordlistfn = join(dirname(abspath(__file__)), 'wordlist.txt')

def makecode():
    f = open(wordlistfn)
    try:
        wordlist = map(str.strip,f.readlines())
        code = []
        while len('-'.join(code)) < codelen:
            i = random.randrange(0,len(wordlist))
            word = wordlist[i]
            if word in code:
                continue
            code.append(word)
        return '-'.join(code)[:codelen]
    finally:
        f.close()

def payment_code():
    r = np.random.rand(1).view(np.uint64)
    code = base_repr(r, 26)
    n = len(code)
    idx = range(0,n,4)
    code = [ code[slice(idx[i-1],idx[i])] for i in xrange(1,len(idx)) ] + [
            code[idx[-1]:] ]
    return '-'.join(code)

TREATMENTS = [
        ( 1, u'Weak proposer' ),
        ( 2, u'Weak responder' ),
        ( 3, u'Equal power' ),
]

CURRENCIES = [
        ( 'USD', u'$' ),
        ( 'EUR', u'€' ),
        ( 'GBP', u'£' ),
        ( 'CHF', u'CHF' ),
        ( 'JPY', u'¥' ),
        ( 'RUB', u'руб' ),
]

class Session(models.Model):
    start_date = models.DateTimeField('start date')
    end_date = models.DateTimeField('end date')
    login_code = models.CharField(max_length=codelen, unique=True,
            default=makecode)
    default_treatment = models.SmallIntegerField(null=True, blank=True,
            choices=TREATMENTS)
    scale = models.IntegerField(default=100)
    boundary = models.FloatField(default=.1)
    payment = models.FloatField(default=17.)
    payment.verbose_name = 'participant payment'
    payment_currency = models.CharField(max_length=255, default='CHF',
            choices=CURRENCIES)
    def is_ongoing(self):
        return self.start_date <= datetime.now() <= self.end_date
    is_ongoing.short_description = 'Is ongoing?'
    def __unicode__(self):
        return '(%s) - (%s)' % (
                self.start_date.strftime('%Y-%m-%d, %H:%M:%S'),
                self.end_date.strftime('%Y-%m-%d, %H:%M:%S'), )
    @classmethod
    def current_session(cls):
        now = datetime.now()
        query = Q(start_date__lte=now) & Q(end_date__gte=now)
        return cls.objects.filter(query).get()
    @classmethod
    def next_session(cls):
        now = datetime.now()
        return Session.objects.filter(
                start_date__gt=now).order_by('start_date')[:1].get()
    def get_parameters(self, type):
        ''' type is \in { 1,2,3 } '''
        return dict(scale=self.scale, boundary=self.boundary,
                name=TREATMENTS[type][1])

STAGES = (
        ( u'E', u'enter' ),
        ( u'I', u'instructions' ),
        ( u'W', u'wait' ),
        ( u'T', u'trial' ),
        ( u'P', u'proposal' ),
        ( u'R', u'reply'),
        ( u'G', u'game' ),
        ( u'D', u'donation' ),
)

class Participant(models.Model):
    user = models.OneToOneField(User)
    is_proposer = models.NullBooleanField()
    link_clicked = models.BooleanField(default=False)
    payment_received = models.BooleanField(default=False)
    payment_code = models.CharField(max_length=17, default=payment_code,
            unique=True)
    amount_paid = models.IntegerField(null=True, blank=True)
    amount_donated = models.IntegerField(null=True, blank=True)
    stage = models.CharField(max_length=1, choices=STAGES, default=u'I')
    proposal_time = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        try:
            return self.user.username
        except ObjectDoesNotExist:
            return 'unregistered participant'
    @classmethod
    def create_user(cls, login_code):
        ''' creates a new user links to it a participant profile. Returns both
        user and participant profile '''
        n = User.objects.order_by('-id')[0].pk
        user = User.objects.create_user('participant-%d' % n,'',
                password=login_code)
        user.is_staff = False
        user.is_superuser = False
        flag = True
        while flag:
            try:
                participant = cls()
            except IntegrityError:
                # payment_code may return a duplicate value, hence we catch the
                # IntegrityError and try again
                pass
            else:
                flag = False
        participant.user = user
        user.save()
        participant.save()
        return user, participant

A = Q(player_a__isnull=True)
NA = Q(player_a__isnull=False)
B = Q(player_b__isnull=True)
NB = Q(player_b__isnull=False)
XOR_QUERY = (A & NB) | (NA & B)

class Game(models.Model):
    '''
    If proposal_accepted is True, then A
    will have to do proposed_trials trials, while B initial_trials -
    proposed_trials. In case of rejection, the trials to split will be a function
    of proposed_trials, initial_trials, and rule_type.
    '''
    session = models.ForeignKey(Session)
    player_a = models.ForeignKey(Participant,related_name='player_a',null=True)
    player_b = models.ForeignKey(Participant,related_name='player_b',null=True)
    treatment = models.SmallIntegerField()
    initial_trials = models.IntegerField()
    proposed_trials = models.CommaSeparatedIntegerField(null=True, blank=True,
            max_length=255)
    proposal_accepted = models.NullBooleanField()
    end_time = models.DateTimeField('end time', null=True, blank=True)
    def __unicode__(self):
        return '%d (%s vs %s)' % (self.id, self.player_a, self.player_b)
    def is_over(self):
        return self.end_time != None
    is_over.boolean = True
    def is_active(self):
        '''
        returns True if all existing players are active (as in
        django.contrib.auth.models.User)
        '''
        flag = lambda k : k is None or ( k is not None and k.user.is_active )
        return flag(self.player_a) and flag(self.player_b)
    is_active.boolean = True
    @classmethod
    def game_of(cls, participant):
        query = Q(player_a=participant) | Q(player_b=participant)
        return cls.objects.filter(query)[:1].get()
    @classmethod
    def available_game(cls, session):
        games = session.game_set.filter(XOR_QUERY).order_by('-id')
        games = filter(Game.is_active, games)
        if len(games):
            return games[0]
        raise ObjectDoesNotExist('no available games')

class Trial(models.Model):
    participant = models.ForeignKey(Participant)
    question = models.CharField(max_length=255)
    answer = models.SmallIntegerField()
    submission_date_millis = models.BigIntegerField('submission_date_millis')
    submission_date_millis.verbose_name = 'Submission date (in msec.)'
    def submission_date(self):
        return datetime.fromtimestamp(self.submission_date_millis / 1000.0)
    def __unicode__(self):
        if self.is_correct():
            sign = '='
        else:
            sign = '<>'
        return '%s %s %d' % (self.question, sign, self.answer)
    def is_correct(self):
        try:
            a, b = map(int,self.question.split('+'))
            return a + b == self.answer
        except:
            return False
    is_correct.boolean = True
    def trial_data(self):
        return dict(
                question=self.question,
                result=self.answer)
        is_correct.short_description = 'Is correct?'

class Feedback(models.Model):
    user = models.ForeignKey(User, null=True)
    message = models.TextField()
    stage = models.CharField(max_length=1, choices=STAGES, null=True)
    timestamp = models.DateTimeField('timestamp')
