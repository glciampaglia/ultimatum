
/* Poller objects
 *
 * Constructor
 * -----------
 * reqfun is a no argument function. It may call for example jQuery's $.post or
 * $.get on a given url with given callback. timeout is in millisec and if not
 * specified by default is 500 msec.
 *
 */

var DEBUG = 0; // if set to 1, then alert() the redirection url
var poller;

function Poller(reqfun,timeout) {
    this.reqfun = reqfun;
    this.timeout = timeout ? timeout : 750;
}

Poller.prototype.startPolling = function() {
    this.ispolling = true;
    var self = this;
    setTimeout(function() { self.poll(); }, 2000);
}

Poller.prototype.stopPolling = function() {
    this.ispolling = false;
}

Poller.prototype.poll = function(timeout) {
    this.reqfun();
    var self = this;
    var timeout = timeout ? timeout : this.timeout;
    if (this.ispolling) setTimeout(function() { self.poll(timeout); }, timeout);
}

function poll_for_redirect(url) {
    return function() {
        redirect_callback = function(data) {
            if ( data.redirect ) { 
                if (DEBUG) { alert('redirecting to: '+data.redirect); }
                window.location.href = data.redirect; 
            }
        };
        poller = new Poller(function () { 
            $.post( url, {}, redirect_callback, 'json' ); 
        });
        poller.startPolling();
    };
}

