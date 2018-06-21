'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.reform = (function(){
	
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;
	
	var data = {
			trigger_selector: "#btn-send-invites",
			trigger_action: "click",
			user_list_selector: "#char-list",
			// it gets a jquery object of the element gotten with the
			// user_list_selector
			user_list_extractor_func: function(el) {
				return el.val().split(/\n/);
			},
			progress_selector: "#progressbar"
	};

	function invite(playerName) {
		$.post({
			'url': data.api_invite_by_name.replace('-1', playerName),
			'data': {
				'_csrf_token': data.csrf
			},
			'error': function(data) {
				var message = data.statusText;

				if (typeof data.responseJSON !== 'undefined' && typeof data.responseJSON.message !== 'undefined') {
					message += ": " + data.responseJSON.message;
				}
				else if (typeof data.responseText !== 'undefined') {
						message += ": " + data.responseText;
				}
				displayMessage(message, "danger");
				increaseCounter(1);
			},
			'success': function(){
				increaseCounter(1);
			},
			'dataType': 'json'
		});
	}
	
	function increaseCounter(inc) {
		var bar = $(data.progress_selector);
		var old = Number(bar.attr('value'));
		bar.attr('value', old+inc);
	}
	
	function startInvites() {
		var character_names = data.user_list_extractor_func($(data.user_list_selector));
		var bar = $(data.progress_selector);
		bar.attr('max', character_names.length);
		bar.attr('value', 0);
		for (let name of character_names) {
			invite(name);
		}
	}
	
	function init() {
		data.api_invite_by_name = getMetaData('api-invite-by-name');
		data.csrf = getMetaData('csrf-token');
		var button = $(data.trigger_selector);
		button.on(data.trigger_action, startInvites);
	}
	
    $(document).ready(init);
	
	return {};
}());