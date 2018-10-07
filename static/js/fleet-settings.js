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
		
		// confirm dialog handler
		$("#remove-diag").on('show.bs.modal', function(e){
			var source = $(e.relatedTarget);
			var fname = source.data("type");
			var gid = Number(source.data("id"));
			if (fname === "clearWaitlist") {
				$("#remove-diag-accept").off();
				$("#remove-diag-accept").on("click", function() {
					clearWaitlist(gid);
				});
				
				$("#remove-diag-body").text($.i18n('wl-clear-list-warning-body'));
				$("#remove-diag-label").text($.i18n('wl-clear-list-warning-label'));
			}
		});
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

	function moveFleetToSafetyChannel(fleetID) {
		$.post({
			'url': urls.move_to_safety,
			'data': {
				'_csrf_token': getMetaData('csrf-token'),
				'fleetID': fleetID
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.responseText !== 'undefined') {
					message += ": " + data.responseText;
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
				if (typeof data.responseText !== 'undefined') {
					message += ": " + data.responseText;
				}
				waitlist.base.displayMessage(message, "danger");
			}
		});
	}
	
	function setupTypeahead(){
		var constellationSource = new Bloodhound({
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace('conName'),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: {
				url: urls.settings_fleet_query_constellations+'?term=%QUERY',
				wildcard: '%QUERY',
				filter: function(response) {
		            return response.result;
		        }
			}
		});
		$('.con-typeahead').typeahead({
			  hint: true,
			  highlight: true,
			  minLength: 1
			}, {
			name: 'constellations',
			display: 'conName',
			source: constellationSource
		});
		
		var stationSource = new Bloodhound({
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace('statName'),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: {
				url: urls.settings_fleet_query_stations+'?term=%QUERY',
				wildcard: '%QUERY',
				filter: function(response) {
		            return response.result;
		        }
			}
		});
		$('.dock-typeahead').typeahead({
			  hint: true,
			  highlight: true,
			  minLength: 1
			}, {
			name: 'stations',
			display: 'statName',
			source: stationSource
		});

		var systemSource = new Bloodhound({
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace('sysName'),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: {
				url: urls.settings_fleet_query_systems+'?term=%QUERY',
				wildcard: '%QUERY',
				filter: function(response) {
					return response.result;
				}
			}
		});
		$('.hq-typeahead').typeahead({
			  hint: true,
			  highlight: true,
			  minLength: 1
			}, {
			name: 'SolarSystems',
			display: 'sysName',
			source: systemSource
		});
	}
	
	$(document).ready();

	function clearWaitlist(gid) {
		$('#clearwaitlistform-'+gid).submit();
	}
	
	function init() {
		urls.remove_fleet = getMetaData('api-fleet-remove');
		urls.move_to_safety = getMetaData('api-movetosafety');
		urls.global_fleet_set = getMetaData('api-global-fleet');
		urls.settings_fleet_query_constellations = getMetaData('settings.fleet_query_constellations');
		urls.settings_fleet_query_systems = getMetaData('settings.fleet_query_systems');
		urls.settings_fleet_query_stations = getMetaData('settings.fleet_query_stations');
		setupActionHandler();
		setupTypeahead();
	}
	
	$(document).ready(init);

	return {};
}());