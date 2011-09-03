/* game.js 
 * author: Giovanni Luca Ciampaglia <ciampagg@ethz.ch>
 */

/* tasks functions */

function parseQuestion(task) {
    var q = task.question.split('+');
    var op1 = parseInt(q[0]);
    var op2 = parseInt(q[1]);
    return { op1:op1, op2:op2, flag:(op1 + op2 == task.result) };
}

function Task(question,result) {
    this.question = question;
    this.result = result;
    this.timestamp = (new Date()).getTime();
}

function ListFullError() {
    this.name = 'ListFullError';
    this.message = 'list is full';
}

ListFullError.prototype = Error.prototype;

/* game */

function Game(
        my_id,
        opponent_id, 
        game_id, 
        my_tasks, 
        opponent_tasks, 
        post_game_url) 
{
    // all arrays are (me, opponent)
    this.game_id        = parseInt(game_id);
    this.opponent_id    = parseInt(opponent_id);
    this.my_id          = parseInt(my_id);
    this.my_tasks       = parseInt(my_tasks);
    this.opponent_tasks = parseInt(opponent_tasks);
    this.lastquestion   = sessionStorage.lastquestion;
    this.post_game_url  = post_game_url;
    this.total          = new Array(this.my_tasks, this.opponent_tasks);
    this.right          = new Array(0,0);
    this.wrong          = new Array(0,0);
    this.fetched        = new Array(0,0);
    this.blankTables();
    this.updateUI(0, this.my_id, 100);
    this.updateUI(1, this.opponent_id, 100);
    this.polling();
}

Game.prototype.isFull = function(idx) {
    if (undefined == idx) throw new Error()
    return this.right[idx] == this.total[idx];
}

Game.prototype.isOver = function() {
    return this.isFull(0);
}

Game.prototype.sendTask = function(task) {
    $.post("/experiment/" + this.game_id + '/store/', task);
}

Game.prototype.updateUI = function(idx, participant_id, speed,sound) {
    $.post("/experiment/" + this.game_id + '/' + participant_id + '/trials/', 
        { from_index: this.fetched[idx] },
        function(data) { 
            for (i=0; i<data.length; i++) {
                game.addTask(data[i], idx, speed, sound);
                game.fetched[idx] += 1;
            }
        game.scrollList(idx);
        game.updateStatusLine();
        if (game.isOver())
            window.location.href = game.post_game_url;
        else {
            game.showForm();
            if (sessionStorage.lastquestion) {
                $("#question").text(sessionStorage.lastquestion);
            } else {
                sessionStorage.lastquestion = game.updateFormOK(1500);
            }
        }
    }, 'json');
}

Game.prototype.scrollList = function(idx) {
    try {
        var fr = $('iframe')[idx];
        if (fr) {
            var tr = $('#taskstable',fr.contentDocument)[0].tBodies[0].lastChild;
            if (tr.scrollIntoView) tr.scrollIntoView(true);
        }
    } catch (Error) {}
}

// returns true/false. Throws ListFullError if list is full
Game.prototype.addTask = function (task,idx,speed,sound) {
    if (undefined === idx) throw new Error('list not specified')
    if (this.isFull(idx)) throw new ListFullError();
    var p = parseQuestion(task)
    var mf = $("iframe")[idx];
    var mt = $('#taskstable',mf.contentDocument)[0];
    var text = '<tr><td>' + p.op1 + '+' + p.op2 + '</td><td>' + task.result + 
            '</td><td>' + (p.flag? gettext('OK!') : gettext('Wrong')) + '</td></tr>'; 
    $(mt).prepend(text);
    if (sound) audio(sound)
    $('tr:last > td',mt).each(function() {
        $(this).hide();
        $(this).fadeIn(undefined === speed ? 400 : speed);
    });
    if (p.flag) this.right[idx] += 1
    else this.wrong[idx] += 1
    return p.flag;
}

/* UI transitions */

Game.prototype.updateStatusLine = function () {
    // by default 'A' is the first player, so he/she has lower playerid
    var isproposer = parseInt(sessionStorage.isproposer);
    if (isNaN(isproposer)) 
        // guessing is better than nothing
        isproposer = randInt(0,1);
    $("#oppname").html( isproposer ? 'A' : 'B');
    $("#mystatus").html(this.total[0] - this.right[0]);
    $("#oppstatus").html(this.total[1] - this.right[1]);
}

Game.prototype.updateFormOK = function (speed) {
    var op1 = randInt(9);
    var op2 = randInt(9);
    var textarea = $("#controls input:first")[0];
    var question = op1 + ' + ' + op2;
    textarea.disabled = 1;
    $("#question").fadeOut(0);
    $("#question").css('color','black');
    $("#question").html(question);
    $("#question").fadeIn(speed);
    textarea.disabled = 0;
    $("#reset").click();
    return question;
}

Game.prototype.updateFormWrong = function (speed) {
    $("#question").css('color','red')
}

Game.prototype.disableForm = function() {
    $("#controls input").each(function(i) { this.disabled = 1; });
}

Game.prototype.showForm = function() {
    $("#thanks").hide();
    $("#controls").show();
}

Game.prototype.grabInput = function() {
    if ($("input")[0].value == '') {
        audio('Funk');
        alert(gettext("please insert a number!"));
        return;
    }
    var r = parseInt($("input")[0].value);
    if (isNaN(r)) {
        audio('Funk')
        alert(gettext("please insert a correct number!"));
        return;
    }
    return new Task($("#question").text(),r);
}

var poller;

Game.prototype.polling = function() {
    self = this;
    poller = new Poller(function () { 
        game.updateUI.apply(self,[ 1, game.opponent_id, 400, 'Pop' ]) 
    });
    poller.startPolling();
}

Game.prototype.blankTables = function() {
    $('iframe').each( function(i) {
        $("#taskstable > tbody", this.contentDocument).html(""); 
    });
}

/* jQuery callbacks on document ready */
// handler for submit events
$(function() {
    $("#operationform").submit(function(event){
        event.preventDefault();
        var task;
        if (task = game.grabInput()) {
        try {
            var outcome = game.addTask(task,0);
            game.sendTask(task)
            if (outcome) {
                game.updateStatusLine();
                game.updateFormOK(200);
            } else {
                audio('Basso');
                game.updateFormWrong(); 
            }
            sessionStorage.lastquestion = $("#question").text(); 
        } catch (ListFullError) { } 
            if (game.isOver()) audio('Glass'); 
        } 
    });
});

// global Game object
var game;

function make_game(my_id, opponent_id, game_id, my_tasks, opponent_tasks, post_game_url) {
    return function() {
        game = new Game(my_id, opponent_id, game_id, my_tasks, opponent_tasks, post_game_url);
    };
}
