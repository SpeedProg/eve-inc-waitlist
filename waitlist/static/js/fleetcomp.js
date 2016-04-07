var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

/**
 * @param tag: B = Basi, S = Scimi, DPS = Short Range Damage, SNI = Sniper, LOGI == Scruffy Logi
 */
function createTypeTag(name) {
	type = "default";
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
	return $.parseHTML('<span class="label label-'+type+'">'+name+'</span>');
}

/**
 * Add a new entry to the given list
 * @param wlname name of the waitlist the entry needs to be added to
 * @param wlid id of the waitlist
 * @param entry the entry object as received from the api
 */
function addNewEntry(wlname, wlid, entry) {
	var entryDOM = createEntryDOM(wlname, entry);
	var wlEntryContainer = $('#wl-fits-'+wlid);
	wlEntryContainer.append(entryDOM);
}

/**
 * Get which labels these fits create
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
 * @param entry the waitlist entry as received from the api
 * @returns
 */
function createHeaderDOM(wlname, entry) {
	var tags = getTagsFromFits(entry.fittings);
	var header = $('<div></div>');
	var charRow = $('<a href="javascript:CCPEVE.showInfo(1377, '+entry.character.id+');">'+
						'<div class="wel-header-32">'+
							'<div class="wel-img-32">'+
									'<img src="https://image.eveonline.com/Character/'+entry.character.id+'_32.jpg" alt="'+entry.character.name+'">'+
							'</div>'+
							'<div class="wel-container-32">'+
								'<div class="wel-text-row-32-2">'+entry.character.name+'</div>'+
								'<div class="wel-text-row-32-2 tag-row"></div>'+
							'</div>'+
						'</div>'+
						'</a>');
	var tagContainer = $('div.tag-row', charRow);
	for (var i = 0; i < tags.length; i++) {
		tagContainer.append(createTypeTag(tags[i]));
	}
	var buttonRow = null;
	if (wlname == "queue") {
		buttonRow = $('<div>'+
				'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
					// only if it is your own entry
					//'<button type="button" class="btn btn-mini btn-warning" onclick="javascript:removeOwnEntry(\'queue\', '+entry.character.id+', '+entry.id+');">Remove Self</button>'+
					'<button type="button" class="btn btn-success" onclick="javascript:moveEntryToWaitlists('+entry.id+', '+entry.character.id+')"><i class="fa fa-thumbs-o-up"></i></button>'+
					'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-plus"></i> &#47; <i class="fa fa-minus"></i> Fits</button>'+
					'<button type="button" class="btn btn-secondary" onclick="javascript:CCPEVE.startConversation('+entry.character.id+')"><i class="fa fa-comment-o"></i></button>'+
					'<button type="button" class="btn btn-danger" onclick="javascript:removeEntry('+entry.id+', '+entry.character.id+');"><i class="fa fa-times"></i></button>'+
				'</div>'+
			'</div>');
	} else {
		buttonRow = $('<div>'+
					'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
					'<button type="button" class="btn btn-success" onclick="javascript:invitePlayer('+entry.character.id+')"><i class="fa fa-bell-o"></i></button>'+
						'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-plus"></i> &#47; <i class="fa fa-minus"></i> Fits</button>'+
						'<button type="button" class="btn btn-secondary" onclick="javascript:CCPEVE.startConversation('+entry.character.id+')"><i class="fa fa-comment-o"></i></button>'+
						'<button type="button" class="btn btn-danger" onclick="javascript:removePlayer('+entry.character.id+');"><i class="fa fa-times"></i></button>'+
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
 * @param entry the entry object as received from the api
 */
function createEntryDOM(wlname, entry) {
	var entryDOM = $('<li class="list-group-item" id="entry-'+wlname+'-'+entry.character.id+'" data-count="'+entry.fittings.length+'"></li>');
	var cardDOM = $('<div class="card"></div>');
	cardDOM.append(createHeaderDOM(wlname, entry));
	entryDOM.append(cardDOM);
	var fittlistDOM = $('<ul aria-expanded="true" class="list-group list-group-flush collapse" id="fittings-'+entry.id+'"></ul>')
	entryDOM.append(fittlistDOM);
	for (var i=0; i<entry.fittings.length; i++) {
		fittlistDOM.append(createFitDOM(entry.fittings[i], wlname == "queue" ? true : false));
	}
	return entryDOM;
}

/**
 * Check and add a entry to the DOM if it doesn't exist
 * @param wlname name of the waitlist the entry belongs to
 * @param wlid id of the waitlist the entry belongs to
 * @param entry the entry object as received from the api
 * @returns {Number} number of new entry that where added (0 or 1)
 */
function updateWlEntry(wlname, wlid, entry) {
	var new_entry_count = 0;
	var jEntries = $('#entry-'+wlname+'-'+entry.character.id);
	if (jEntries.size() <= 0) {
		addNewEntry(wlname, wlid, entry);
		new_entry_count = 1;
	} else {
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
	return new_entry_count;
}

/**
 * Creat html entity of a fit
 * @param fit fit object as received from the api
 * @param pass if it is the x-up list, so we can add approve button, defaults to false
 * @returns {HTMLElement} the fit's DOM
 */
function createFitDOM(fit, queue) {
	queue = typeof queue !== 'undefined' ? queue : false;
	var isDummy = (fit.shipType == 1);
	var approveButton = "";
	if (queue) {
		approveButton = ' <button type="button" class="btn btn-mini btn-success" onclick="javascript:var event = arguments[0]; event.stopPropagation(); approveFit('+fit.id+')"><i class="fa fa-thumbs-o-up"></i></button>';
	}
	var fitdom = isDummy ? $($.parseHTML('<li class="list-group-item" id="fit-'+fit.id+'"></li>')) : $($.parseHTML('<li class="list-group-item fitting" id="fit-'+fit.id+'"></li>'));
	var commentHTML = "";
	if (fit.comment != null) {
		commentHTML = '<small>'+fit.comment+'</small>';
	}
	// lets check if it is the dummy fit
	
	var baseElement = isDummy ? $.parseHTML('<div></div>') : $.parseHTML('<div class="fit-link" data-dna="'+fit.dna+'"></div>');
	fitdom.append(
			$(baseElement)
				.append($($.parseHTML('<div class="wel-header-32"></div>'))
						.append($.parseHTML('<div class="wel-img-32"><img src="https://image.eveonline.com/Render/'+fit.shipType+'_32.png" alt="'+fit.shipName+'"></div>'))
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
 * Update a waitlist
 * @param wldata waitlist object as received from the api
 */
function updateWaitlist(wldata) {
	var waitlist = $('#wl-'+wldata.name)[0];
	// if there are no entrys in the wl make sure that there ain't any on our page
	if (wldata.entries.length == 0) {
		cleanWL(wldata);
		setWlEntryCount(wldata.name, 0);
	} else {
		var new_entry_count = 0;
		for (var i = 0; i < wldata.entries.length; i++) {
			new_entry_count += updateWlEntry(wldata.name, wldata.id, wldata.entries[i]);
		}
		// now that all are updated delete entrys that are not in existance
		var entries = $('li[id|="entry-'+wldata.name+'"]');
		var preLen = ("entry-"+wldata.name+"-").length;
		for (var i=0; i < entries.size(); i++) {
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
				new_entry_count -= 1;
			}
		}
		var oldCount = getWlEntryCount(wldata.name);
		var newCount = oldCount + new_entry_count;
		setWlEntryCount(wldata.name, newCount);
	}
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
	$.getJSON(getMetaData('api-waitlists'), function(data){
		for (var i=0; i < data.waitlists.length; i++) {
			updateWaitlist(data.waitlists[i]);
		}
	});
}

/**
 * Send the notification for a player
 * @param userId eve id of the user, the notification should be send too
 */
function invitePlayer(userId) {
	$.post(getMetaData('api-invite-player'), {'playerId': userId, '_csrf_token': getMetaData('csrf-token')}, function(){
	}, "text");
}

/**
 * Remove a player from Waitlists and not X-UP
 * @param userId eve id of the user that should be removed
 */
function removePlayer(userId) {
	$.post(getMetaData('api-wls-remove-player'), {'playerId': userId, '_csrf_token': getMetaData('csrf-token')}, function(){
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

/**
 * Move a X-UP entry to waitlists (approving)
 * @param entryId id of the entry that should be approved
 * @param userId eve id the of the user the entry belongs to
 */
function moveEntryToWaitlists(entryId, userId) {
	$.post(getMetaData('api-move-entry-to-wls'), {'entryId': entryId, '_csrf_token': getMetaData('csrf-token')}, function(){
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
	for (var i=0; i < wlists.size(); i++) {
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
	refreshWl();
	lastRefreshInterval = setInterval(refreshWl, 10000);
});