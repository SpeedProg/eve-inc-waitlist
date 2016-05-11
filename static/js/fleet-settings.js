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
				remove_fleet: lib.getMetaData('api-fleet-remove')
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
	return lib;
}());

$(document).ready(FSETTINGS.init);