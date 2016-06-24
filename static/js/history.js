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
			return "Send Invitation to Character";
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
		case "comp_send_noti":
			return "Send Notification to Character";
		case "set_fc":
			return "Was set as FC";
		case "set_fcomp":
			return "Was set as Fleet Comp";
		case "auto_rm_pl":
			return "Player was removed after found in fleet";
		case "auto_inv_missed":
			return "Player missed his invite";
		case "self_rm_etr":
			return "Player removed himself from X-UPs";
		case "comp_inv_by_name":
			return "Player was invited by Name(Reform Tool?)";
		default:
			return action;
		}
	};
	lib.createHistoryEntryDOM = function(entry) {
		var historyEntrySkeleton = $.parseHTML(
			"<tr class=\"bg-danger h-entry\" data-action=\""+entry.action+"\">\
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
				hbody.trigger("hentry-adding", hEntryDOM);
				hbody.prepend(hEntryDOM);
				hbody.trigger("hentry-added", hEntryDOM);
			}
			if (data.history.length > 0) {
				lib.laststamp = (new Date(Date.parse( data.history[data.history.length-1].time))).getTime();
			}
		});
	};
	
	lib.filter_enabled = function() {
		return $('#filter-approval-only-box')[0].checked;
	};
	
	lib.filter_handler = function(event) {
		if (!lib.filter_enabled()) {
			$('tr.h-entry:not([data-action="comp_mv_xup_etr"])').addClass('hidden-el');
		} else {
			$('tr.h-entry:not([data-action="comp_mv_xup_etr"])').removeClass('hidden-el');
		}
	};
	
	lib.entry_added_handler = function(event, entry) {
		entry = $(entry);
		if (lib.filter_enabled()) {
			if (entry.attr('data-action') != "comp_mv_xup_etr") {
				entry.addClass("hidden-el");
			}
		}
	};
	
	lib.init = function() {
		$(document).ready(function(){
			$( document ).on( "mouseenter", ".h-entry", function(e) {
				var el = $(this);
				if (el.hasClass("bg-danger")){
					el.removeClass("bg-danger");
				}
			});
			lib.refresh()
			setInterval(lib.refresh, 10000);
			$('#filter-approval-only').on('click', lib.filter_handler);
			$('#historybody').on("hentry-adding", lib.entry_added_handler);
		});
	};
	return lib;
}());
HISTORY.init();

