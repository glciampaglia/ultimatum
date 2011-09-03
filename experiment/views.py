# coding=utf-8
# vim:ts=8:sw=4

#------------------------------------------------------------------------------- 
# Ultimatum Web Experiment
#
# Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
#
# This code is © copyright of ETH Zürich 2010.
#-------------------------------------------------------------------------------


import re
from cStringIO import StringIO
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
from experiment.models import Session, Participant, Game, Trial, Feedback, STAGES
from random import randint
from subprocess import Popen, PIPE
from os.path import expandvars
from django.template import Context, RequestContext
from django.template.loader import get_template

STAGE_NAMES = dict(STAGES)

def redirecting(view):
    def redirecting_view(request, *args, **kwargs):
        if request.user.is_anonymous():
            if view.func_name != 'enter':
                return HttpResponseRedirect(reverse('experiment.views.enter'))
            else:
                return view(request, *args)
        try:
            participant = request.user.get_profile()
        except ObjectDoesNotExist:
            return HttpResponse('user %s is not a participant, please logout' %
                    repr(request.user))
        stage_view = STAGE_TO_VIEW[participant.stage]
        if view.func_name != stage_view.name:
            stage_name = STAGE_NAMES[participant.stage]
            view_full_name = __name__ + '.' + stage_name
            try:
                game = Game.game_of(participant)
            except ObjectDoesNotExist:
                redirection_url = reverse(view_full_name)
            else:
                redirection_url = reverse(view_full_name, args=(game.id,))
            if request.is_ajax():
                response_data = dict(redirect=redirection_url)
                return HttpResponse(simplejson.dumps(response_data), 
                        mimetype='application/javascript')
            else:
                return HttpResponseRedirect(redirection_url)
        return view(request, *args, **kwargs)
    redirecting_view.name = view.func_name
    return redirecting_view

@redirecting
def enter(request):
    '''
    if there is a session now, show a form for inserting the login code, else if
    there is any future session show when it starts, else say to check back
    later.
    '''
    try:
        session = Session.current_session()
    except ObjectDoesNotExist:
        # if no current session, return the next one or set it to None
        ongoing = False
        try:
            session = Session.next_session()
        except ObjectDoesNotExist:
            session = None
    else:
        ongoing = True
    request.session.set_test_cookie()
    return render_to_response('experiment/enter.html',
            dict(session=session, ongoing=ongoing))

def logout_view(request):
    request.user.is_active = False
    request.user.save()
    logout(request);
    return HttpResponseRedirect(reverse('experiment.views.enter'))

def login_participant(request):
    '''
    Custom login procedure
    '''
    try:
        session = Session.current_session()
    except ObjectDoesNotExist:
        # highly unlikely, but might happen if the session expires while sending
        # the POST.
        try:
            session = Session.next_session()
        except ObjectDoesNotExist:
            session = None
        return render_to_response('experiment/enter.html',
                dict(
                    ongoing=False,
                    session=session,
                    error_message=_('Sorry but the session just ended!')))
    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()
    else:
        return render_to_response('experiment/enter.html',
                dict(
                    ongoing=True,
                    session=session,
                    error_message="Please enable cookies and try again."))
    if request.POST['login_code'] == session.login_code:
# create the user
        user, participant = Participant.create_user(session.login_code)
        participant.session = session
        participant.stage = 'I'
#        participant.save()
# authenticate the user
        login(request,authenticate(username=user.username,\
                password=session.login_code))
# set session expire date to 7 days
        request.session.set_expiry(session.end_date + timedelta(7))
# assign it to a game
        try:
            game = Game.available_game(session)
        except ObjectDoesNotExist:
            # create new game
            treatment = session.default_treatment or randint(1,3)
            game = Game(session=session, initial_trials=session.scale * 10,
                    treatment=treatment)
            # choose at random if player a (proposer) or player b (evaluator)
            if randint(0,1):
                game.player_a = participant
                participant.is_proposer = 1
            else:
                game.player_b = participant
                participant.is_proposer = 0
        else: 
            # join existing game
            if game.player_a is None:
                game.player_a = participant
                participant.is_proposer = 1
            else:
                game.player_b = participant
                participant.is_proposer = 0
            participant.stage = 'I'
        game.save()
        participant.save()
        return HttpResponseRedirect(reverse('experiment.views.instructions', 
                args=(game.id,)))
    else:
        return render_to_response('experiment/enter.html',
                dict(session=session, ongoing=True,
                    error_message=_('code not correct, please try again')))

@login_required
@redirecting
def instructions(request, game_id):
    '''
    shows the instructions
    '''
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    if participant == game.player_a:
        participant_type = 'A'
    else:
        participant_type = 'B'
    return render_to_response('experiment/instructions.html',
            dict(session=Session.current_session(), game=game,
                participant_type=participant_type),
            context_instance=RequestContext(request))

@login_required
def start(request, game_id):
    '''
    Check that user ticked the boxes for regulations and instructions
    '''
    game = get_object_or_404(Game, pk=game_id)
    try:
        participant = request.user.get_profile()
    except ObjectDoesNotExist:
        return HttpResponse(
                _('User %(user)s is not a participant. please logout') %
                dict(user=request.user))
    session = Session.current_session()
    instructions_read = request.POST.get('instructions_read')
    if participant == game.player_a:
        participant_type = 'A'
    else:
        participant_type = 'B'
    if instructions_read is None:
        return render_to_response('experiment/instructions.html',
                dict(message=_('Please read the instructions'), session=session, 
                    game=game, participant_type=participant_type),
                context_instance=RequestContext(request))
    participant.stage = 'W'
    participant.save()
    return HttpResponseRedirect(reverse('experiment.views.wait', args=(game.id,)))

@login_required
@redirecting
def wait(request, game_id):
    participant = request.user.get_profile()
    game = get_object_or_404(Game,pk=game_id)
    if participant == game.player_a:
        flag = (game.player_b is not None) and game.player_b.stage != 'I'
    else:
        flag = (game.player_a is not None) and game.player_a.stage != 'I'
    if flag:
        for p in [ game.player_a, game.player_b ]:
            p.stage = 'T'
            p.save()
        if request.is_ajax():
            response_data = dict(redirect=reverse('experiment.views.trial',
                    args=(game.id,)))
            return HttpResponse(simplejson.dumps(response_data),
                    mimetype='application/javascript')
        else:
            return HttpResponseRedirect(reverse('experiment.views.trial',
                    args=(game.id,)))
    else:
        if request.is_ajax():
            return HttpResponse(simplejson.dumps({}),
                    mimetype='application/javascript')
        else:
            polling_url = reverse('experiment.views.wait',args=(game.id,))
            return render_to_response('experiment/wait.html', 
                    dict(game=game, participant=participant, url=polling_url))

@login_required
def store_trial(request, game_id):
    if request.is_ajax():
        trial = Trial(participant=request.user.get_profile(),
                answer = int(request.POST['result']),
                question = request.POST['question'],
                submission_date_millis = int(request.POST['timestamp'])
                )
        trial.save()
        return HttpResponse(simplejson.dumps({}),
                mimetype='application/javascript')
    else:
        return HttpResponse('ciao')

@login_required
def get_trials(request, game_id, participant_id):
    game = get_object_or_404(Game, pk=game_id)
    participant = get_object_or_404(Participant, pk=participant_id)
    from_index = int(request.POST['from_index'])
    trials = Trial.objects.filter(participant=participant).all().order_by('id')
    response_data = map(Trial.trial_data, trials[from_index:])
    if request.is_ajax():
        return HttpResponse(simplejson.dumps(response_data),
                mimetype='application/javascript')
    else:
        return HttpResponse('ciao')

@login_required
@redirecting
def trial(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    i_am_player_a = (game.player_a == participant)
    if i_am_player_a:
        my_id, opponent_id = game.player_a.id, game.player_b.id
    else:
        my_id, opponent_id = game.player_b.id, game.player_a.id
    if i_am_player_a:
        player_label = 'A'
    else:
        player_label = 'B'
    return render_to_response('experiment/play.html',
            dict(
                player_label=player_label,
                is_trial=True,
                my_id=my_id,
                opponent_id=opponent_id,
                game=game,
                my_trials=3,
                opponent_trials=3,
                post_game_url= reverse(
                    'experiment.views.set_proposal', args=(game.id,))
                )
            )

@login_required
def set_proposal(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    # advance to proposal only if at trial stage
    if participant.stage == 'T':
        participant.stage = 'P'
        participant.save()
    return HttpResponseRedirect(reverse('experiment.views.proposal',\
            args=(game.id,)))

@login_required
@redirecting
def proposal(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    if request.is_ajax():
        # store proposal in game, advance stage for both participants
        game.proposed_trials = ','.join(request.POST.getlist('proposal[]'))
        game.save()
        participant.proposal_time = float(request.POST['proposal_time'])
        participant.save()
        for player in [ game.player_a, game.player_b ]:
            player.stage = 'R'
            player.save()
        response_data = { 'redirect' :
                reverse('experiment.views.reply',
                    args=(game.id,)) }
        return HttpResponse(simplejson.dumps(response_data),
                mimetype='application/javascript')
    else:
        return render_to_response('experiment/proposal.html',\
                dict(participant=participant, game=game,
                    treatment=simplejson.dumps(game.session.get_parameters(game.treatment-1)),))

@login_required
def proposal_poll(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    if request.is_ajax():
        # redirect to reply page
        if game.proposed_trials:
            response_data = {'redirect' :
                    reverse('experiment.views.reply',
                        args=(game.id,)) }
        else:
            response_data = {}
        return HttpResponse(simplejson.dumps(response_data),
                mimetype='application/javascript')
    else:
        raise RuntimeError('not ajax')

@login_required
@redirecting
def reply(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    if request.is_ajax():
        # store reply in game, advance 'stage' for both participant
        game.proposal_accepted = int(request.POST['reply'])
        game.save()
        participant.proposal_time = float(request.POST['reply_time'])
        participant.save()
        Trial.objects.filter(Q(participant=game.player_a) |
                Q(participant=game.player_b)).delete()
        for player in [ game.player_a, game.player_b ]:
            player.stage = 'G'
            player.save()
        response_data = { 
                'redirect' : reverse('experiment.views.game', args=(game.id,))
        }
        return HttpResponse(simplejson.dumps(response_data),
                    mimetype='application/javascript')
    else:
        return render_to_response('experiment/reply.html',
                dict(participant=participant, game=game))

@login_required
def reply_poll(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    if request.is_ajax():
        if game.proposal_accepted is not None:
            # redirect to game page
            response_data = { 'redirect' :
                    reverse('experiment.views.game', args=(game.id,))}
        else:
            response_data = {}
        return HttpResponse(simplejson.dumps(response_data),
                    mimetype='application/javascript')
    else:
        raise RuntimeError('ajax only')

@login_required
@redirecting
def game(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    proposal = map(int,game.proposed_trials.split(','))
    i_am_player_a = (game.player_a == participant)
    if i_am_player_a:
        my_id, opponent_id = game.player_a.id, game.player_b.id
    else:
        my_id, opponent_id = game.player_b.id, game.player_a.id
    if game.proposal_accepted:
        my_trials, opponent_trials = proposal[:2]
    else:
        my_trials, opponent_trials = proposal[2:]
    if not participant.is_proposer:
        my_trials, opponent_trials = opponent_trials, my_trials
    if i_am_player_a:
        player_label = 'A'
    else:
        player_label = 'B'
    return render_to_response('experiment/play.html',
            dict(
                player_label=player_label,
                is_trial=False,
                my_id=my_id,
                opponent_id=opponent_id,
                game=game,
                participant=participant,
                my_trials=my_trials,
                opponent_trials=opponent_trials,
                session=game.session,
                post_game_url= reverse(
                    'experiment.views.set_donation', args=(game.id,))
                )
            )

@login_required
def set_donation(request, game_id):
    participant = request.user.get_profile()
    game = get_object_or_404(Game, pk=game_id)
    participant.stage = 'D'
    participant.save()
    return HttpResponseRedirect(reverse('experiment.views.donation',
        args=(game.id,)))

@login_required
@redirecting
def donation(request, game_id):
    game = get_object_or_404(Game,pk=game_id)
    participant = request.user.get_profile()
    game.end_time = datetime.now()
    game.save()
    if request.is_ajax():
        participant.link_clicked = True;
        participant.save()
        return HttpResponse(simplejson.dumps({}),
                mimetype='application/javascript')
    else:
        if participant.amount_donated is not None:
            message = _('You already donated.')
            return render_to_response('experiment/donation.html',
                    dict(participant=participant, game=game, message=message,
                        hide_form=True, session=game.session))
        return render_to_response('experiment/donation.html',
                dict(participant=participant, game=game, session=game.session,
                    hide_form=False))

path = '/instances/home/hermes/ultimatum'
htmldoc_cmd = 'htmldoc --format pdf --webpage --path %s -' % path

@login_required
def coupon(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    participant = request.user.get_profile()
    if participant.amount_donated is None:
        try:
            donation = int(request.POST['donation'])
        except ValueError:
            message = _("Please insert any amount to donate or 0")
            return render_to_response('experiment/donation.html',
                    dict(participant=participant, message=message, game=game,
                        session=game.session))
        if donation < 0:
            message = _("Donated amount cannot be negative!")
            return render_to_response('experiment/donation.html',
                    dict(participant=participant, message=message, game=game,
                        session=game.session))
        if donation > game.session.payment:
            message = _("Donated amount cannot exceed %(payment)s %(currency)s"
                    % dict(payment='%.2g' % game.session.payment,
                        currency=game.session.payment_currency) )
            return render_to_response('experiment/donation.html',
                    dict(participant=participant, message=message, game=game,
                        session=game.session))
        participant.amount_donated = donation
        participant.amount_paid = game.session.payment - donation
        participant.save()
    # Create the HttpResponse object with the appropriate PDF headers.
    t = get_template('experiment/coupon.html')
    ctx = Context(dict(participant=participant, session=game.session))
    p = Popen(htmldoc_cmd.split(), stdin=PIPE, stdout=PIPE)
    pdf,stderr = p.communicate(t.render(ctx).encode('UTF-8'))
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=coupon.pdf'
    response.write(pdf)
    return response

STAGE_TO_VIEW = dict([
    ( u'I', instructions ),
    ( u'W', wait ),
    ( u'T', trial ),
    ( u'P', proposal ),
    ( u'R', reply ),
    ( u'G', game ),
    ( u'D', donation ),
])

def payment(request):
    ci = RequestContext(request)
    try:
        payment_code = request.POST['payment_code']
    except KeyError:
        return render_to_response('experiment/payment.html', dict(show_form=1,
        message=None), context_instance=ci)
    else:
        if len(payment_code) != 17:
            msg = _('Incorrect code "%s"! Should be 17 characters long.' 
                    % payment_code)
            return render_to_response('experiment/payment.html',
                    dict(show_form=1, message=msg), context_instance=ci)

        try:
            p = Participant.objects.filter(payment_code=payment_code).get()
        except ObjectDoesNotExist:
            msg = _('Payment code not authorized: %s' % payment_code)
            return render_to_response('experiment/payment.html',
                    dict(show_form=1, message=msg), context_instance=ci)
        else:
            if p.payment_received:
                msg = 'Payment not authorized (already used code).'
                return render_to_response('experiment/payment.html',
                        dict(show_form=1, message=msg), context_instance=ci)
            else:
                p.payment_received = True
                p.save()
                msg = _('Payment code was accepted. Please proceed with payment of %d CHF' % p.amount_paid)
                return render_to_response('experiment/payment.html', 
                        dict(show_form=0, message=msg), context_instance=ci)

def feedback(request):
    if not request.is_ajax():
        return HttpResponse('invalid request')
    if request.user.is_anonymous():
        stage = None
        user = None
    else:
        participant = request.user.get_profile()
        stage = participant.stage
        user = request.user
    message = request.POST['message']
    feedback = Feedback(message=message, user=user, stage=stage, 
            timestamp=datetime.now())
    feedback.save()
    return HttpResponse('OK')

# vim:ts=8:sw=4
