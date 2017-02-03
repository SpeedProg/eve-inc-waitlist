'use strict';

if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.calendar) {
	waitlist.calendar = {};
}

waitlist.calendar = (function() {
	var displayMessage = waitlist.base.displayMessage;
	var getMetaData = waitlist.base.getMetaData;
	function init() {
		$('#timepicker').datetimepicker({
			icons: {
				time: "fa fa-clock-o",
				date: "fa fa-calendar",
				up: "fa fa-arrow-up",
				down: "fa fa-arrow-down",
				previous: 'fa fa-chevron-left',
				next: 'fa fa-chevron-right',
				today: 'fa fa-calendar-o',
				clear: 'fa fa-trash',
				close: 'fa fa-times'
			},
			format: "YYYY/MM/DD HH:mm"
		});
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
					displayMessage("error", "Deleting event failed");
				},
				method: "DELETE",
				success: function() {
					displayMessage("success", "Event deleted");
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
