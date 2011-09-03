-- :Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
-- :Copyright: © ETH Zürich 2010
-- :Description: summary of all games of given session (by ID)

select 
    g.id as game,
    p.id as participant,
    p.amount_paid,
    p.amount_donated,
    p.payment_received,
    p.stage, 
    count(*) as num_trials
from 
    experiment_session s join 
    experiment_game g join
    experiment_participant p join 
    experiment_trial t 
on 
    s.id = g.session_id and 
    ( p.id = g.player_a_id or p.id = g.player_b_id ) and
    p.id = t.participant_id
where s.id = 5 -- change this ID to the one of the session you want
group by p.id
order by g.id;
