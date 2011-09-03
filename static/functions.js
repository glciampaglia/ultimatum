/* utility functions */ 

function max(a,b) {
	return a > b ? a : b;
}

function audio(name) {
	var rsa = /safari/i;
	var rfi = /firefox/i;
        var rex = /MSIE/i;
	var isSafari = rsa.test(window.navigator.userAgent);
	var isFirefox = rfi.test(window.navigator.userAgent);
	if (isSafari || isFirefox) {
            var a = new Audio('/static/sounds/'+ name + (isSafari ? '.aiff' : '.ogg'));
            a.play();
        }
}

// samples a random integer from minvalue to maxvalue, default is [0,10)
function randInt (maxvalue,minvalue) {
	minvalue = Math.round(minvalue === undefined ? 0 : minvalue);
	maxvalue = Math.round(maxvalue === undefined ? 10 : maxvalue);
	var diff = maxvalue - minvalue;
	return Math.round(Math.random() * diff - 0.5) + minvalue;
}

function showModalDialog(msg) {
	$("#grayscreen").fadeIn(200);
	$("#waitingdialog").fadeIn(400);
	$("#waitingdialog > span").html(msg);
}

// callback is a function that takes in input the index of the link being
// clicked. msg get in the span. additional arguments are turned to strings and
// a link is created for each of them
function showModalInputDialog(msg,callback) {
	$("#grayscreen").fadeIn(200);
	$("#inputdialog").fadeIn(400);
	$("#inputdialog > span").html(msg);
	var i;
	for (i=2; i<arguments.length; i++) {
		$("#inputdialog > div").append('<span>' + String(arguments[i]) + '</span>');
		$("#inputdialog > div").append('&nbsp;');
	}
	$("#inputdialog > div span").each(function(i) {
		$(this).click(function(event) {
			event.preventDefault();
			if (callback)
				callback(i);
			$("#inputdialog").fadeOut(100);
			$("#grayscreen").fadeOut(200);
			$("#inputdialog > span").html("");
			$("#inputdialog > div").html("");
		});
	});
}
