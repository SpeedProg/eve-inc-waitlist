'use strict';

if (!waitlist) {
	var waitlist = {};
}

/**
 * wrapper for eve igb fuctions
 */
waitlist.IGBW = (function() {

	var urls = {
		openwindow: waitlist.base.getMetaData('api-igui-openwindow-ownerdetails'),
		newmail: waitlist.base.getMetaData('api-igui-openwindow-newmail'),
		esi_mail_send: waitlist.base.getMetaData('api-esi-mail-send'),
		esi_mail_auth: waitlist.base.getMetaData('api-esi-mail-auth')
	};

	/**
	 * Opens information window for the given item, oog it opens chruker.dk if only typeID is given
	 * @param typeID id for the type of the item id can be corporationID, allianceID, factionID, characterID, a celestial ID like regionID or solarSystemID 
	 */
	function showInfo(typeID, itemID) {
		if (typeof itemID === "undefined") {
			window.open("http://games.chruker.dk/eve_online/item.php?type_id="+typeID, "_blank");
		} else {
			$.post({
				'url': urls.openwindow,
				'data': {
					'characterID': itemID,
					'_csrf_token': waitlist.base.getMetaData('csrf-token')
				},
				'error': function(data) {
					var message = data.statusText;
					if (typeof data.message !== 'undefined') {
							message += ": " + data.message;
					}
					waitlist.base.displayMessage(message, "danger");
				}
			});
		}
	}

	/**
	 * Opens a mailwindow either igbapi or crest
	 * with the given topic, mail as body and charId as recipiant
	 * @param recipients = [{"recipient_id": ID, "recipient_type": "alliance|character|corporation|mailing_list"}]
	 * @param subject Mails Subject
	 * @param body Mails Body
	 */
	function sendMail(recipents, subject, body) {
		/*
		* mailRecipients => JSON String recipients=[{"recipient_id": ID, "recipient_type": "alliance|character|corporation|mailing_list"}]
		* mailBody => String
		* mailSubject => String
		 */
		$.post({
			'url': urls.esi_mail_send,
			'data': {
				'_csrf_token': waitlist.base.getMetaData('csrf-token'),
				'mailRecipients': JSON.stringify(recipents),
				'mailBody': body,
				'mailSubject': subject
			},
			'error': function(data) {
				var message = data.statusText;
				if (data.status == 412) {
					window.location = urls.esi_mail_auth;
				}
				if (typeof data.message !== 'undefined') {
						message += ": " + data.message;
				}
				waitlist.base.displayMessage(message, "danger");
			}
		});
	}

	return {
		sendMail: sendMail,
		showInfo: showInfo
	};
}());