// clicking on "feedback" makes the form fade in
$(function() {
    $("#feedbacklink").click(function(event){
        event.preventDefault();
        $("#feedbackform").fadeIn(200);
    });
});

// when user clicks within the text area for the first time, the text "write
// your own feedback" is removed
var neverClicked = 1;

$(function() {
    $("#feedbackmessage").click(function(){
        if (neverClicked) {
            neverClicked = 0;
            $(this).empty()
        }
    });
});

var maxTextLength = 150;

// when you click submit, the message is checked to have only 150 chars max,
// then sent via Ajax. If more than 150, alert the user
$(function() {
    $("#feedbackform").submit(function(event){
        event.preventDefault();
        var ta = $("#feedbackmessage")[0];
        if (ta.textLength > maxTextLength) {
            alert("no more than " + maxTextLength + " characters allowed!");
        } else {
            $.post('/experiment/feedback/', { message: ta.value });
            $("#feedbackform").fadeOut(100);
            $("#feedback div").empty();
            $("#feedback div").append('Thank you!');
        }
    });
});
