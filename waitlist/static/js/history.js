var HISTORY = (function(){
	// 4h in the past
	var lib = {'laststamp':((new Date(Date.now())).getTime()-14400000)};
	/**
	 * Get meta elements content from the website
	 */
	lib.getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	}
	lib.resolveAction = function(action) {
		switch (action){
		case "xup":
			return "X-UP";
		case "comp_rm_pl":
			return "Removed a Character from Waitlists";
		case "comp_inv_pl":
			return "Send Notification to Character";
		case "comp_rm_etr":
			return "Removed Entry from X-UPs";
		case "self_rm_fit":
			return "Removed own fit";
		case "self_rm_entry":
			return "Removed own entry";
		case "self_rm_wls_all":
			return "Removed himself from all lists";
		case "comp_mv_xup_etr":
			return "Approved X-UP entry";
		case "comp_mv_xup_fit":
			return "Approved Single Fit";
		default:
			return action;
		}
	};
	lib.createHistoryEntryDOM = function(entry) {
		var historyEntrySkeleton = $.parseHTML(
			"<tr class=\"bg-danger h-entry\">\
				<td>"+entry.time+"</td>\
				<td>"+lib.resolveAction(entry.action)+"</td>\
				<td></td>\
				<td><a href=\"javascript:CCPEVE.showInfo(1377, "+entry.target.id+");\"></a></td>\
				<td></td>\
			</tr>");
		var nameTD = $(":nth-child(3)", historyEntrySkeleton);
		var targetA = $(":nth-child(4) > a", historyEntrySkeleton);
		var fittingsTD = $(":nth-child(5)", historyEntrySkeleton);
		
		if (entry.source != null) {
			nameTD.text(entry.source.username);
		}
		targetA.text(entry.target.name)
		
		for (var i=0; i < entry.fittings.length; i++) {
			fittingsTD.append(lib.createFittingDOM(entry.fittings[i]));
		}
		return historyEntrySkeleton;
	};
	
	lib.createFittingDOM = function(fit) {
		if (fit.ship_type == 1) {
			return $.parseHTML("<a class=\"booby-link\">"+fit.shipName+" </a> ")
		} else {
			return $.parseHTML("<a class=\"fit-link\" data-dna=\""+fit.dna+"\">"+fit.shipName+" </a>")
		}
	};
	
	lib.refresh = function() {
		$.getJSON(lib.getMetaData('api-history-changed')+"?last="+lib.laststamp, function(data){
			var hbody = $('#historybody');
			for (var i=0; i < data.history.length; i++) {
				var hEntryDOM = lib.createHistoryEntryDOM(data.history[i]);
				hbody.prepend(hEntryDOM);
			}
			if (data.history.length > 0) {
				lib.laststamp = (new Date(Date.parse( data.history[data.history.length-1].time))).getTime();
			}
		});
	};
	lib.init = function() {
		$(document).ready(function(){
			$( document ).on( "mouseenter", ".h-entry", function(e) {
				var el = $(this);
				if (el.hasClass("bg-danger")){
					el.removeClass("h-entry").removeClass("bg-danger");
				}
			});
			lib.refresh()
			setInterval(lib.refresh, 10000);
		});
	};
	return lib;
}());
HISTORY.init();

