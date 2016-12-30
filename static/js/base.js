'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.base = (function(){
	function getMetaData (name) {
		return $('meta[name="'+name+'"]').attr('content');
	}
	
	function displayMessage(message, type, html, id) {
		var alertHTML = $($.parseHTML(`<div class="alert alert-dismissible alert-${type}" role="alert">
				<button type="button" class="close" data-dismiss="alert" aria-label="Close">
				<span aria-hidden="true">&times;</span>
				</button>
				<p class="text-xs-center"></p>
				</div>`));
		var textContainer = $('.text-xs-center', alertHTML);
		if (typeof id !== "undefined") {
			alertHTML.attr("id", id);
		}
		if (typeof html !== "undefined") {
			textContainer.html(message);
		} else {
			textContainer.text(message);
		}
		var alertArea = $('#alert-area-base');
		alertArea.append(alertHTML);
	}

	return {
		getMetaData: getMetaData,
		displayMessage: displayMessage
	};
})();