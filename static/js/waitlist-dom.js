'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.listdom = (function(){
	var getMetaData = waitlist.base.getMetaData;
	var settings = {
			anno_icon: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAAAAABWESUoAAAAWHRFWHRDb3B5cmlnaHQAQ0MwIFB1YmxpYyBEb21haW4gRGVkaWNhdGlvbiBodHRwOi8vY3JlYXRpdmVjb21tb25zLm9yZy9wdWJsaWNkb21haW4vemVyby8xLjAvxuO9+QAAAXNJREFUOMuFkz8oxGEcxr+PuHAOOX/u8qcMVgxMIgNdFsrAcpEUxXCFhGzEYqGb5MqgM0hKKQYpd4qSUmIQSko5zoI7/+6x+N37o/N6pvf5PJ/lHb5ClY+rlZbUtFq/N2SCop4nVdvPM87sofBGyX4CIbZWgC1yaIC8sNk2fwqRw4WeYsDywAt72hFZh6Qm33lceKlNAQCghgzseNZJFwAgt6Z9nRRyE9/pID9nG6NktUEynijkuFF7SbZlfZKFBsEehaw3WjPJIpwxmhwX/BS+phstL0ZasMrD+I5pCoOqHjMCeDmvSB+Fu6r28w6YZKcirnfhsKrW0CUw+mZXxP4obFUVnnNgeNEEMu+FxaZuWQa6Ss3gTkIwJx9I+gHWJABt5sSnF0ZkTC+4xa0XGqReL5RLmV5wSKZeSBa7XoAM6nerRCq1QoXwNEezO4NCHjj+3JtuKCSvq//44pJxOFFbor07HL+s2NREgtz+Pt7E+Vf4AmxYMy7fksTaAAAAAElFTkSuQmCC"
		};
	
	/**
	 * Create a DOM for a ship type tag
	 * 
	 * @param tag: B = Basi, S = Scimi, DPS = Short Range Damage, SNI = Sniper,
	 *            LOGI == Scruffy Logi
	 */
	function createTypeTag(name) {
		var type = "default";
		switch (name) {
		case "B":
			type = "success";
			name = $.i18n('wl-tag-basilisk');
			break;
		case "S":
			type = "success";
			name = $.i18n('wl-tag-scimitar');
			break;
		case "LOGI":
			type = "success";
			name = $.i18n('wl-tag-logi');
			break;
		case "DPS":
			type = "danger";
			name = $.i18n('wl-tag-dps')
			break;
		case "SNI":
			type = "warning";
			name = $.i18n('wl-tag-sniper')
			break;
		default:
			type = "secondary";
		}
		
		
		return $.parseHTML(`<span class="badge badge-pill badge-${type}">${name}</span>`);
	}
	
	/**
	 * Get which tags these fits create
	 * 
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
		for (let fit of fits) {
			addTag(getTagFromJsonFit(fit));
		}
		// make a list out of the object properties
		var tagList = [];
		for (let tag in tags) {
			tagList.push(tag);
		}
		return tagList;
	}
	
	/**
	 * returns back what kind of tag this fit is
	 * 
	 * @param jsonFit a fit in the json format as returned by the api
	 */
	function getTagFromJsonFit(jsonFit) {
		switch (jsonFit.wl_type) {
		case "logi":
			// since we want to have basi/scimi specificly need to check
			// shipType here
			if (jsonFit.shipType === 11985) {
				return "B";
			} else if (jsonFit.shipType === 11978) {
				return "S";
			} else if (jsonFit.shipType === 1) {
				// it is scruffy
				return "LOGI";
			} else {
			  return "LOGI"
			}
			break;
		case "sniper":
			return "SNI";
		case "dps":
			return "DPS";
		case "other":
			return "OTHER";
		default:
			return jsonFit.wl_type;
		}
	}
	
	/**
	 * Create the html entity for the entry's header
	 * 
	 * @param wlname name of the waitlist the entry belongs to
	 * @parm wlid id of the waitlist
	 * @param entry the waitlist entry as received from the api
	 * @returns {HTMLElement} DOM fo the entries header
	 */
	function createHeaderDOM(wlid, entry, groupId, isQueue) {
		var newBroTag = "";
		
		// if the current user can view fits and or it is this character and
		// this entry is a rookie
		if ((settings.can_view_fits || entry.character.id === settings.user_id) && entry.character.newbro) {
			newBroTag = ' <span class="badge badge-pill badge-info">'+$.i18n('wl-new')+'</span>';
		}
		var cTime = new Date(Date.now());
		var xupTime = new Date(Date.parse(entry.time));
		var waitTimeMinutes = Math.max(0, Math.floor((cTime - xupTime)/60000));
		var header = $('<div class="w-100"></div>');
		var oldInvites = "";
		// we can view fits or this is our entry and the entry is not in a queue
		// display missed invites if there are any, but at least create the
		// element for it
		if ((settings.can_view_fits || entry.character.id === settings.user_id) && !isQueue) {
			if (entry.missedInvites > 0) {
				oldInvites =
				`<div class="missed-invites d-inline" data-userId="${entry.character.id}">
					<div class="missed-invites-number d-inline">${entry.missedInvites}</div>
					<i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="${$.i18n('wl-missed-invites')}"></i>
				</div>`;
			} else {
				oldInvites = `<div class="missed-invites d-inline" data-userId="${entry.character.id}"></div>`;
			}
		}
		
		// make managers call the CREST API others should open in quie's tool
		var charHref = settings.can_manage ? '#' : `char:${entry.character.id}`;
		var charInserts = settings.can_manage ? ` data-action="openCharInfo" data-characterid="${entry.character.id}"` : '';
		
		
		var imgHTML;
		if (entry.character.id === null) {
			imgHTML = `<img class="img-32" src="${settings.anno_icon}">`;
			charHref = '#'; // change the href to not call quies script because
							// we have no id
		} else {
			imgHTML = `<img class="img-32" src="${eve_image("Character/"+entry.character.id+"_32", "jpg")}">`;
		}

		let wardecHTML = '';
		if (settings.can_view_fits || entry.character.id === settings.user_id) {
		  wardecHTML = `<img height="15px" width="15px" class="float-right mt-1 mr-1" src="https://wars.feralfedo.com/characters/${entry.character.id}/img/"
		   data-toggle="tooltip" data-placement="top" title="${$.i18n('wl-wardec-desc')}">`;
		}
		
		var charRow = $(`<a href="${charHref}"${charInserts}>
							<div class="wel-header-32">
								${imgHTML}
								${wardecHTML}
								<div class="wel-container-32">
									<div class="wel-text-row-32-2">${entry.character.name}${oldInvites}${newBroTag} <small class="wait-time" data-time="${entry.time}">${waitTimeMinutes} min ago</small></div>
									<div class="wel-text-row-32-2 tag-row"></div>
								</div>
							</div>
						</a>`);
		if (settings.can_view_fits || entry.character.id === settings.user_id) {
			var tags = getTagsFromFits(entry.fittings);
			var tagContainer = $('div.tag-row', charRow);
			for (let tag of tags) {
				tagContainer.append(createTypeTag(tag));
			}
		}
		var buttonHTML = "";
		const dropdownButton = `<button type="button" data-toggle="collapse" data-target="#fittings-${entry.id}-col" class="btn btn-primary"><span class="fitdd">${$.i18n('wl-fits')}</span></button>`;
		if (settings.can_manage) { // fleet comp
			var button1, button4, convoButton = "";
			const notificationButton = `<button type="button" class="btn btn-success" data-action="sendNotification" data-characterid="${entry.character.id}" data-wlId="${wlid}"><i class="fa fa-bell-o"></i></button>`;
			if (isQueue) { // if in x'ups
				button1 = `<button type="button" class="btn btn-success" data-action="approveEntry" data-wlId="${wlid}" data-entryId="${entry.id}"><i class="fa fa-thumbs-o-up"></i></button>`;
				button4 = `<button type="button" class="btn btn-danger" data-action="dismissEntry" data-wlId="${wlid}" data-entryId="${entry.id}"><i class="fa fa-times"></i></button>`;
			} else { // else in wl's
				button1 = `<button type="button" class="btn btn-success" data-action="invitePlayer" data-characterid="${entry.character.id}" data-wlId="${wlid}" data-groupId="${groupId}"><i class="fa fa-plus"></i></button>`;
				button4 = `<button type="button" class="btn btn-danger" data-action="removePlayer" data-characterid="${entry.character.id}" data-groupId="${groupId}"><i class="fa fa-times"></i></button>`;
			}
			buttonHTML = button1 + dropdownButton + convoButton + notificationButton + button4;
		} else { // line members/view fits
			if (entry.character.id === settings.user_id) {
				buttonHTML = `<button type="button" class="btn btn-warning" data-action="removeOwnEntry" data-characterid="${entry.character.id}" data-wlId="${wlid}" data-entryId="${entry.id}"><i class="fa fa-times"></i></button>`;
			}
			if (entry.character.id === settings.user_id || settings.can_view_fits) {
				buttonHTML += dropdownButton;
			}
		}

		
		header.append(charRow);
		if (buttonHTML !== "") {
			var buttonRow = $('<div class="btn-group btn-group-mini" role="group">'+buttonHTML+'</div>');
			header.append(buttonRow);
		}
		return header;
	}
	
	/**
	 * Create the html entity of the entry
	 * 
	 * @param wlname name of the waitlist the entry belongs to
	 * @param wlid id of the waitlist
	 * @param entry the entry object as received from the api
	 * @returns {HTMLElement} DOM of an entry
	 */
	function createEntryDOM(wlId, entry, groupID, isQueue) {
		let entryDOM = $(`<li class="list-group-item" data-username="${entry.character.name}" id="entry-${wlId}-${entry.id}"></li>`);
		let headerDOM = createHeaderDOM(wlId, entry, groupID, isQueue);
		entryDOM.append(headerDOM);
		let collapsLayer = $($.parseHTML(`<div id="fittings-${entry.id}-col" class="collapse"></div>`));
		let fittlistDOM = $(`<ul aria-expanded="true" class="list-group list-group-flush" id="fittings-${entry.id}"></ul>`);
		collapsLayer.append(fittlistDOM);
		headerDOM.append(collapsLayer);
		for (let fit of entry.fittings) {
			fittlistDOM.append(createFitDOM(fit, wlId, entry.id, isQueue, entry.character.name, entry.character.id));
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
		fitContainer.append(fitDom);
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
	 * Take a string and return the same string
	 * unless the string is "#System"
	 * then return "Booby"(the bird)
	 * @param old_name inventory type name
	 * @returns old_name unless it is "#System" then it is replaced by "Booby"
	 */
	function filterShipName(old_name) {
		if (old_name === "#System") {
			return "Booby";
		}
		return old_name;
	}
	
	/**
	 * Creat html entity of a fit
	 * 
	 * @param fit fit object as received from the api
	 * @param wlId id of the waitlist this fit is in
	 * @param entryId id of the entry this fit belongs to
	 * @param queue if the entry is in the initial queue or one of the other
	 *            lists
	 * @param username character name the entry belongs to
	 * @param userId character id the entry belongs to
	 * @returns {HTMLElement} the fit's DOM
	 */
	function createFitDOM(fit, wlId, entryId, queue, username, userId) {
		queue = typeof queue !== 'undefined' ? queue : false;
		var isDummy = fit.shipType === 0;
		var approveButton = "", fitButtons = "",commentHTML = "";
		// if user can manage fleet and if on x'ups
		if (settings.can_manage && queue) {
			// approve fit button
			approveButton = '<button type="button" class="btn btn-mini btn-success" data-action="approveFit" data-id="'+fit.id+'" data-wlId="'+wlId+'" data-entryId="'+entryId+'"><i class="fa fa-thumbs-o-up"></i></button>';
		}
		// if user is looking at their own entry
		if (settings.user_id === userId) {
			// remove own fit
			fitButtons = '<button type="button" class="btn btn-mini btn-danger" data-action="remove-own-fit" data-fit='+fit.id+' data-wlId='+wlId+' data-entryId='+entryId+'><i class="fa fa-times"></i> ' + $.i18n('wl-fit') + '</button>';
			if (queue) {
				// update fit (only displayed if in x'up)
				fitButtons += '<button type="button" class="btn btn-mini btn-danger" data-action="update-fit" data-fit="'+fit.id+'" class="btn btn-warning">' + $.i18n("wl-update") + '</button>';
			}
		}
		// button group

		let buttonRowHTML = '';
		if ((approveButton+fitButtons) !== '') {
			buttonRowHTML = '<div class="btn-group btn-group-mini">' + approveButton + fitButtons + '</div>';
		}

		// if fit has a comment add it
		if (fit.comment !== null) {
			commentHTML = `<div id="fit-${wlId}-${entryId}-${fit.id}-comment"><small>${fit.comment}</small></div>`;
		}
		// text html with ship name and comment
		var textHTML = '<div class="wel-text-row-32-2">'+filterShipName(fit.shipName)+commentHTML+'</div>';

		var fitDOM = $('<li class="list-group-item" id="fit-'+wlId+"-"+entryId+"-"+fit.id+'" data-type="'+getTagFromJsonFit(fit)+'" role="button"></li>');

		// lets extract caldari bs lvl from comments
		let skillsData = '';
		let caldariBsLvelRex = /<b>Cal BS: ([012345])<\/b>/;
		let bsResult = caldariBsLvelRex.exec(fit.comment);
		if (bsResult !== null) {
			skillsData = `3338:${bsResult[1]}`;
		}
		// lets check if it is the dummy fit, and create the html accordingly
		var baseHTML = isDummy ? '<div class="booby-link w-100" ></div>' : `<div class="fit-link w-100" data-title="${username}" data-skills="${skillsData}" data-dna="${fit.shipType}:${fit.modules}" data-type="${fit.wl_type}"></div>`;
		let fitContainer = $('<div class="wel-header-32"></div>');
		fitContainer.append('<img class="img-32" src="'+eve_image('Render/'+fit.shipType+'_32', 'png')+'">')
		if ((textHTML+buttonRowHTML) !== "") {
			fitContainer.append('<div class="wel-container-32">'+textHTML+buttonRowHTML+'</div>');
		}

		fitDOM.append($(baseHTML)
					.append(fitContainer)
					);
		return fitDOM;
	}
	
	/**
	 * Add a new entry to the given list
	 * 
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
			var xupTime = new Date(Date.parse(waitElement.attr('data-time')));
			// the entry we are looking at happened after ours
			if (xupTime > newEntryTime) {
				
				// the entry that we saved is newer then the one we are look at
				// atm
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
		updateWlEntryTagCount(wlid);
	}
	
	function removeEntryFromDom(wlid, entryId) {
		var targetEntry = $('#entry-'+wlid+'-'+entryId);
		if (targetEntry.length <= 0) {
			return 0;
		}
		targetEntry.remove();
		updateWlEntryTagCount(wlid);
		return 1;
	}

	/**
	 * Update the entry tag counter for a given waitlist
	 * 
	 * @param wlid id of the waitlist
	 */
	function updateWlEntryTagCount(wlid) {
		const
		countElement = document.getElementById("wl-count-" + wlid),
		wlEntries = document.getElementById("wl-fits-" + wlid);
		countElement.textContent = wlEntries.children.length;
	}

	// json update only related stuff down here

	/**
	 * Updates fits of entries
	 * 
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
					let counterElement = $.parseHTML("<div class='missed-invites-number d-inline'>"+entry.missedInvites+'</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="' + $.i18n('wl-missed-invites') + '"></i>');
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
			// backup of original fits, we gonna need them later if sth was
			// modified
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
						entry.fittings.splice(i, 1); // this fit is already
														// there we don't need
														// it
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
			for (let fit of entry.fittings) {
				jFittings.append(createFitDOM(fit, wlid, entry.id, isQueue, entry.character.username, entry.character.id));
			}
			
			// if we modified sth update the tags
			if (modified) {
				let tags = getTagsFromFits(fittings);
				let tagContainer = $('div.tag-row', jEntries);
				tagContainer.empty();
				for (let tag of tags) {
					tagContainer.append(createTypeTag(tag));
				}
				$('[data-toggle="tooltip"]').tooltip();
			}
		}
	}


	/**
	 * Remove missing entries from DOM
	 * 
	 * @param wldata waitlist data as received from api
	 * @returns {Number} number of entries that where removed
	 */
	function deleteMissingEntries(wldata) {
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
			}
		}
	}

	// before using this all none existing entries need to be removed from the
	// DOM
	/**
	 * Adds entries that do not exist in the DOM at their correct positions
	 * 
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
	}

	/**
	 * Update a waitlist
	 * 
	 * @param wldata waitlist object as received from the api
	 */
	function updateWaitlist(wldata, groupID) {
		deleteMissingEntries(wldata);
		addNewEntries(wldata, groupID);
		updateWlEntryTagCount(wldata.id);
	}

	/**
	 * Refresh entries of all waitlists with the data from the json API
	 */
	function refreshWl() {
		var wlid = getMetaData('wl-group-id');
		if (typeof wlid !== 'undefined') {
			$.getJSON(getMetaData('api-waitlists-groups').replace('-1', wlid), function(data) {
				setStatusDom(data);
			});
			$.getJSON(getMetaData('api-waitlists')+"?group="+wlid, function(data){
				for (let waitlist of data.waitlists) {
					updateWaitlist(waitlist, data.groupID);
				}
			});
		}
	}

	function updateWaitTimes() {
		$('li[id|="entry"]').each(function(idx, e){
			var waitElement = $('.wait-time', e);
			var cTime = new Date(Date.now());
			var xupTime = new Date(Date.parse(waitElement.attr('data-time')));
			var waitTimeMinutes = Math.max(0, Math.floor((cTime - xupTime)/60000));
			waitElement.text($.i18n('wl-min-ago', waitTimeMinutes));
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
				el.append($(`<div class="missed-invites-number d-inline">${count+1}</div> <i class="fa fa-bed" aria-hidden="true" data-toggle="tooltip" data-placement="top" title="${$.i18n('wl-missed-invites')}"></i>`));
				
			}
		});
	}
	
	// end of json update related stuff
	
	// status update start
	/**
	 * @param groupStatus { groupID=INT, status=STR, influence=BOOL,
	 *            constellation={constellationID=INT,constellationName=STR},
	 *            solarSystem={systemID=INT,systemName=STR},
	 *            station={stationID=INT, stationName=STR},
	 *            fcs=[{id=INT,name=STR,newbro=BOOL}...],
	 *            managers=[{id=INT,name=STR,newbro=BOOL}...],
	 *            fleets=[{groupID=INT, comp={id=INT,name=STR,newbro=BOOL}}...] }
	 */
	
	function setStatusDom(groupStatus) {
		// get the TD that contains all the FCs
		var fcTD = $(`#grp-${groupStatus.groupID}-fcs`);
		// remove all FC entries
		fcTD.empty();
		for(let fc of groupStatus.fcs) {
			// create the fc link
			let fcA = $(`<a href="char:${fc.id}" class="mr-3">${fc.name}</a>`);
			fcTD.append(fcA);
		}

		// set the constellation
		var constTD = $(`#grp-${groupStatus.groupID}-const`);
		constTD.empty();
		var constA;
		if (groupStatus.constellation) {
			constA = $(`<a href="#">${groupStatus.constellation.constellationName}</a>`);
		} else {
			constA = $('<a href="#">Not Set</a>');
		}
		constTD.append(constA);
		
		// set the dockup
		var dockupTD = $(`#grp-${groupStatus.groupID}-dockup`);
		dockupTD.empty();
		var dockupA;
		if (groupStatus.station) {
			dockupA = $(`<a href="#">${groupStatus.station.stationName}</a>`);
		} else {
			dockupA = $(`<a href="#">Not Set</a>`);
		}
		dockupTD.append(dockupA);
		

		var systemTD = $(`#grp-${groupStatus.groupID}-system`);
		systemTD.empty();
		var systemA;
		if (groupStatus.solarSystem) {
			systemA = $(`<a href="#">${groupStatus.solarSystem.solarSystemName}</a>`);
		} else {
			systemA = $(`<a href="#">Not Set</a>`);
		}
		systemTD.append(systemA);
		
		// update managers
		var managerTD = $(`#grp-${groupStatus.groupID}-manager`);
		managerTD.empty();
		// we have connected crest fleets, use the managers from those
		for(let manager of groupStatus.managers) {
			var managerA = $(`<a href="char:${manager.id}" class="mr-3">${manager.name}</a>`);
			managerTD.append(managerA);
		}
		
		// set the status
		var statusDiv = $(`#grp-${groupStatus.groupID}-status`);
		statusDiv.empty();
		if (groupStatus.enabled) {
			if (groupStatus.status) {
				// lets see if an translation exists
				let translation_key = `wl-liststatus-${groupStatus.status}`;
				let translated_status = $.i18n(translation_key);
				// no translation exists
				if (translated_status === translation_key) {
					translated_status = groupStatus.status;
				}
				
				statusDiv.text(translated_status+' ');
				if (groupStatus.influence) {
					let influenceLink = getMetaData('influence-link');
					statusDiv.append($(`<a id='influence-link' class=".no-collapse" href="${influenceLink}" target="_blank">${$.i18n('wl-fit-influence')}</a>`));
					$('#influence-link').on('click', function (e) {
						e.stopPropagation();
					});
				}
			}
		} else {
			statusDiv.html($.i18n('wl-list-closed'));
			$('#status-link').on('click', function (e) {
				e.stopPropagation();
			});
		}
	}
	
	function clearWaitlists() {
		var fitLists = $('ol[id|="wl-fits"]');
		fitLists.empty();
		fitLists.each(function(idx, el){
			let wlId = Number($(el).attr('id').replace('wl-fits-', ''));
			updateWlEntryTagCount(wlId);
		});
	}
	
	// status update end
	
	function init() {
		settings.can_view_fits = getMetaData('can-view-fits') === "True";
		settings.can_manage = getMetaData('can-fleetcomp') === "True";
		settings.user_id = Number(getMetaData('user-id'));
		if (window.EventSource) {
			setInterval(updateWaitTimes, 30000);
		}
	}

	
	$(document).ready(init);
	return {
		loadWaitlist: refreshWl,
		addFitToDom: addFitToDom,
		addNewEntry: addNewEntry,
		removeFitFromDom: removeFitFromDom,
		removeEntryFromDom: removeEntryFromDom,
		updateMissedInvite: updateMissedInvite,
		setStatusDom: setStatusDom,
		clearWaitlists: clearWaitlists
	};
})();
