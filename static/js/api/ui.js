'use strict';

if (!waitlist) {
	var waitlist = {};
	waitlist.esi = {};
} else if (!waitlist.esi) {
    waitlist.esi = {};
}

/**
 * api-esi-ui related calls
 */
waitlist.esi.ui = (function() {

    var urls = {
		esi_ui_newmail: waitlist.base.getMetaData('api-esi-ui-newmail'),
        esi_ui_auth: waitlist.base.getMetaData('api-esi-ui-auth')
	};

	/**
	 * Opens a mailwindow either igbapi or crest
	 * with the given topic, mail as body and charId as recipiant
	 * @param recipients = [{"recipient_id": ID, "recipient_type": "alliance|character|corporation|mailing_list"}]
	 * @param subject Mails Subject
	 * @param body Mails Body
	 */
    function open_newmail(receipients, subject, body) {
		/*
		* mailRecipients => JSON String recipients=[{"recipient_id": ID, "recipient_type": "alliance|character|corporation|mailing_list"}]
		* mailBody => String
		* mailSubject => String
		 */
		$.post({
			'url': urls.esi_ui_newmail,
			'data': {
				'_csrf_token': waitlist.base.getMetaData('csrf-token'),
				'mailRecipients': JSON.stringify(receipients),
				'mailBody': body,
				'mailSubject': subject
			},
			'error': function(data) {
				var message = data.statusText;
				if (data.status === 412) {
					window.location = urls.esi_ui_auth;
				}
				if (typeof data.message !== 'undefined') {
						message += ": " + data.message;
				}
				waitlist.base.displayMessage(message, "danger");
			}
		});
    }

    return {
		newmail: open_newmail,
	};
})();
