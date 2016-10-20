'use strict';
/**
 * Get meta elements content from the website
 */
if (!getMetaData){
	var getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
}

var can_view_fits = (getMetaData('can-view-fits') === "True");
var can_manage = (getMetaData('can-fleetcomp') === "True");
var user_id = Number((getMetaData('user-id')));

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
	alertArea.append(alertHTML);
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
 * Get which tags these fits create
 * @param fits fits object as received from the API
 * @returns {Array} list of tags
 */
function getTagsFromFits(fits) {
	var tags = {};
	var addTag = function(name) {
		if (name in tags) {
			return;
		}
		tags[name] = true;
	};
	for (var i=0; i < fits.length; i++) {
		addTag(getTagFromJsonFit(fits[i]));
	}
	// make a list out of the object properties
	var tagList = [];
	for (var tag in tags) {
		tagList.push(tag);
	}
	return tagList;
}

function getTagFromJsonFit(jsonFit) {
	switch (jsonFit.wl_type) {
	case "logi":
		// since we want to have basi/scimi specificly need to check shipType here
		if (jsonFit.shipType === 11985) {
			return "B";
		} else if (jsonFit.shipType === 11978) {
			return "S";
		} else if (jsonFit.shipType === 1) {
			// it is scruffy
			return "LOGI";
		}
		break;
	case "sniper":
		return "SNI";
	case "dps":
		return "DPS";
	case "other":
		return "OTHER";
	default:
		return "UNKNOWN";
	}
}

/**
 * Create the html entity for the entry's header
 * @param wlname name of the waitlist the entry belongs to
 * @parm wlid id of the waitlist
 * @param entry the waitlist entry as received from the api
 * @returns {HTMLElement} DOM fo the entries header
 */
function createHeaderDOM(wlid, entry, groupId, isQueue) {
	var newBroTag = "";
	if ((can_view_fits || entry.character.id === user_id) && entry.character.newbro) {
		newBroTag = ' <span class="tag tag-info">New</span>';
	}
	var cTime = new Date(Date.now());
	var xupTime = new Date(Date.parse(entry.time));
	var waitTimeMinutes = Math.max(0, Math.floor((cTime - xupTime)/60000));
	var header = $('<div></div>');
	var oldInvites = "";
	if ((can_view_fits || entry.character.id === user_id) && !isQueue) {
		if (entry.missedInvites > 0) {
			oldInvites = " <div class='missed-invites' style='display: inline;' data-userId='"+entry.character.id+"'><div style='display: inline;' class='missed-invites-number'>"+entry.missedInvites+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="Missed Invites"></i></div>';
		} else {
			oldInvites = " <div class='missed-invites' style='display: inline;' data-userId='"+entry.character.id+"'></div>";
		}
	}
	
	// make managers call the CREST API others should open in quie's tool
	var charHref = can_manage ? 'javascript:IGBW.showInfo(1377, '+entry.character.id+');' : 'char:'+entry.character.id;
	var charRow = $('<a href="' + charHref + '" data-ext="char-header">'+
						'<div class="wel-header-32">'+
									'<img class="img-32" src="https://imageserver.eveonline.com/Character/'+entry.character.id+'_32.jpg" alt="'+entry.character.name+'">'+
							'<div class="wel-container-32">'+
								'<div class="wel-text-row-32-2">'+entry.character.name+oldInvites+newBroTag+' <small class="wait-time" data-time="'+entry.time+'">'+waitTimeMinutes+' min ago</small></div>'+
								'<div class="wel-text-row-32-2 tag-row"></div>'+
							'</div>'+
						'</div>'+
						'</a>');
	if (can_view_fits || entry.character.id === user_id) {
		var tags = getTagsFromFits(entry.fittings);
		var tagContainer = $('div.tag-row', charRow);
		for (var i = 0; i < tags.length; i++) {
			tagContainer.append(createTypeTag(tags[i]));
		}
	}
	var convoButton = "";
	var buttonRow = null;
	if (can_manage && isQueue) { // fleetcom queue
		buttonRow = $('<div>'+
				'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
					'<button type="button" class="btn btn-success" onclick="javascript:moveEntryToWaitlists('+wlid+', '+entry.id+')"><i class="fa fa-thumbs-o-up"></i></button>'+
					'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-caret-down"></i></i> Fits</button>'+
					'<button type="button" class="btn btn-success" onclick="javascript:sendNotification('+entry.character.id+', '+wlid+')"><i class="fa fa-bell-o"></i></button>'+
					convoButton+
					'<button type="button" class="btn btn-danger" onclick="javascript:removeEntry('+wlid+', '+entry.id+');"><i class="fa fa-times"></i></button>'+
				'</div>'+
			'</div>');
	} else if (can_manage) { // fleetcomp not queue
		buttonRow = $('<div>'+
					'<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">'+
						'<button type="button" class="btn btn-success" onclick="javascript:invitePlayer('+entry.character.id+', '+wlid+', '+groupId+')"><i class="fa fa-plus"></i></button>'+
						'<button aria-expanded="true" type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-caret-down"></i> Fits</button>'+
						'<button type="button" class="btn btn-success" onclick="javascript:sendNotification('+entry.character.id+', '+wlid+')"><i class="fa fa-bell-o"></i></button>'+
						convoButton+
						'<button type="button" class="btn btn-danger" onclick="javascript:removePlayer('+entry.character.id+', '+groupId+');"><i class="fa fa-times"></i></button>'+
					'</div>'+
				'</div>');
	} else { // linemembers/only view fits
		var buttonHTML = '<div class="btn-group btn-group-mini" role="group" aria-label="Action Buttons">';
		if (entry.character.id === user_id) {
			buttonHTML += '<button type="button" class="btn btn-mini btn-warning" '+
			'onclick="javascript: removeOwnEntry(\''+wlid+'\', '+entry.character.id+', '+entry.id+');"><i class="fa fa-times"></i></button>';
		}
		if (entry.character.id === user_id || can_view_fits) {
			buttonHTML += '<button type="button" data-toggle="collapse" data-target="#fittings-'+entry.id+'" class="btn btn-primary"><i class="fa fa-caret-down"></i> Fits</button>';
		}
		buttonHTML +='</div>';
		buttonRow = $(buttonHTML);
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
function createEntryDOM(wlId, entry, groupID, isQueue) {
	var entryDOM = $('<li class="list-group-item" data-username="'+entry.character.name+'" id="entry-'+wlId+'-'+entry.id+'" data-count="'+entry.fittings.length+'"></li>');
	entryDOM.append(createHeaderDOM(wlId, entry, groupID, isQueue));
	var fittlistDOM = $('<ul aria-expanded="true" class="list-group list-group-flush collapse" id="fittings-'+entry.id+'"></ul>');
	entryDOM.append(fittlistDOM);
	for (var i=0; i<entry.fittings.length; i++) {
		fittlistDOM.append(createFitDOM(entry.fittings[i], wlId, entry.id, isQueue, entry.character.name, entry.character.id));
	}
	return entryDOM;
}

function getTagFromDomFit(fit) {
	return fit.attr('data-type');
}

function getTagsFromDomEntry(entry) {
	var tagContainer = $('div.tag-row', entry);
	var tagList = [];
	tagContainer.children().each(function(){
		tagList.push($(this).text());
	});
	return tagList;
}

function getTagsFromDomFitContainer(fitContainer) {
	var tagList = [];
	fitContainer.children().each(function(){
		tagList.push(getTagFromDomFit($(this)));
	});
	return tagList;
}

function removeTagFromDomEntry(entry, tagString) {
	var tagContainer = $('div.tag-row', entry);
	tagContainer.children().each(function(){
		var e = $(this);
		if (e.text() === tagString) {
			e.remove();
		}
	});
}

function addTagToDomEntry(entry, tagString) {
	var tagContainer = $('div.tag-row', entry);
	var tag = createTypeTag(tagString);
	tagContainer.append(tag);
}

function removeFitFromDom(wlId, entryId, fitId) {
	var targetFit = $('#fit-'+wlId+'-'+entryId+'-'+fitId);
	if (targetFit.length <= 0) {
		return 0;
	}
	targetFit.remove();
	// make sure that a tag gets removed if they are not needed anymore
	var entry = $('#entry-'+wlId+'-'+entryId);
	var tagList = getTagsFromDomEntry(entry);
	var fitTags = getTagsFromDomFitContainer($('#fittings-'+entryId));
	for(let tag of tagList) {
		if (!fitTags.includes(tag)) {
			removeTagFromDomEntry(entry, tag);
		}
	}
	return 1;
}

function addFitToDom(wlId, entryId, fit, isQueue, userId) {
    var entry = $('#entry-'+wlId+'-'+entryId);
	var fitContainer = $('#fittings-'+entryId);
	var username = entry.attr('data-username');
	
	var fitDom = createFitDOM(fit, wlId, entryId, isQueue, username, userId);
	fitContainer.appendChild(fitDom);
	// add new tags if needed
	var tagList = getTagsFromDomEntry(entry);
	
	var fitTags = getTagsFromDomFitContainer(fitContainer);
	for( let tag of fitTags) {
		if (!tagList.includes(tag)) {
			addTagToDomEntry(entry, tag);
		}
	}
	
}

/**
 * Creat html entity of a fit
 * @param fit fit object as received from the api
 * @param pass if it is the x-up list, so we can add approve button, defaults to false
 * @returns {HTMLElement} the fit's DOM
 */
function createFitDOM(fit, wlId, entryId, queue, username, userId) {
	queue = typeof queue !== 'undefined' ? queue : false;
	var isDummy = (fit.shipType === 1);
	var approveButton = "";
	if (can_manage && queue) {
		approveButton = ' <button type="button" class="btn btn-mini btn-success" data-type="fit-approve" data-id="'+fit.id+'" data-wlId="'+wlId+'" data-entryId="'+entryId+'"><i class="fa fa-thumbs-o-up"></i></button>';
	}
	var fitButtons = "";
	if (user_id === userId) {
		fitButtons += '<button type="button" class="btn btn-mini btn-danger" data-action="remove-own-fit" data-fit='+fit.id+' data-wlId='+wlId+' data-entryId='+entryId+'><i class="fa fa-times"></i> Fit</button>';
		if (queue) {
			fitButtons += '<button type="button" class="btn btn-mini btn-danger" data-action="update-fit" data-fit="'+fit.id+'" class="btn btn-warning">Update</button>';
		}
	}
	
	var fitdom = isDummy ? $($.parseHTML('<li class="list-group-item fitting" id="fit-'+wlId+"-"+entryId+"-"+fit.id+'" data-type="'+getTagFromJsonFit(fit)+'"></li>')) : $($.parseHTML('<li class="list-group-item fitting" id="fit-'+wlId+"-"+entryId+"-"+fit.id+'" data-type="'+getTagFromJsonFit(fit)+'"></li>'));
	var commentHTML = "";
	if (fit.comment !== null) {
		commentHTML = '<small>'+fit.comment+'</small>';
	}
	// lets check if it is the dummy fit
	
	var baseElement = isDummy ? $.parseHTML('<div class="booby-link" ></div>') : $.parseHTML('<div class="fit-link" data-title="'+username+'" data-dna="'+fit.shipType+':'+fit.modules+'" data-type="'+fit.wl_type+'"></div>');
	fitdom.append(
			$(baseElement)
				.append($($.parseHTML('<div class="wel-header-32"></div>'))
						.append($.parseHTML('<img class="img-32" src="https://imageserver.eveonline.com/Render/'+fit.shipType+'_32.png" alt="'+fit.shipName+'">'))
						.append($.parseHTML('<div class="wel-container-32"><div class="wel-text-row-32-2">'+fit.shipName+'</div><div class="wel-text-row-32-2">'+commentHTML+approveButton+fitButtons+'</div></div>'))
						)
			);
	return fitdom;
}

/**
 * Add a new entry to the given list
 * @param wlid id of the waitlist
 * @param entry the entry object as received from the api
 * @param groupId id of the group this waitlist belongs to
 * @param if this waitlist is the intial queue
 */
function addNewEntry(wlid, entry, groupID, isQueue) {

	var newEntryTime = new Date(Date.parse(entry.time));
	
	var entryDOM = createEntryDOM(wlid, entry, groupID, isQueue);
	var wlEntryContainer = $('#wl-fits-'+wlid);
	var entries = wlEntryContainer.children();

	var insertBefore = null;
	var insertBeforeTime = null;

	entries.each(function(idx, e){
		var el = $(e);
		var waitElement = $('.wait-time', el);
		var cTime = new Date(Date.now());
		var xupTime = new Date(Date.parse(waitElement.attr('data-time')));
		// the entry we are looking at happened after ours
		if (xupTime > newEntryTime) {
			
			// the entry that we saved is newer then the one we are look at atm
			// or we didn't save one yet
			// => save this one
			if (insertBeforeTime === null || insertBeforeTime > xupTime) {
				insertBefore = el;
				insertBeforeTime = xupTime;
			}
		}
	});

	if (insertBefore !== null) {
		insertBefore.before(entryDOM);
	} else {
		wlEntryContainer.append(entryDOM);
	}
	setWlEntryCount(wlid, getWlEntryCount(wlid)+1);
}

function removeEntryFromDom(wlid, entryId) {
	var targetEntry = $('#entry-'+wlid+'-'+entryId);
	if (targetEntry.length <= 0) {
		return 0;
	}
	targetEntry.remove();
	setWlEntryCount(wlid, getWlEntryCount(wlid)-1);
	return 1;
}

/**
 * Set the entry counter for a given waitlist
 * @param wlid id of the waitlist
 * @param count count of entries to set to
 */
function setWlEntryCount(wlid, count) {
	document.getElementById('wl-'+wlid).setAttribute("data-count", count);
	var countElement = document.getElementById('wl-count-'+wlid);
	if (countElement !== null) {
		countElement.textContent = count;
	}
}

/**
 * Get the count for a given waitlist
 * @param wlid id of the waitlist
 * @returns {Number} count of entries in the waitlist
 */
function getWlEntryCount(wlid) {
	return Number(document.getElementById('wl-'+wlid).getAttribute("data-count"));
}


// json update only related stuff down here

/**
 * Updates fits of entries
 * @param wlname name of the waitlist the entry belongs to
 * @param wlid id of the waitlist the entry belongs to
 * @param entry the entry object as received from the api
 * @returns {Number} number of new entry that where added (0 or 1)
 */
function updateWlEntry(wlid, entry, isQueue) {
	var jEntries = $('#entry-'+wlid+'-'+entry.id);
	if (jEntries.length > 0) {
		// update the wait time
		// ' <small class="wait-time">'+waitTimeMinutes+' min ago</small>
		var wtElement = $('.wait-time', jEntries[0]);
		var cTime = new Date(Date.now());
		var xupTime = new Date(Date.parse(entry.time));
		var waitTimeMinutes = Math.floor((cTime - xupTime)/60000);
		var newTimeText = waitTimeMinutes+" min ago";
		var oldTimeText = wtElement.text();
		if (oldTimeText !== newTimeText) {
			wtElement.text(newTimeText);
		}
		
		// update the missed invites
		if (entry.missedInvites > 0) {
			let invNumElement = $('.missed-invites-number', jEntries[0]);
			if (invNumElement.length > 0) {
				var oldNum = Number(invNumElement.text());
				if (oldNum !== entry.missedInvites) {
					invNumElement.text(entry.missedInvites);
				}
			} else {
				let invElement = $('.missed-invites', jEntries[0]);
				let counterElement = $.parseHTML("<div style='display: inline;' class='missed-invites-number'>"+entry.missedInvites+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="Missed Invites"></i>');
				invElement.append(counterElement);
			}
		} else {
			let invNumElement = $('.missed-invites-number', jEntries[0]);
			if (invNumElement.length > 0) {
				let invElement = $('.missed-invites', jEntries[0]);
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
			var is_existing = false;
			for (let i=0; i < entry.fittings.length; i++ ) {
				var fit = entry.fittings[i];
				if (fit.id === currentId) {
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
			jFittings.append(createFitDOM(entry.fittings[i], wlid, entry.id, isQueue, entry.character.username, entry.character.id));
		}
		
		// if we modified sth update the tags
		if (modified) {
			let tags = getTagsFromFits(fittings);
			let tagContainer = $('div.tag-row', jEntries);
			tagContainer.empty();
			for (let i = 0; i < tags.length; i++) {
				tagContainer.append(createTypeTag(tags[i]));
			}
		}
	}
}


/**
 * Remove a entries from a waitlist
 * @param wldata wl object as received from the api
 */
function cleanWL(wldata) {
	$('#wl-fits-'+wldata.id).empty();
}

/**
 * Remove missing entries from DOM
 * @param wldata waitlist data as received from api
 * @returns {Number} number of entries that where removed
 */
function deleteMissingEntries(wldata) {
	var removeCount = 0;
	var entries = $('li[id|="entry-'+wldata.id+'"]');
	var preLen = ("entry-"+wldata.id+"-").length;
	for (let i=0; i < entries.length; i++) {
		var id = $(entries[i]).attr("id");
		id = Number(id.slice(preLen));
		var is_existing = false;
		for (let n=0; n < wldata.entries.length; n++) {
			if (wldata.entries[n].id === id) {
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
	var preLen = ("entry-"+wldata.id+"-").length;
	var entries = $('li[id|="entry-'+wldata.id+'"]');
	var domEntryCount = entries.length;
	var addedCounter = 0;

	// we iterate over our entries, they are in the right order
	// if we do not match with the entry at the same position in the dom
	// there needs to be added the current entry there
	// if we do match, we need to check the fits there
	var inserAfterElement = null;
	for (let n=0; n < wldata.entries.length; n++) {
		var currentDOMIdx = n-addedCounter;
		if (currentDOMIdx < domEntryCount) {
			var currentDOM = $(entries[n-addedCounter]);
			var domId = Number(currentDOM.attr('id').slice(preLen));
			// if ids match == check for fits that need to be updated
			if (domId === wldata.entries[n].id) {
				inserAfterElement = currentDOM;
				updateWlEntry(wldata.id, wldata.entries[n], wldata.name === "queue" ? true : false);
			} else {
				// we need to add a new entry
				let entryDOM = createEntryDOM(wldata.id, wldata.entries[n], groupID, wldata.name === "queue");
				if (inserAfterElement === null) {
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
			let entryDOM = createEntryDOM(wldata.id, wldata.entries[n], groupID, wldata.name === "queue");
			if (inserAfterElement === null) {
				let wlEntryContainer = $('#wl-fits-'+wldata.id);
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
	var oldCount = getWlEntryCount(wldata.id);
	var newCount = oldCount + addedEntryCount - removedEntryCount;
	setWlEntryCount(wldata.id, newCount);
}

/**
 * Refresh entries of all waitlists with the data from the json API
 */
function refreshWl() {
	var wlid = getMetaData('wl-group-id');
	if (typeof wlid !== 'undefined') {
		$.getJSON(getMetaData('api-waitlists')+"?group="+wlid, function(data){
			for (var i=0; i < data.waitlists.length; i++) {
				updateWaitlist(data.waitlists[i], data.groupID);
			}
		});
	}
}

function updateWaitTimes() {
	$('li[id|="entry"').each(function(idx, e){
		var waitElement = $('.wait-time', e);
		var cTime = new Date(Date.now());
		var xupTime = new Date(Date.parse(waitElement.attr('data-time')));
		var waitTimeMinutes = Math.max(0, Math.floor((cTime - xupTime)/60000));
		waitElement.text(waitTimeMinutes+" min ago");
	});
}

function updateMissedInvite(userId) {
	// first get the missed invites elements
	var missedElements = $('.missed-invites[data-userId="'+userId+'"]');
	// go through them and check if there is allready a missed invites dom
	missedElements.each(function(idx, e){
		let el = $(e);
		let count = 0;
		if (el.children().length > 0) { // we have the DOM
			// read current count
			let countEl = $('.missed-invites-number', el);
			count = Number(countEl.text());
			// set the new count
			countEl.text(count+1);
		} else {
			// he didn't miss invites yet, no DOM
			el.append($("<div style='display: inline;' class='missed-invites-number'>"+(count+1)+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="Missed Invites"></i>'))
		}
	});
}