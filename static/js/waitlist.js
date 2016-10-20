'use strict';
if (!getMetaData){
	var getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
}

function getFitUpdateUrl(fitID) {
	var baseURL = getMetaData('api-fit-update');
	return baseURL.replace('-1', fitID);
}

function dropdownManagment(){
	
	// extract urls out of html meta tags

    $('.collapse').on('show.bs.collapse', function (e) {
    	var id = $(e.target).attr("id");
    	var togglerSelector = $(e.target).data("tog-icon");
    	if (togglerSelector !== undefined || togglerSelector !== null) {
            localStorage.removeItem(id);
       	    $(togglerSelector).removeClass("fa-plus-square").addClass("fa-minus-square");
        }
    });

    $('.collapse').on('hide.bs.collapse', function (e) {
    	var id = $(e.target).attr("id");
    	var togglerSelector = $(e.target).data("tog-icon");
    	if (togglerSelector !== undefined || togglerSelector !== null) {
            localStorage.setItem(id, 'closed');
       	    $(togglerSelector).removeClass("fa-minus-square").addClass("fa-plus-square");
        }
    });
    
    $("#row-waitlists").on("click", '[data-action="remove-own-fit"]', removeOwnFit);
    $("#row-waitlists").on("click", '[data-action="update-fit"]', updateFit);

}

document.addEventListener('DOMContentLoaded', dropdownManagment);

function dropdownLoad(){
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

document.addEventListener('DOMContentLoaded', dropdownLoad);

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