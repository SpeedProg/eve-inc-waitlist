'use strict';
var REFORM = (function(){
	var lib = {
			trigger_selector: "#btn-send-invites",
			trigger_action: "click",
			user_list_selector: "#char-list",
			// it gets a jquery object of the element gotten with the user_list_selector
			user_list_extractor_func: function(el) {
				return el.val().split(/\n/);
			},
			progress_selector: "#progressbar"
	};
	lib.getMetaData = function(name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
	
	lib.api_invite_by_name = lib.getMetaData('api-invite-by-name');
	lib.csrf = lib.getMetaData('csrf-token');
	
	lib.displayMessage = function(message, type) {
		var alertHTML = $($.parseHTML('<div class="alert alert-dismissible" role="alert">'+
				'<button type="button" class="close" data-dismiss="alert" aria-label="Close">'+
				'<span aria-hidden="true">&times;</span>'+
				'</button>'+
				'<p class="text-xs-center"></p>'+
				'</div>'));
		var textContainer = $('.text-xs-center', alertHTML);
		textContainer.html(message);
		alertHTML.addClass('alert-'+type);
		var alertArea = $('#alert-area-base');
		alertArea.append(alertHTML);
	};
	
	lib.invite = function(playerName) {
		$.post({
			'url': lib.api_invite_by_name.replace('-1', playerName),
			'data': {
				'_csrf_token': lib.csrf
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.message !== 'undefined') {
						message += ": " + data.message;
				}
				if (typeof data.responseJSON !== 'undefined' && typeof data.responseJSON.message !== 'undefined') {
					message += ": " + data.responseJSON.message;
				}
				lib.displayMessage(message, "danger");
				lib.increaseCounter(1);
			},
			'success': function(data){
				lib.increaseCounter(1);
			},
			'dataType': 'json'
		});
	};
	
	lib.increaseCounter = function(inc) {
		var bar = $(lib.progress_selector);
		var old = Number(bar.attr('value'));
		bar.attr('value', old+inc);
	};
	
	lib.startInvites = function(event) {
		var character_names = lib.user_list_extractor_func($(lib.user_list_selector));
		var bar = $(lib.progress_selector);
		bar.attr('max', character_names.length);
		bar.attr('value', 0);
		for (let name of character_names) {
			lib.invite(name);
		}
	};
	
	lib.init = function(inputAreaID, barContainerID, startButtonID) {
		var button = $(lib.trigger_selector);
		button.on(lib.trigger_action, lib.startInvites);
	};
	
	return lib;
}());
$(document).ready(function() {
	REFORM.init();
});