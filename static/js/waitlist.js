'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.linemember = (function(){
	var getMetaData = waitlist.base.getMetaData;
	var settings = {};
	
	function getFitUpdateUrl(fitID) {
		return settings.fit_update_url.replace('-1', fitID);
	}
	
	function removeSelf() {
		var settings = {
				dataType: "text",
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				},
				method: 'DELETE',
				success: function(data, status, jqxhr){
				},
				url: getMetaData('url-self-remove-all')
		};
		$.ajax(settings);
	}
	
	function removeOwnEntry(wlId, charId, entryId) {
		var settings = {
				dataType: "text",
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				},
				method: 'DELETE',
				success: function(data, status, jqxhr){
				},
				url: "/api/self/wlentry/remove/"+entryId
		};
		$.ajax(settings);
	}
	
	function removeOwnFit(event) {
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-fit'));
		var wlId = Number(target.attr('data-wlId'));
		var entryId = Number(target.attr('data-entryId'));
		event.stopPropagation();
		var settings = {
				dataType: "text",
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				},
				method: 'DELETE',
				success: function(data, status, jqxhr){
				},
				url: "/api/self/fittings/remove/"+fitId
		};
		$.ajax(settings);
	}
	
	function updateFit(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-fit'));
		var updateUrl = getFitUpdateUrl(fitId);
		window.location = updateUrl;
	}
	
	function removeOwnEntryHandler(event) {
		var target = $(event.currentTarget);
		var wlId = target.attr('data-wlId');
		var charId = target.attr('data-characterid');
		var entryId = target.attr('data-entryId');
		removeOwnEntry(wlId, charId, entryId);
	}
	
	function waitlistCollapseHandler(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
    	var id = target.attr("id");
    	var togglerSelector = target.attr("data-tog-icon");
    	if (togglerSelector !== undefined || togglerSelector !== null) {
            localStorage.setItem(id, 'closed');
       	    $(togglerSelector).removeClass("fa-minus-square").addClass("fa-plus-square");
        }
	}
	
	function waitlistExpandeHandler(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
    	var id = target.attr("id");
    	var togglerSelector = target.data("tog-icon");
    	if (togglerSelector !== undefined || togglerSelector !== null) {
            localStorage.removeItem(id);
       	    $(togglerSelector).removeClass("fa-plus-square").addClass("fa-minus-square");
        }
	}
	
	function removeSelfHandler(event) {
		removeSelf();
	}
	
	function init () {
		settings.fit_update_url = getMetaData('api-fit-update');
		
		// setup handler for the leave waitlist button
		$('body').on('click', '[data-action="removeSelfFromWaitlists"]', removeSelfHandler);
		
		// setup fit button handler related to linemembers
	    $("#waitlists").on("click", '[data-action="remove-own-fit"]', removeOwnFit);
	    $("#waitlists").on("click", '[data-action="update-fit"]', updateFit);
	    $("#waitlists").on('click', '[data-action="removeOwnEntry"]', removeOwnEntryHandler);

	    // setup waitlist close/opne event handlers
	    $('#waitlists').on('show.bs.collapse', '.collapse', waitlistExpandeHandler);
	    $('#waitlists').on('hide.bs.collapse', '.collapse', waitlistCollapseHandler);
	    
	    
	    // load old states of the waitlists
	    var wlists = $('ol[id|="wl-fits"]');
		for (var i=0; i < wlists.length; i++) {
			var wl = $(wlists[i]);
			var wlId = wl.attr("id");
			var wllist = wl.attr("data-tog-icon");
			var storage = localStorage.getItem(wlId);

			if (storage !== null) {
	            wl.collapse('hide');
			}
		}
	}
	
	document.addEventListener('DOMContentLoaded', init);

	return {};
})();
