'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.base = (function(){
	function getMetaData (name) {
		return $('meta[name="'+name+'"]').attr('content');
	}

	var wlClient = SwaggerClient(
		{
			url: "/spec/v1/swagger.json",
			requestInterceptor : function(req) {
				req.headers['X-CSRFToken'] = getMetaData('csrf-token');
				return req;
			}
		}
	);
	
	function displayMessage(message, type, html, id) {
		var alertHTML = $($.parseHTML(`<div class="alert alert-dismissible alert-${type}" role="alert">
				<button type="button" class="close" data-dismiss="alert" aria-label="Close">
				<span aria-hidden="true">&times;</span>
				</button>
				<p class="text-center"></p>
				</div>`));
		var textContainer = $('.text-center', alertHTML);
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
	
	function handleLanguageSelection(event) {
		let langCode = event.target.value;
		wlClient.then((client) => {
			client.apis.I18n.put_i18n_locale({
				'lang': langCode
			}).then(() => {
				location.reload();
			}).catch(function(event) {
				if (typeof(event.response) !== "undefined" &&
					typeof(event.response.obj) !== "undefined" &&
					typeof(event.response.obj.error) !== "undefined"){
					waitlist.base.displayMessage($.i18n('wl-lang-change-failed', event.response.obj.error), "danger");
				} else {
					waitlist.base.displayMessage($.i18n('wl-add-alt-failed'), "danger");
				}
			});
		});
	}
	
	function init() {
		$('#lang-select').on('change', handleLanguageSelection);
	}
	
	$(document).ready(init);

	return {
		getMetaData: getMetaData,
		displayMessage: displayMessage
	};
})();