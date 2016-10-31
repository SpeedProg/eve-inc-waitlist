'use strict';
if (!waitlist) {
	var waitlist = {};
}
waitlist.fsettings = (function() {
	/**
	 * Get meta elements content from the website
	 */
	var getMetaData = waitlist.base.getMetaData;
	
	var urls = {};

	function removeFleet(fleetID) {
		$.ajax({
			success: function() {
				$('#fleet-' + fleetID).remove();
			},
			data: {
				'_csrf_token': getMetaData('csrf-token')
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
		$('#scramble-cbx').on('change', scrambleStatusChanged);
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
		urls.remove_fleet = getMetaData('api-fleet-remove');
		urls.move_to_safety = getMetaData('api-movetosafety');
		urls.global_fleet_set = getMetaData('api-global-fleet');
		setupActionHandler();
	}

	function moveFleetToSafetyChannel(fleetID) {
		$.post({
			'url': urls.move_to_safety,
			'data': {
				'_csrf_token': getMetaData('csrf-token'),
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
	
	function scrambleStatusChanged(event) {
		var scramble;
		if (event.currentTarget.checked) {
			scramble = 'on';
		} else {
			scramble = 'off';
		}
		$.post({
			'url': urls.global_fleet_set,
			'data': {
				'_csrf_token': getMetaData('csrf-token'),
				'action': 'set_name_scramble',
				'scramble': scramble
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