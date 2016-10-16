'use strict';
FSETTINGS = (function(){
	var lib = {};
	/**
	 * Get meta elements content from the website
	 */
	lib.getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
	
	lib.api = {
			urls: {
				remove_fleet: lib.getMetaData('api-fleet-remove'),
				move_to_safety: lib.getMetaData('api-movetosafety')
			}
	};
	
	lib.removeFleet = function(fleetID) {
		$.ajax({
			success: function(){
				$('#fleet-'+fleetID).remove()
			},
			data: {
				'_csrf_token': this.getMetaData('csrf-token')
			},
			dataType: 'text',
			method: 'DELETE',
			url: this.api.urls.remove_fleet.replace("-1", fleetID)
		});
	};
	
	lib.removeButton = function() {
		$('[data-type="remove-fleet"]').on('click', function(e){
			var target = $(e.target);
			var id = Number(target.attr('data-id'));
			lib.removeFleet(id);
		});
	};
	lib.init = function() {
		lib.removeButton();
	};
	
	lib.move_to_safety = function(fleetID) {
		$.post({
			'url': lib.api.urls.move_to_safety,
			'data': {
				'_csrf_token': this.getMetaData('csrf-token'),
				'fleetID': fleetID
			},
			'error': function(data) {
				var message = data.statusText
				if (typeof data.message != 'undefined') {
						message += ": " + data.message;
				}
				displayMessage(message, "danger");
			},
			'success': function(data){
			}
		});
	}
	
	return lib;
}());

$(document).ready(FSETTINGS.init);