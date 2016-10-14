/**
 * Get meta elements content from the website
 */
var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

/**
 * Sends out a notification
 * @param charId
 * @param wlid
 */
function sendNotification(charID, waitlistID) {
	$.post({
		'url':getMetaData('api-send-notification').replace("-1", charID),
		'data': {
			'waitlistID': waitlistID,
			'_csrf_token': getMetaData('csrf-token')
		},
		'error': function(data) {
			var message = data.statusText
			if (typeof data.message != 'undefined') {
					message += ": " + data.message;
			}
			displayMessage(message, "danger");
		},
		'success': function(data){
		},
		'dataType': 'json'
	});
}

/**
 * Send the notification for a player,  and logs from which wl he was invited
 * @param userId eve id of the user, the notification should be send too
 */
function invitePlayer(userID, waitlistID, groupID) {
	$.post({
		'url':getMetaData('api-send-invite'),
		'data': {
			'charID': userID,
			'waitlistID': waitlistID,
			'groupID': groupID,
			'_csrf_token': getMetaData('csrf-token')
		},
		'error': function(data) {
			var message = data.statusText
			if (typeof data.message != 'undefined') {
					message += ": " + data.message;
			}
			if (typeof data.responseJSON != 'undefined' && typeof data.responseJSON.message != 'undefined') {
				message += ": " + data.responseJSON.message
			}
			displayMessage(message, "danger");
		},
		'success': function(data){
		},
		'dataType': 'json'
	});
}

/**
 * Remove a player from Waitlists and not X-UP
 * @param userId eve id of the user that should be removed
 */
function removePlayer(userId, groupId) {
	$.post(getMetaData('api-wls-remove-player'), {'playerId': userId, 'groupId': groupId, '_csrf_token': getMetaData('csrf-token')}, function(){
	}, "text");
	var wl_names = getMetaData('wl-names').split(',');
	for (idx in wl_names) {
		var wl_name = wl_names[idx]
		var entry_id = "entry-"+wl_name+"-"+userId
		var entry = document.getElementById(entry_id);
		if (entry != null) { // there is a entry for him on that wl
			entry.parentNode.removeChild(entry); // remote it from the DOM
			setWlEntryCount(wl_name, getWlEntryCount(wl_name)-1)
		}
	 }
}

/**
 * Remove a specific entry (from X-UP)
 * @param entryId id of the entry to remove
 * @param userId user id the entry belongs to
 */
function removeEntry(wlId, entryId) {
	$.post(getMetaData('api-wl-remove-entry'), {'entryId': entryId, '_csrf_token': getMetaData('csrf-token')}, function(){
	}, "text");
	removeEntryFromDom(wlId, entryId);
}

/**
 * Move a X-UP entry to waitlists (approving)
 * @param entryId id of the entry that should be approved
 * @param userId eve id the of the user the entry belongs to
 */
function moveEntryToWaitlists(wlId, entryId) {
	var entryDOM = $("#entry-"+wlId+"-"+entryId);
	var fitDOMs = $(".fitting", entryDOM);
	var fit_id_str = "";
	var fitCount = fitDOMs.length;
	var fitid_prefix_length = ("fit-"+wlId+"-"+entryId+"-").length;
	
	fitDOMs.each(function(idx, element){
		var cIdStr = $(element).attr("id");
		var cId = cIdStr.substring(fitid_prefix_length, cIdStr.length);
		fit_id_str += cId;
		if (idx < fitCount-1) {
			fit_id_str += ","
		}
	});
	$.post(getMetaData('api-move-entry-to-wls'), {'entryId': entryId, 'fitIds': fit_id_str, '_csrf_token': getMetaData('csrf-token')}, function(){
	}, "text");
}

/**
 * Mave a single fit to waitlist
 */
function approveFit(wlId, entryId, fitId) {
	$.post(getMetaData('api-approve-fit'), {'fit_id': fitId, '_csrf_token': getMetaData('csrf-token')}, function(){
	}, "text");
}

/**
 * Load the old state of the waitlists (open/closed) and start the entry update interval
 */
$(document).ready(function(){
	var wlists = $('ol[id|="wl-fits"]');
	$(document).on("click", '[data-type="fit-approve"]', function(event) {
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-id'));
		var wlId = Number(target.attr('data-wlId'));
		var entryId = Number(target.attr('data-entryId'));
		event.stopPropagation();
		approveFit(wlId, entryId, fitId);
	});
	new Clipboard('[data-ext="char-header"]');
});
