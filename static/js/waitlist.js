var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

$(document).ready(function(){    
	
	// extract urls out of html meta tags
	
    $('.collapse').on('show.bs.collapse', function (e) {
    	var id = $(e.target).attr("id");
    	sessionStorage.setItem(id, 'open');
    	var togglerSelector = $(e.target).data("tog-icon");
       	$(togglerSelector).removeClass("fa-plus-square").addClass("fa-minus-square");
    });

    $('.collapse').on('hide.bs.collapse', function (e) {
    	var id = $(e.target).attr("id");
    	sessionStorage.removeItem(id);
    	var togglerSelector = $(e.target).data("tog-icon");
		$(togglerSelector).removeClass("fa-minus-square").addClass("fa-plus-square");
    });
    var wlists = $('ol[id|="wl-fits"]');
	for (var i=0; i < wlists.length; i++) {
		var wl = $(wlists[i]);
		var wlId = wl.attr("id");
		var storage = sessionStorage.getItem(wlId);

		if (storage != "open") {
			wl.collapse('hide');
		}
	}
});
function removeSelf() {
	var settings = {
			dataType: "text",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			method: 'DELETE',
			success: function(data, status, jqxhr){
				var wlNames = getMetaData("wl-names").split(",");
				for(var i=0, len=wlNames.length; i < len; i++) {
					var wlName = wlNames[i];
					var entryId = "entry-"+wlName+"-"+getMetaData('user-id');
					var entry = document.getElementById(entryId);
					if (entry != null) { // there is a entry for him on that wl
						entry.parentNode.removeChild(entry); // remote it from the DOM
					}
				}
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
				var htmlId = "entry-"+wlId+"-"+entryId;
				var entry = document.getElementById(htmlId);
				if (entry != null) { // there is a entry for him on that wl
					entry.parentNode.removeChild(entry); // remote it from the DOM
				}
			},
			url: "/api/self/wlentry/remove/"+entryId
	};
	$.ajax(settings);
}

function removeOwnFit(fitId, wlId, entryId) {
	var settings = {
			dataType: "text",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			method: 'DELETE',
			success: function(data, status, jqxhr){
				var entryHtmlId = "entry-"+wlId+"-"+entryId;
				var fitHtmlId = "fit-"+wlId+"-"+entryId+"-"+fitId;
				var fit = document.getElementById(fitHtmlId);
				var entry = document.getElementById(entryHtmlId);
				if (fit != null) { // there is a entry for him on that wl
					fit.parentNode.removeChild(fit); // remote it from the DOM
				}
				var count = Number(entry.getAttribute("data-count"));
				if (count <= 1) {
					// no fit left, remove entry
					if (entry != null) { // there is a entry for him on that wl
						entry.parentNode.removeChild(entry); // remote it from the DOM
					}
				} else {
					count--;
					entry.setAttribute("data-count", count);
				}
			},
			url: "/api/self/fittings/remove/"+fitId
	};
	$.ajax(settings);
}