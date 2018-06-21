'use strict';

if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.calendar) {
	waitlist.calendar = {};
}

waitlist.calendar.settings = (function() {
	var displayMessage = waitlist.base.displayMessage;
	var getMetaData = waitlist.base.getMetaData;
	function init() {
		setupEventHandler();
	}

	function removeEventHandler(event) {
		var target = $(event.currentTarget);
		var eventID = target.attr('data-eventid');
		var urlpath = target.attr('date-deletepath');
		var settings = {
				async: true,
				dataType: "text",
				error: function() {
					displayMessage($.i18n('wl-calendar-settings-error-event-delete'), "danger");
				},
				method: "DELETE",
				success: function() {
					displayMessage($.i18n('wl-calendar-settings-event-deleted'), "success");
					target.closest("tr").remove();
				},
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				}
		};
		$.ajax(urlpath, settings);
	}

	function setupEventHandler() {
		$(document).on('click', '[data-action="remove-event"]', removeEventHandler);
	}

	$(document).ready(init);
	return {};
})();
