'use strict';
if (!waitlist) {
	var waitlist = {};
}
waitlist.fsettings = (function() {
	/**
	 * Get meta elements content from the website
	 */
	var urls = {
		remove_fleet: waitlist.base.getMetaData('api-fleet-remove'),
		move_to_safety: waitlist.base.getMetaData('api-movetosafety')
	};

	function removeFleet(fleetID) {
		$.ajax({
			success: function() {
				$('#fleet-' + fleetID).remove();
			},
			data: {
				'_csrf_token': waitlist.base.getMetaData('csrf-token')
			},
			dataType: 'text',
			method: 'DELETE',
			url: urls.remove_fleet.replace("-1", fleetID)
		});
	}

	function setupActionHandler() {
		$('body')
			.on('click', '[data-type="remove-fleet"]', removeButtonHandler);
		$('body').on('click', '[data-action="moveToSafety"]',
			safetyButtonHandler);
	}

	function removeButtonHandler(event) {
		var target = $(event.currentTarget);
		var id = Number(target.attr('data-id'));
		removeFleet(id);
	}

	function safetyButtonHandler(event) {
		var target = $(event.currentTarget);
		var fleetId = Number(target.attr('data-fleetId'));
		moveFleetToSafetyChannel(fleetId);
	}

	function init() {
		setupActionHandler();
	}

	function moveFleetToSafetyChannel(fleetID) {
		$.post({
			'url': urls.move_to_safety,
			'data': {
				'_csrf_token': waitlist.base.getMetaData('csrf-token'),
				'fleetID': fleetID
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.message !== 'undefined') {
					message += ": " + data.message;
				}
				waitlist.base.displayMessage(message, "danger");
			}
		});
	}

	$(document).ready(init);

	return {};
}());