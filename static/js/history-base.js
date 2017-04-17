'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.history = {};
waitlist.history.base = (function() {

	// 4h in the past
	var data = {
		laststamp: new Date(Date.now()-14400000).getTime(),
		exclude_selector:'tr.h-entry:not([data-action="comp_mv_xup_etr"]):not([data-action="comp_mv_xup_fit"])'
	};
	
	function getLastRefresh() {
		return data.laststamp;
	}
	
	function setLastRefresh(stamp) {
		data.laststamp = stamp;
	}
	
	function getExcludeSelector() {
		return data.exclude_selector;
	}

	function resolveAction(action) {
		switch (action) {
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
	}
	
	function createHistoryEntryDOM(entry) {
		/* jshint multistr: true */
		var historyEntrySkeleton = $.parseHTML(
			`<tr class="bg-danger h-entry" data-action="${entry.action}">
				<td>${entry.time}</td>
				<td>${resolveAction(entry.action)}</td>
				<td></td>
				<td><a href="char:${entry.target.id}"></a></td>
				<td></td>
			</tr>`);
		var nameTD = $(":nth-child(3)", historyEntrySkeleton);
		var targetA = $(":nth-child(4) > a", historyEntrySkeleton);
		var targetTD = $(":nth-child(4)", historyEntrySkeleton);
		var fittingsTD = $(":nth-child(5)", historyEntrySkeleton);
		
		if (entry.source !== null) {
			nameTD.text(entry.source.username);
		}
		targetA.text(entry.target.name);

		if (entry.target.newbro) {
			targetTD.prepend('<span class="tag tag-info">New</span> ');
		}
		for (var i=0; i < entry.fittings.length; i++) {
			fittingsTD.append(createFittingDOM(entry.fittings[i]));
		}
		return historyEntrySkeleton;
	}
	
	function createFittingDOM(fit) {
		var comment = "";
		let skillsData = "";
		if (fit.comment !== null) {
			comment = " " + $.parseHTML(fit.comment)[0].textContent;

			// lets extract caldari bs lvl from comments
			let caldariBsLvelRex = /<b>Cal BS: ([012345])<\/b>/;
			let bsResult = caldariBsLvelRex.exec(fit.comment);
			if (bsResult !== null) {
				skillsData = `3338:${bsResult[1]}`;
			}
		}
		if (fit.ship_type === 1) {
			return $.parseHTML(`<a href="#" class="booby-link">${fit.shipName}${comment}</a>`);
		} else {
			return $.parseHTML(`<a href="#" class="fit-link" data-skills="${skillsData}" data-dna="${fit.shipType+':'+fit.modules}">${fit.shipName}${comment}</a>`);
		}
	}
	
	function filter_enabled() {
		return data.approvalBox.checked;
	}
	
	function entry_added_handler(event, entry) {
		entry = $(entry);
		if (filter_enabled()) {
			var action = entry.attr('data-action');
			if (action !== "comp_mv_xup_etr" && action !== "comp_mv_xup_fit") {
				entry.addClass("hidden-el");
			}
		}
	}
	
	function filter_handler() {
		if (!filter_enabled()) {
			$(data.exclude_selector).addClass('hidden-el');
		} else {
			$(data.exclude_selector).removeClass('hidden-el');
		}
	}
	
	function entryEnteredHandler(event) {
		var el = $(event.currentTarget);
		if (el.hasClass("bg-danger")){
			el.removeClass("bg-danger");
		}
	}

	function init() {
		data.approvalBox = $('#filter-approval-only-box')[0];
		$('#filter-approval-only').on('click', filter_handler);
		$('#historybody').on("hentry-adding", entry_added_handler);
		$('#historybody').on("mouseenter", ".h-entry", entryEnteredHandler);
	}
	
    $(document).ready(init);
	
	return {
		createHistoryEntryDOM: createHistoryEntryDOM,
		getLastRefresh: getLastRefresh,
		setLastRefresh: setLastRefresh,
		getExcludeSelector: getExcludeSelector,
		isApprovalEnabled: filter_enabled
	};
})();