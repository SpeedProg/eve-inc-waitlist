/**
 * Get meta elements content from the website
 */
var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

var is_igb = /.*EVE-IGB/.test(navigator.userAgent);

function displayMessage(message, type) {
	var alertHTML = $($.parseHTML('<div class="alert alert-dismissible" role="alert">'+
			'<button type="button" class="close" data-dismiss="alert" aria-label="Close">'+
    			'<span aria-hidden="true">&times;</span>'+
  			'</button>'+
			'<p class="text-xs-center"></p>'+
			'</div>'));
	var textContainer = $('.text-xs-center', alertHTML);
	textContainer.html(message);
	alertHTML.addClass('alert-'+type);
	var alertArea = $('#alert-area-base');
	alertArea.append(alertHTML)
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
 * Create a DOM for a ship type tag
 * @param tag: B = Basi, S = Scimi, DPS = Short Range Damage, SNI = Sniper, LOGI == Scruffy Logi
 */
function createTypeTag(name) {
	var type = "default";
	switch (name) {
	case "B":
	case "S":
	case "LOGI":
		type = "success";
		break;
	case "DPS":
		type = "danger";
		break;
	case "SNI":
		type = "warning";
		break;
	default:
		type = "default";
	}
	return $.parseHTML('<span class="tag tag-'+type+'">'+name+'</span>');
}

/**
 * Add a new entry to the given list
 * @param wlname name of the waitlist the entry needs to be added to
 * @param wlid id of the waitlist
 * @param entry the entry object as received from the api
 */
function addNewEntry(wlname, wlid, entry, groupID) {
	var entryDOM = createEntryDOM(wlname, wlid, entry, groupID);
	var wlEntryContainer = $('#wl-fits-'+wlid);
	wlEntryContainer.append(entryDOM);
}

/**
 * Get which tags these fits create
 * @param fits fits object as received from the API
 * @returns {Array} list of tags
 */
function getTagsFromFits(fits) {
	var tags = {};
	var addTag = function(name) {
		if (name in tags) {
			return
		}
		tags[name] = true;
	}
	for (var i=0; i < fits.length; i++) {
		switch (fits[i].wl_type) {
		case "logi":
			// since we want to have basi/scimi specificly need to check shipType here
			if (fits[i].shipType == 11985) {
				addTag("B");
			} else if (fits[i].shipType == 11978) {
				addTag("S");
			} else if (fits[i].shipType == 1) {
				// it is scruffy
				addTag("LOGI");
			}
			break;
		case "sniper":
			addTag("SNI");
			break;
		case "dps":
			addTag("DPS");
			break;
		default:
			break;
		}
	}
	// make a list out of the object properties
	var tagList = [];
	for (var tag in tags) {
		tagList.push(tag);
	}
	return tagList;
}

/**
 * Create the html entity for the entry's header
 * @param wlname name of the waitlist the entry belongs to
 * @parm wlid id of the waitlist
 * @param entry the waitlist entry as received from the api
 * @returns {HTMLElement} DOM fo the entries header
 */
function createHeaderDOM(wlname, wlid, entry, groupId) {
	var tags = getTagsFromFits(entry.fittings);
	var newBroTag = "";
	if (entry.character.newbro) {
		newBroTag = ' <span class="tag tag-info">New</span>';
	}
	var cTime = new Date(Date.now());
	var xupTime = new Date(Date.parse(entry.time));
	var waitTimeMinutes = Math.floor((cTime - xupTime)/60000);
	var header = $('<div></div>');
	var oldInvites = "";
	if (wlname != "queue") {
		if (entry.missedInvites > 0) {
			oldInvites = " <div class='missed-invites' style='display: inline;'><div style='display: inline;' class='missed-invites-number'>"+entry.missedInvites+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="Missed Invites"></i></div>';
		} else {
			oldInvites = " <div class='missed-invites' style='display: inline;'></div>";
		}
	}
	var charRow = $('<a href="javascript:IGBW.showInfo(1377, '+entry.character.id+');" data-ext="char-header" data-clipboard-text="'+entry.character.name+'">'+
						'<div class="wel-header-32">'+
									'<img class="img-32" src="https://imageserver.eveonline.com/Character/'+entry.character.id+'_32.jpg" alt="'+entry.character.name+'">'+
							'<div class="wel-container-32">'+
								'<div class="wel-text-row-32-2">'+entry.character.name+oldInvites+newBroTag+' <small class="wait-time">'+waitTimeMinutes+' min ago</small></div>'+
								'<div class="wel-text-row-32-2 tag-row"></div>'+
							'</div>'+
						'</div>'+
						'</a>');
	var tagContainer = $('div.tag-row', charRow);
	for (var i = 0; i < tags.length; i++) {
		tagContainer.append(createTypeTag(tags[i]));
	}
	var convoButton = ""
	if (is_igb) {
		convoButton = '<button type="button" class="btn btn-secondary" onclick="javascript:IGBW.startConversation('+entry.character.id+')"><i class="fa fa-comment-o"></i></button>';
	}
	var buttonRow = null;
	if (wlname == "queue") {
		buttonRow = $('<div>'+
				'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
					'<button type="button" class="btn btn-success" onclick="javascript:moveEntryToWaitlists('+entry.id+', '+entry.character.id+')"><i class="fa fa-thumbs-o-up"></i></button>'+
					'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-caret-down"></i></i> Fits</button>'+
					'<button type="button" class="btn btn-success" onclick="javascript:sendNotification('+entry.character.id+', '+wlid+')"><i class="fa fa-bell-o"></i></button>'+
					convoButton+
					'<button type="button" class="btn btn-danger" onclick="javascript:removeEntry('+entry.id+', '+entry.character.id+');"><i class="fa fa-times"></i></button>'+
				'</div>'+
			'</div>');
	} else {
		buttonRow = $('<div>'+
					'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
						'<button type="button" class="btn btn-success" onclick="javascript:invitePlayer('+entry.character.id+', '+wlid+', '+groupId+')"><i class="fa fa-plus"></i></button>'+
						'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-caret-down"></i> Fits</button>'+
						'<button type="button" class="btn btn-success" onclick="javascript:sendNotification('+entry.character.id+', '+wlid+')"><i class="fa fa-bell-o"></i></button>'+
						convoButton+
						'<button type="button" class="btn btn-danger" onclick="javascript:removePlayer('+entry.character.id+', '+groupId+');"><i class="fa fa-times"></i></button>'+
					'</div>'+
				'</div>');
	}

	header.append(charRow);
	header.append(buttonRow);
	return header;
}

/**
 * Create the html entity of the entry
 * @param wlname name of the waitlist the entry belongs to
 * @param wlid id of the waitlist
 * @param entry the entry object as received from the api
 * @returns {HTMLElement} DOM of an entry
 */
function createEntryDOM(wlname, wlid, entry, groupID) {
	var entryDOM = $('<li class="list-group-item" id="entry-'+wlname+'-'+entry.character.id+'" data-count="'+entry.fittings.length+'"></li>');
	entryDOM.append(createHeaderDOM(wlname, wlid, entry, groupID));
	var fittlistDOM = $('<ul aria-expanded="true" class="list-group list-group-flush collapse" id="fittings-'+entry.id+'"></ul>')
	entryDOM.append(fittlistDOM);
	for (var i=0; i<entry.fittings.length; i++) {
		fittlistDOM.append(createFitDOM(entry.fittings[i], wlname == "queue" ? true : false, entry));
	}
	return entryDOM;
}

/**
 * Updates fits of entries
 * @param wlname name of the waitlist the entry belongs to
 * @param wlid id of the waitlist the entry belongs to
 * @param entry the entry object as received from the api
 * @returns {Number} number of new entry that where added (0 or 1)
 */
function updateWlEntry(wlname, wlid, entry) {
	var jEntries = $('#entry-'+wlname+'-'+entry.character.id);
	if (jEntries.length > 0) {
		// update the wait time
		// ' <small class="wait-time">'+waitTimeMinutes+' min ago</small>
		var wtElement = $('.wait-time', jEntries[0]);
		var cTime = new Date(Date.now());
		var xupTime = new Date(Date.parse(entry.time));
		var waitTimeMinutes = Math.floor((cTime - xupTime)/60000);
		var newTimeText = waitTimeMinutes+" min ago";
		var oldTimeText = wtElement.text();
		if (oldTimeText != newTimeText) {
			wtElement.text(newTimeText);
		}
		
		// update the missed invites
		if (entry.missedInvites > 0) {
			var invNumElement = $('.missed-invites-number', jEntries[0])
			if (invNumElement.length > 0) {
				var oldNum = Number(invNumElement.text());
				if (oldNum != entry.missedInvites) {
					invNumElement.text(entry.missedInvites);
				}
			} else {
				var invElement = $('.missed-invites', jEntries[0]);
				var counterElement = $.parseHTML("<div style='display: inline;' class='missed-invites-number'>"+entry.missedInvites+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="Missed Invites"></i>');
				invElement.append(counterElement);
			}
		} else {
			var invNumElement = $('.missed-invites-number', jEntries[0]);
			if (invNumElement.length > 0) {
				var invElement = $('.missed-invites', jEntries[0]);
				invElement.empty();
			}
		}
		// update fits and such
		var modified = false;
		// backup of original fits, we gonna need them later if sth was modified
		var fittings = entry.fittings.slice();
		var jFittings = $($('#fittings-'+entry.id)[0]);
		var existingFits = jFittings.children();
		// we remove fits that are not in the received data,
		// and filter out those that where already on the page
		existingFits.each(function(){
			// check if fit still exists
			var currentElement = $(this);
			var currentId = currentElement.attr("id");
			currentId = Number(currentId.slice(4));
			var is_existing = false
			for (var i=0; i < entry.fittings.length; i++ ) {
				var fit = entry.fittings[i];
				if (fit.id == currentId) {
					is_existing = true;
					entry.fittings.splice(i, 1); // this fit is already there we don't need it
					i=i-1;
					break;
				}
			}
			if (! is_existing) {
				// we need to remove the fit
				modified = true;
				currentElement.remove();
			}
			
		});
		
		// now we add the new fits
		if (entry.fittings.length > 0) {
			modified = true;
		}
		for (var i=0; i < entry.fittings.length; i++) {
			jFittings.append(createFitDOM(entry.fittings[i], wlname == "queue" ? true : false));
		}
		
		// if we modified sth update the tags
		if (modified) {
			var tags = getTagsFromFits(fittings);
			var tagContainer = $('div.tag-row', jEntries);
			tagContainer.empty();
			for (var i = 0; i < tags.length; i++) {
				tagContainer.append(createTypeTag(tags[i]));
			}
		}
	}
}

/**
 * Creat html entity of a fit
 * @param fit fit object as received from the api
 * @param pass if it is the x-up list, so we can add approve button, defaults to false
 * @returns {HTMLElement} the fit's DOM
 */
function createFitDOM(fit, queue, entry) {
	queue = typeof queue !== 'undefined' ? queue : false;
	var isDummy = (fit.shipType == 1);
	var approveButton = "";
	if (queue) {
		approveButton = ' <button type="button" class="btn btn-mini btn-success" data-type="fit-approve" data-id="'+fit.id+'"><i class="fa fa-thumbs-o-up"></i></button>';
	}
	var fitdom = isDummy ? $($.parseHTML('<li class="list-group-item fitting" id="fit-'+fit.id+'"></li>')) : $($.parseHTML('<li class="list-group-item fitting" id="fit-'+fit.id+'"></li>'));
	var commentHTML = "";
	if (fit.comment != null) {
		commentHTML = '<small>'+fit.comment+'</small>';
	}
	// lets check if it is the dummy fit
	
	var baseElement = isDummy ? $.parseHTML('<div class="booby-link"></div>') : $.parseHTML('<div class="fit-link" data-title="'+entry.character.name+'" data-dna="'+fit.dna+'"></div>');
	fitdom.append(
			$(baseElement)
				.append($($.parseHTML('<div class="wel-header-32"></div>'))
						.append($.parseHTML('<img class="img-32" src="https://imageserver.eveonline.com/Render/'+fit.shipType+'_32.png" alt="'+fit.shipName+'">'))
						.append($.parseHTML('<div class="wel-container-32"><div class="wel-text-row-32-2">'+fit.shipName+'</div><div class="wel-text-row-32-2">'+commentHTML+approveButton+'</div></div>'))
						)
			);
	return fitdom
	// add own fit removal button if its your own entry :/
	
}

/**
 * Remove a entries from a waitlist
 * @param wldata wl object as received from the api
 */
function cleanWL(wldata) {
	var wlbody = $('#wl-fits-'+wldata.id);
	wlbody.empty();
}

/**
 * Remove missing entries from DOM
 * @param wldata waitlist data as received from api
 * @returns {Number} number of entries that where removed
 */
function deleteMissingEntries(wldata) {
	var removeCount = 0;
	var entries = $('li[id|="entry-'+wldata.name+'"]');
	var preLen = ("entry-"+wldata.name+"-").length;
	for (var i=0; i < entries.length; i++) {
		var id = $(entries[i]).attr("id");
		id = Number(id.slice(preLen))
		var is_existing = false;
		for (var n=0; n < wldata.entries.length; n++) {
			if (wldata.entries[n].character.id == id) {
				is_existing = true;
				break;
			}
		}
		if (! is_existing) {
			$(entries[i]).remove();
			removeCount += 1;
		}
	}
	return removeCount;
}

// before using this all none existing entries need to be removed from the DOM
/**
 * Adds entries that do not exist in the DOM at their correct positions
 * @param wldata waitlist data as received from the api
 * @return {Number} number of added entries
 */
function addNewEntries(wldata, groupID) {
	var preLen = ("entry-"+wldata.name+"-").length;
	var entries = $('li[id|="entry-'+wldata.name+'"]');
	var domEntryCount = entries.length;
	var addedCounter = 0;

	// we iterate over our entries, they are in the right order
	// if we do not match with the entry at the same position in the dom
	// there needs to be added the current entry there
	// if we do match, we need to check the fits there
	var inserAfterElement = null;
	for (var n=0; n < wldata.entries.length; n++) {
		var currentDOMIdx = n-addedCounter;
		if (currentDOMIdx < domEntryCount) {
			var currentDOM = $(entries[n-addedCounter]);
			var domId = Number(currentDOM.attr('id').slice(preLen));
			// if ids match == check for fits that need to be updated
			if (domId == wldata.entries[n].character.id) {
				inserAfterElement = currentDOM;
				updateWlEntry(wldata.name, wldata.id, wldata.entries[n]);
			} else {
				// we need to add a new entry
				var entryDOM = createEntryDOM(wldata.name, wldata.id, wldata.entries[n], groupID);
				if (inserAfterElement == null) {
					var wlEntryContainer = $('#wl-fits-'+wldata.id);
					wlEntryContainer.prepend(entryDOM);
					inserAfterElement = entryDOM;
				} else {
					inserAfterElement.after(entryDOM);
				}
				inserAfterElement = entryDOM;
				addedCounter += 1;
			}
		} else {
			var entryDOM = createEntryDOM(wldata.name, wldata.id, wldata.entries[n], groupID);
			if (inserAfterElement == null) {
				var wlEntryContainer = $('#wl-fits-'+wldata.id);
				wlEntryContainer.prepend(entryDOM);
				inserAfterElement = entryDOM;
			} else {
				inserAfterElement.after(entryDOM);
			}
			inserAfterElement = entryDOM;
			addedCounter += 1;
		}
	}
	return addedCounter;
}

/**
 * Update a waitlist
 * @param wldata waitlist object as received from the api
 */
function updateWaitlist(wldata, groupID) {
	var removedEntryCount = deleteMissingEntries(wldata);
	var addedEntryCount = addNewEntries(wldata, groupID);
	var oldCount = getWlEntryCount(wldata.name);
	var newCount = oldCount + addedEntryCount - removedEntryCount;
	setWlEntryCount(wldata.name, newCount);
}

/**
 * Set the entry counter for a given waitlist
 * @param wlname name of the waitlist
 * @param count count of entries to set to
 */
function setWlEntryCount(wlname, count) {
	var dataElement = $('#wl-'+wlname);
	dataElement.data("count", count);
	var textElement = $('#wl-count-'+wlname);
	textElement.text(count);
}

/**
 * Get the count for a given waitlist
 * @param wlname name of the waitlist
 * @returns {Number} count of entries in the waitlist
 */
function getWlEntryCount(wlname) {
	var dataElement = $('#wl-'+wlname);
	return Number(dataElement.data("count"));
}

/**
 * Refresh entries of all waitlists with the data from the API
 */
function refreshWl() {
	var wlid = getMetaData('wl-group-id');
	if (typeof wlid != 'undefined') {
		$.getJSON(getMetaData('api-waitlists')+"?group="+wlid, function(data){
			for (var i=0; i < data.waitlists.length; i++) {
				updateWaitlist(data.waitlists[i], data.groupID);
			}
		});
	}
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
		clearInterval(lastRefreshInterval);
		refreshWl();
		lastRefreshInterval = setInterval(refreshWl, 10000);
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
function removeEntry(entryId, userId) {
	$.post(getMetaData('api-wl-remove-entry'), {'entryId': entryId, '_csrf_token': getMetaData('csrf-token')}, function(){
		clearInterval(lastRefreshInterval);
		refreshWl();
		lastRefreshInterval = setInterval(refreshWl, 10000);
	}, "text");
	var entry_id = "entry-queue-"+userId
	var entry = document.getElementById(entry_id);
	if (entry != null) { // there is a entry for him on that wl
		entry.parentNode.removeChild(entry); // remote it from the DOM
		setWlEntryCount("queue", getWlEntryCount("queue")-1)
	}
}
var lastRefreshInterval;
/**
 * Move a X-UP entry to waitlists (approving)
 * @param entryId id of the entry that should be approved
 * @param userId eve id the of the user the entry belongs to
 */
function moveEntryToWaitlists(entryId, userId) {
	var entryDOM = $("#entry-queue-"+userId);
	var fitDOMs = $(".fitting", entryDOM);
	var fit_id_str = "";
	var fitCount = fitDOMs.length;
	fitDOMs.each(function(idx, element){
		var cIdStr = $(element).attr("id");
		var cId = cIdStr.substring(4, cIdStr.length);
		fit_id_str += cId;
		if (idx < fitCount-1) {
			fit_id_str += ","
		}
	});
	$.post(getMetaData('api-move-entry-to-wls'), {'entryId': entryId, 'fitIds': fit_id_str, '_csrf_token': getMetaData('csrf-token')}, function(){
		clearInterval(lastRefreshInterval);
		refreshWl();
		lastRefreshInterval = setInterval(refreshWl, 10000);
	}, "text");
	var entry_id = "entry-queue-"+userId
	var entry = document.getElementById(entry_id);
	if (entry != null) { // there is a entry for him on that wl
		entry.parentNode.removeChild(entry); // remote it from the DOM
		setWlEntryCount("queue", getWlEntryCount("queue")-1)
	}
}

/**
 * Mave a single fit to waitlist
 */
function approveFit(fitId) {
	// remove this before sending, since the fit-id stays in existance and we could by accident remove it afterwards from the waitlist
	var entry_id = "fit-"+fitId
	var entry = document.getElementById(entry_id);
	if (entry != null) { // there is a entry for him on that wl
		parent = entry.parentNode;
		parent.removeChild(entry); // remove it from the DOM
		if (parent.childNodes.length == 0) { // if there is not fit anymore remove the entry from the dom too
			entry = parent.parentNode;
			entry.parentNode.removeChild(entry);
			setWlEntryCount("queue", getWlEntryCount("queue")-1)
		}
	}
	$.post(getMetaData('api-approve-fit'), {'fit_id': fitId, '_csrf_token': getMetaData('csrf-token')}, function(){
		clearInterval(lastRefreshInterval);
		refreshWl();
		lastRefreshInterval = setInterval(refreshWl, 10000);
	}, "text");
}

/**
 * Load the old state of the waitlists (open/closed) and start the entry update interval
 */
$(document).ready(function(){
	var wlists = $('ol[id|="wl-fits"]');
	for (var i=0; i < wlists.length; i++) {
		var wl = $(wlists[i]);
		var wlId = wl.attr("id");
		var cookie = $.cookie(wlId);
		if (cookie == null) {
			$.cookie(wlId, "closed");
			cookie = "closed";
		}

		if (cookie == "closed") {
			wl.collapse('hide');
		} else if (cookie == "open") {
			wl.collapse('show');
		}
	}
	$(document).on("click", '[data-type="fit-approve"]', function(event) {
		var fit_id = Number($(event.currentTarget).data('id'));
		event.stopPropagation();
		approveFit(fit_id);
	});
	refreshWl();
	lastRefreshInterval = setInterval(refreshWl, 10000);
	new Clipboard('[data-ext="char-header"]');
});
