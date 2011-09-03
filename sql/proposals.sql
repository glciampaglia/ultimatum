-- :Author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
-- :Copyright: © ETH Zürich 2010
-- :Description: summary of all games that complemeted the proposal/reply phase

select 
    g.id,
    g.treatment,
    g.proposed_trials,
    g.proposal_accepted,
    g.end_time
from 
    experiment_session s join
    experiment_game g 
on 
    s.id = g.session_id 
where s.id = 5 and -- change this number to the ID of the session you want
    proposed_trials is not NULL 
order by treatment;

