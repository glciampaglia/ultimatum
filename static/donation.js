$(function () {
	$("#redcross").click(function (event) {
		$.post(document.location.href, {clicked:true}, function () {}, 'json');
	});
});

$(function () {
	$("#donationform").submit(function (event) {
		$("#donationform").hide() 
		$("#thankyou").show()
	});
});


