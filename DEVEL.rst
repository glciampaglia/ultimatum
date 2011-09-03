========================================================
Ultimatum Game Web Application
========================================================
-----------------
Development Guide
-----------------

:Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
:Copyright: This code is © copyright of ETH Zürich 2010.

.. contents::

Introduction
------------

The scope of this document is to explain how to extend and mantain the ultimatum
game web app. This web application was written using Django, a popular web
application framework for Python. This documents presuppones you are already
familiar with it [#]_.

Naming Conventions
------------------

We use the classic Python convention, e.g.: **threading.Thread.run()** means we
refer to the method **run** of class **Thread** in module **experiment**.

Source tree
-----------

The source code follows the classic layout of Django projects. The
**experiment** package implements the web app. This is located at the top level. 
Within this you find the files **models.py**, **views.py** and **urls.py**, plus
other stuff. The templates are under **templates/experiment**. They all inherit
from **templates/base.html**. Localization files for the German language are
under **locale/de**. At the top level you also find:

* **settings.py** main settings file for the project
* **urls.py** top-level url-patterns
* **__init__.py**, which must be an empty text file
* **empty.db** a "empty" SQLite database

Model
-----

The data model is implemented using four classes:

1. **experiment.models.Session**, a single experimental session. One-to-Many
   relation with **Game**. Each session has a randomly-generatad pass-code.
2. **experiment.models.Game**, a single game. It has two One-to-One relations
   with **Participant**, in order to keep track for player A and player B.
3. **experiment.models.Participant**, an anonymous participant. It is in relation
   with **django.contrib.auth.models.User** since **Participant** instances are
   user profiles. A new pair of User/Participant instances is created upon
   authentication with a session's pass-code. The User instance has a standard
   user name (e.g. "Participant-1") and the password is the session's pass-code.
   This authentication information is not really important because participants
   can login only once during their browser session (which is not the same thing
   as the experimental session, though) [#]_. **Participant** is in a
   One-to-Many relation with **Trial** (see below). Another important attribute
   of this class is the field **stage** (see next section).
4. **experiment.models.Trial**, a single arithmetic trial, which might be wrong
   or correct.

Stages Structure
----------------

The web app implements an interactive two player game. The game is structured as
a sequence of stages. Each stage defines what interface the two players will
see, and what kind of events are needed in order to move to the next stage.

+-------+--------------+--------------+-------+----------+-------+------+----------+
| enter | instructions |      wait    |       |          |       |      |          |
+-------+--------------+--------------+ trial + proposal + reply + game + donation +
|       |   enter      | instructions |       |          |       |      |          |
+-------+--------------+--------------+-------+----------+-------+------+----------+

The logics of this flowchart is implemented in **experiment.views**. 
**Participant.stage** codes for the current stage the player is in. Transitions
between stages happen upon acquistion of new information needed to progress the
game, in particular:

1. Let us assume the first player authenticates with the session's pass-code. A
   new **Game** instance is created, and the role of the player (A or B) is
   randomly determined. The player enters the instructions phase.
2. The player reads all instructions, checks the button saying she has read them
   and clicks the `start` button. At this point, if another player has joined
   the game in the meanwhile, both are taken to the trial phase, otherwise, she
   stops at the wait phase. From this stage a polling mechanism (see
   **static/polling.js**) will take her to the trial phase, once another player
   joins the game.
3. In the trial stage, players test the game interface by solving 3 test trials.
4. Once each player finishes her 3 trials, she is taken to the proposal phase.
   At this point the roles have been already defined, and the proposal template
   will display two different screen: player A (the proposer) will see the
   proposal interface. Player B will see instead a waiting screen. In the
   background the same polling mechanism of before will ensure an automatic
   transition once Player B's **stage** attribute is updated. The conditional is
   implemented in the template code in **templates/experiment/proposal.html**
   using Javascript transition effect (look at **static/proposal.js**)
   The view **experiment.views.proposal()** is responsible for updating the
   **stage** attribute of both players once the proposal information is
   received.
5. Next stage is reply, which is simmetrical in terms of displayed information:
   player B will see a form with two buttons (for accepting or rejecting the
   proposal from A) and A will wait, while polling for a stage transition. The
   view **experiment.views.reply()** takes care of updating the **stage**
   attribute in sync.
6. In the game phase, players solve their own calculations. At this point stage
   advancement is not anymore in sync, but happens as soon as a player solves
   correctly the whole amount of trials of her own.
7. The donation phase is the terminal phase. Players choose an amount of money
   to donate, submit their choice and get back a PDF with a payment coupon they
   can print. Subsequently, the view will render a page with a link to the same
   coupon, in case they want to print it later.

All views after the first one (enter) are authenticated via the pass-code, but
it is important to understand that this authentication mechanism is one-shot,
which means that the participant has no way to logout and login again [#]_.
However, upon authentication a cookie is created for that HTTP session, and the
expiration of that cookie is set to one week after. So the player can access the
website again in the following days and be taken automatically back to the last
screen she was, i.e. the donation one.

Automatic Redirection
~~~~~~~~~~~~~~~~~~~~~

A benefit of having a **stage** attribute for each player is that the web app
knows what page to render to the participant so, if players try to re-access
previous stages (each stage has its own URL, e.g. /experiment/2/proposal. 2
is the game ID, "proposal" is the stage) the web app can redirect them to the
right one. This mechanism is implemented in **experiment.views.redirecting**.

This modular mechanism is much more easy to mantain and extend then a single
view with a `switch` conditional construct in it, and gives the user a feedback
on the stage they are.

Treatments and Payoff functions
-------------------------------

Treatments are implemented as Javascript callback functions that are passed to a
jQuery-UI slider object. As the proposer drags the slider, the payoff values are
updated automatically using the callbacks. There are currently three different
treatments implemented:

- Weak proposer
- Weak responder
- Equal power

Callbacks are defined in the /static/proposal_new.js, and they look like this:

::

    
    type1 = function (x) { return [ x + this.scale * 10 + this.scale, this.scale * 10 - this.scale - x ]; }
    type2 = function (x) { return [ x + this.scale * 10 - 2 * this.scale, this.scale * 10 + 2 * this.scale - x ]; }
    type3 = function(x) { return [ 2 * this.scale * 10 + this.scale - x, x - this.scale ]; }

The parameter **scale** sets the number of trials to divide. If **scale = 1**,
then 10 trials will be requested. This is convenient in case of testing. Other
parameters are defined in the object model:

::


    class Session(models.Model):
    // ... 
        default_treatment = models.SmallIntegerField(null=True, blank=True,
                choices=TREATMENTS)
        scale = models.IntegerField(default=100)
        boundary = models.FloatField(default=.1)

If **default_treatment** is Null, then each game during that session will have a
randomly generated treated. **scale** is passed thru the template to the
javascript objects above. **boundary** sets the minimum and maximum of the range
of values the proposer can choose from and it is a fraction of the total amout
of trials. Defaults are: 1000 trials min/max: 100/900.

Notes
-----
.. [#] Django has a very complete documentation. See http://docs.djangoproject.com
.. [#] In practice, the experimental session is implemented with a cookie. This
    does not deny people to participante more than once during the same
    sesssion, for example from another browser, from another computer, or from
    the same browser after having deleted the cookie. This limitation is
    intrinsic with the anonymous setting we choose.
.. [#] In practice, **experiment.views.logout** is also implemented, and
    accessible (url patter is /experiment/logout) but the user never has a
    button or link to access this view, with one exception: after 10 minutes at
    the wait phase the user has the option to logout and try to login again, *as
    a different participant*. This was implemented as a safety mechanism in case
    of any deadlock or bug that might prevent the Game the participant from
    being selected. Also, we noticed people get fed up rather soon of waiting,
    so it is also a form of feedback in case of low participant turnover.


