/* proposal.js
 * author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
 */

var msg_waitready = gettext("Please wait until the other participant is ready.");
var msg_waitprop = gettext("Please wait until the other participant has proposed how to share the work.");
var msg_waitrep = gettext("Please wait until the other participant replies to your proposal.");

var poller;
var slidermanager;
var timestamp;

// recap table messages
var recapheaderA = [
    gettext("If participant B <strong>accepts</strong>:"), 
    gettext("If participant B <strong>rejects</strong>:")
];

var recapheaderB = [
    gettext("If you <strong>accept</strong>"), 
    gettext("If you <strong>reject</strong>")
];

/* treatments */

// compute trials in case of rejection
type1 = function (x) { return [ x + this.scale * 10 + this.scale, this.scale * 10 - this.scale - x ]; }
type2 = function (x) { return [ x + this.scale * 10 - 2 * this.scale, this.scale * 10 + 2 * this.scale - x ]; }
type3 = function(x) { return [ 2 * this.scale * 10 + this.scale - x, x - this.scale ]; }

/* SliderManager object */

function SliderManager(treatment) {
    this.treatment = treatment;
    this.total = treatment.scale * 10
    this.min_value = Math.round(this.total * treatment.boundary)
    this.max_value = this.total - this.min_value
    self = this;
    this.slideropts = {
        min:this.min_value,
        max:this.max_value,
        value:randInt(0,this.total),
        slide:function(event,ui) { self.slidecb.apply(self,[event,ui]) }
    }
}

SliderManager.prototype.showSlider = function () {
    $("#slider").slider(this.slideropts);
    $($("#sliderbox > span")[0]).text(this.min_value);
    $($("#sliderbox > span")[1]).text(this.max_value);
}

SliderManager.prototype.slidecb = function(event,ui) {
    // avoid to go out of scale
    ui.value =  ui.value > this.total ? this.total : ui.value;
    ui.value =  ui.value < 0 ? 0 : ui.value;
    $("#value").text(ui.value);
    var rej = this.treatment.compute(ui.value);
    // sanity check
    rej[0] = rej[0] > 0 ? rej[0] : 0;
    rej[1] = rej[1] > 0 ? rej[1] : 0;
    populate([ui.value, this.total - ui.value, rej[0], rej[1]]);
    $("#proposalform").fadeIn(400);
}

/* basic UI transitions */

function labelRecap(header,labels) {
    $('#recap .recapheader').each(function(i) { $(this).html(header[i]); });
    $('#recap .label').each(function(i) { $(this).html(labels[i]); });
}

function populate(values) {
    $('.propvalue').each(function(i) { $(this).text(values[i]); });
}

/* use this to set the slider
 * position is an integer
 * rulecalc is a function that takes and index and an integer (x in Dirks notes)
 */
function showProposalUI(header,labels) {
    labelRecap(header,labels);
    $("#proposal").fadeIn(200);
    $("#recap").fadeIn(200);
}

function showProposalConfirmation() {
    showModalInputDialog(
        gettext('Do you want to send this proposal?'),
        function(i){
            if (i) {
                // i is 1 for OK, 0 for CANCEL
                var prop = [];
                $(".propvalue").each(
                    function(i) { 
                        prop[prop.length] = $(this).text(); 
                    }
                );
                prop_time = (new Date()).getTime() - timestamp;
                request_data = { proposal : prop, proposal_time : prop_time }
                $.post(
                    window.location.href,
                    request_data,
                    function(data) {
                        if (data.redirect) { 
                            window.location.href = data.redirect; 
                        }
                    }, 
                    'json'
                );
            }
        },
        gettext('cancel'), gettext('send')
    );
}

/* proposal view */

function proposalUI_proposer() {
    slidermanager = new SliderManager(treatment);
    showProposalUI(recapheaderA,[gettext('You'),gettext('part. B'),gettext('You'),gettext('part. B')]);
    slidermanager.showSlider();
    $("#proposalform").submit(function(event) {
        event.preventDefault();
        showProposalConfirmation();
    });
    timestamp = (new Date()).getTime();
}

/* reply view */

function replyUI_proposer() {
    showProposalUI(recapheaderA,[ gettext('You'), gettext('B'), 
        gettext('You'), gettext('B') ]);
    populate(proposal);
    // also set the slider and the recap to the chosen values
    showModalDialog(msg_waitrep);
//    pollForStateChange({},'green');
}

function replyUI_recipient() {
    $("#recap").show();
    labelRecap(recapheaderB, [ gettext('part.  A'), gettext('You'), 
        gettext('part. A'),gettext('You') ]);
    populate(proposal);
    $("#replyform").fadeIn(400);
    $("#replybutton_accept").click(function(event) {
        event.preventDefault();
        reply_time = (new Date()).getTime() - timestamp;
        var request_data = { reply : 1, reply_time : reply_time };
        $.post(
            window.location.href, 
            request_data, 
            function(data) { 
                if (data.redirect) { window.location.href = data.redirect; } 
            },
            'json'
        );
    });
    $("#replybutton_reject").click(function(event) {
        event.preventDefault();
        reply_time = (new Date()).getTime() - timestamp;
        var request_data = { reply : 0, reply_time : reply_time };
        $.post(
            window.location.href, 
            request_data, 
            function(data) { 
                if (data.redirect) { window.location.href = data.redirect; } 
            }, 
            'json'
        );
    });
    timestamp = (new Date()).getTime();
}
