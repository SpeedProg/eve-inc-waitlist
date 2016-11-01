'use strict';
/**
 * Get meta elements content from the website
 */

if (!waitlist) {
	var waitlist = {};
}

waitlist.fleetcomp = (function() {
	var displayMessage = waitlist.base.displayMessage;
	var getMetaData = waitlist.base.getMetaData;

	var showInfo = waitlist.IGBW.showInfo;

	/**
	 * Sends out a notification
	 * 
	 * @param charId
	 * @param wlid
	 */
	function sendNotification(charID, waitlistID) {
		$.post({
			'url': getMetaData('api-send-notification').replace("-1", charID),
			'data': {
				'waitlistID': waitlistID,
				'_csrf_token': getMetaData('csrf-token')
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.message !== 'undefined') {
					message += ": " + data.message;
				}
				displayMessage(message, "danger");
			},
			'dataType': 'json'
		});
	}

	/**
	 * Send the notification for a player, and logs from which wl he was invited
	 * 
	 * @param userId eve id of the user, the notification should be send too
	 */
	function invitePlayer(userID, waitlistID, groupID) {
		$.post({
			'url': getMetaData('api-send-invite'),
			'data': {
				'charID': userID,
				'waitlistID': waitlistID,
				'groupID': groupID,
				'_csrf_token': getMetaData('csrf-token')
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.message !== 'undefined') {
					message += ": " + data.message;
				}
				if (typeof data.responseJSON !== 'undefined'
					&& typeof data.responseJSON.message !== 'undefined') {
					message += ": " + data.responseJSON.message;
				}
				displayMessage(message, "danger");
			},
			'dataType': 'json'
		});
	}

	/**
	 * Remove a player from Waitlists and not X-UP
	 * 
	 * @param userId eve id of the user that should be removed
	 */
	function removePlayer(userId, groupId) {
		$.post(getMetaData('api-wls-remove-player'), {
			'playerId': userId,
			'groupId': groupId,
			'_csrf_token': getMetaData('csrf-token')
		}, function() {
		}, "text");
	}

	/**
	 * Remove a specific entry (from X-UP)
	 * 
	 * @param entryId id of the entry to remove
	 * @param userId user id the entry belongs to
	 */
	function removeEntry(wlId, entryId) {
		$.post(getMetaData('api-wl-remove-entry'), {
			'entryId': entryId,
			'_csrf_token': getMetaData('csrf-token')
		}, function() {
		}, "text");
	}

	/**
	 * Move a X-UP entry to waitlists (approving all fits inside it)
	 * 
	 * @param entryId id of the entry that should be approved
	 * @param userId eve id the of the user the entry belongs to
	 */
	function moveEntryToWaitlists(wlId, entryId) {
		var entryDOM = $("#entry-" + wlId + "-" + entryId);
		var fitDOMs = $('li[id|="fit"]', entryDOM);
		var fit_id_str = "";
		var fitCount = fitDOMs.length;
		var fitid_prefix_length = ("fit-" + wlId + "-" + entryId + "-").length;

		fitDOMs.each(function(idx, element) {
			var cIdStr = $(element).attr("id");
			var cId = cIdStr.substring(fitid_prefix_length, cIdStr.length);
			fit_id_str += cId;
			if (idx < fitCount - 1) {
				fit_id_str += ",";
			}
		});
		$.post(getMetaData('api-move-entry-to-wls'), {
			'entryId': entryId,
			'fitIds': fit_id_str,
			'_csrf_token': getMetaData('csrf-token')
		}, function() {
		}, "text");
	}

	/**
	 * Mave a single fit to waitlist
	 */
	function approveFit(wlId, entryId, fitId) {
		$.post(getMetaData('api-approve-fit'), {
			'fit_id': fitId,
			'_csrf_token': getMetaData('csrf-token')
		}, function() {
		}, "text");
	}

	function approveFitHandler(event) {
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-id'));
		var wlId = Number(target.attr('data-wlId'));
		var entryId = Number(target.attr('data-entryId'));
		event.stopPropagation();
		if (fitViewed(`fit-${wlId}-${entryId}-${fitId}`)) {
			approveFit(wlId, entryId, fitId);
		} else {
			var name = document.getElementById(`entry-${wlId}-${entryId}`).dataset.username;
			displayMessage("You should view "+ name + "'s fit before accepting it.", "danger");
		}
	}

	function approveEntryHandler(event) {
		var target = $(event.currentTarget);
		var wlId = target.attr('data-wlId');
		var entryId = target.attr('data-entryId');
		if (entryViewed(wlId, entryId)) {
			moveEntryToWaitlists(wlId, entryId);
		} else {
			var name = document.getElementById(`entry-${wlId}-${entryId}`).dataset.username;
			displayMessage("You should view all of "+ name + "'s fits before accepting them.", "danger");
		}
	}

	function sendNotificationHandler(event) {
		var target = $(event.currentTarget);
		var charId = target.attr('data-characterid');
		var wlId = target.attr('data-wlId');
		sendNotification(charId, wlId);
	}

	function dismissEntryHandler(event) {
		var target = $(event.currentTarget);
		var wlId = target.attr('data-wlId');
		var entryId = target.attr('data-entryId');
		removeEntry(wlId, entryId);
	}

	function invitePlayerHandler(event) {
		var target = $(event.currentTarget);
		var charId = target.attr('data-characterid');
		var wlId = target.attr('data-wlId');
		var groupId = target.attr('data-groupId');
		invitePlayer(charId, wlId, groupId);
	}

	function removePlayerHandler(event) {
		var target = $(event.currentTarget);
		var charId = target.attr('data-characterid');
		var groupId = target.attr('data-groupId');
		removePlayer(charId, groupId);
	}

	function openCharInfoHandler(event) {
		var target = $(event.currentTarget);
		var charId = target.attr('data-characterid');
		showInfo(1337, charId);
	}

	function fitViewed(fitId) {
		var viewed = $("#" + fitId).attr('data-viewed');
		var child = $("#" + fitId).children('.booby-link').hasClass("booby-link");
		if (viewed === "y" || child) {
			return true;
		} else {
			return false;
		}
	}

	function entryViewed(wlId, entryId) {
		var fits = document.getElementById('fittings-' + entryId).childNodes;
		var viewed = true;
		for (let fit of fits) {
			if (!fitViewed(fit.id)) {
				viewed = false;
			}
		}
		return viewed;
	}

	function onViewfit(event) {
		const fit = event.currentTarget.offsetParent;
        if (fit.dataset.viewed !== "y") {
        	document.getElementById(fit.id).setAttribute("data-viewed", "y");
        }
	}

	function init() {
		$('#waitlists').on("click", '[data-action="approveFit"]',
			approveFitHandler);
		$('#waitlists').on('click', '[data-action="approveEntry"]',
			approveEntryHandler);
		$('#waitlists').on('click', '[data-action="sendNotification"]',
			sendNotificationHandler);
		$('#waitlists').on('click', '[data-action="dismissEntry"]',
			dismissEntryHandler);
		$('#waitlists').on('click', '[data-action="invitePlayer"]',
			invitePlayerHandler);
		$('#waitlists').on('click', '[data-action="removePlayer"]',
			removePlayerHandler);
		$('body').on('click', '[data-action="openCharInfo"]',
			openCharInfoHandler);
		$('#waitlists').on('click', '[href^="fitting:"],[data-dna]',
		 	onViewfit);
	}

	$(document).ready(init);

	return {};
})();
