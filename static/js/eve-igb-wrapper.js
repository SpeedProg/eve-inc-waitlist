'use strict';
/**
 * wrapper for eve igb fuctions
 */

var IGBW = (function() {
	var getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	}

	var lib = {
			isigb: (typeof CCPEVE != "undefined"),
			urls: {
				openwindow: getMetaData('api-igui-openwindow-ownerdetails'),
				newmail: getMetaData('api-igui-openwindow-newmail')
			}
	};
	/**
	 * Opens information window for the given item, oog it opens chruker.dk if only typeID is given
	 * @param typeID id for the type of the item id can be corporationID, allianceID, factionID, characterID, a celestial ID like regionID or solarSystemID 
	 */
	lib.showInfo = function(typeID, itemID) {
		if (typeof itemID == "undefined") {
			if (this.isigb) {
				CCPEVE.showInfo(typeID);
			} else {
				window.open("http://games.chruker.dk/eve_online/item.php?type_id="+typeID, "_blank");
			}
		} else {
			if (this.isigb) {
				CCPEVE.showInfo(typeID, itemID);
			} else {
				$.post({
					'url': lib.urls.openwindow,
					'data': {
						'characterID': itemID,
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
					}
				});
			}
		}
	}
	/**
	 * Starts converstation with a character, oog shows an alert that this is not available
	 * @param charID id of the character that to start the conversation with
	 */
	lib.startConversation = function(charID) {
		if (this.isigb) {
			CCPEVE.startConversation(charID);
		} else {
			alter("This only works in ingame browser");
		}
	}
	
	/**
	 * Opens a dna fit in a fittng window in game or o.smonium.org out of game
	 * @param dna ingame dna string of a fit
	 */
	lib.showFitting = function(dna) {
		if (this.isigb) {
			CCPEVE.showFitting(dna);
		}/* else {
			window.open("https://o.smium.org/loadout/dna/"+dna, "_blank");
		}*/
	}
	
	/**
	 * Opens a mailwindow either igbapi or crest
	 * with the given topic, mail as body and charId as recipiant
	 * @param charId Character Id of the recipiant
	 * @param subject Mails Subject
	 * @param body Mails Body
	 */
	lib.sendMail = function(charId, subject, body) {
		if (this.isigb) {
			CCPEVE.sendMail(charId, subject, body);
		} else {
			$.post({
				'url': lib.urls.newmail,
				'data': {
					'_csrf_token': getMetaData('csrf-token'),
					'mailRecipients': charId,
					'mailBody': body,
					'mailSubject': subject
				},
				'error': function(data) {
					var message = data.statusText
					if (typeof data.message != 'undefined') {
							message += ": " + data.message;
					}
					displayMessage(message, "danger");
				},
				'success': function(data){
				}
			});
		}
	}
	
	return lib;
}());