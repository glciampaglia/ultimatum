========================================================
Ultimatum Game Web Application
========================================================
------
README
------

The Ultimatum Game
------------------

The ultimatum game is a very popular game in game theory and experimental
economics [#]_. The version implemented here is different from the classical
formulation of the game. 

There are two players, A and B. A is the proposer and B is the responder. A
certain amount of work must be carried out by A and B. The "work" in our case is
a certain amount of trials--N arithmetic sums--that have to be solved. The game
is about how to share the work between the two. Each player is payed as long as
she solves all trials assigned to her. 

A can decide for any amount of trials she intends to solve, let's call this
amount x. The remaining N - x will be given to B. B can decide to accept or
reject the offer. In case of rejection A will have to do y = f(x) calculations
and B M - y. The total amount of calculations in case of rejection can be
doubled (M = 2 * N) or not (M = N). The payoff function f models different
treatments. Currently there are three treatments implemented: Weak proponent,
Weak respondent, Equal power.

.. [#] Quick intro: http://en.wikipedia.org/wiki/Ultimatum_game
