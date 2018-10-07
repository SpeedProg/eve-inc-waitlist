'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.ticketsettings = (function() {

	var sendMail = waitlist.esi.ui.newmail;
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;

	function getTicketElement(ticketId) {
		var el = {
			id: ticketId,
			jqE: $('#fb-' + ticketId)
		};
		el.getTitle = function() {
			return $(":nth-child(4)", this.jqE).text();
		};

		el.getMessage = function() {
			return $(":nth-child(5)", this.jqE).text();
		};

		el.getCharacterId = function() {
			return this.jqE.attr('data-characterid');
		};
		el.getCharacterName = function() {
			return $(":nth-child(3)", this.jqE).text();
		};
		return el;
	}

	function sendTicketMail(ticketId) {
		var ticketElement = getTicketElement(ticketId);
		let title = ticketElement.getTitle();
		var message = ticketElement.getMessage();
		var charID = ticketElement.getCharacterId();
		var charName = ticketElement.getCharacterName();
		title = $("<div>").text(title).html();
		message = $("<div>").text(message).html();
		openMailToCharacter(
			charID,
			$.i18n('wl-fbmail-topic'),
			$.i18n('wl-fbmail-message',	charName, title, message)
		);
	}

	function openMailToCharacter(charId, subject, body) {
		// [{"recipient_id": ID, "recipient_type":
		// "alliance|character|corporation|mailing_list"}]
		sendMail([
			{
				"recipient_id": charId,
				"recipient_type": "character"
			}
		], subject, body);
	}

	function changeTicketStatus(ticketID, ticketStatus, successFunc) {
		$.post({
			'url': '/feedback/settings',
			'data': {
				'_csrf_token': getMetaData('csrf-token'),
				'ticketID': ticketID,
				'ticketStatus': ticketStatus
			},
			'error': function(data) {
				var message = data.statusText;
				if (typeof data.responseText !== 'undefined') {
					message += ": " + data.responseText;
				}
				displayMessage(message, "danger");
			},
			'success': successFunc
		});
	}

	function sendMailClickedHandler(event) {
		var target = $(event.currentTarget);
		var ticketId = target.attr('data-ticketId');
		sendTicketMail(ticketId);
	}

	function changeTicketStatusClickedHandler(event) {
		var target = $(event.currentTarget);
		var ticketId = target.attr('data-ticketId');
		var newStatus = target.attr('data-newStatus');
		changeTicketStatus(ticketId, newStatus, function() {
			target.parent().parent().remove();
		});
	}

	function init() {
		$('#ticket-table-body').on('click', '[data-action="sendTicketMail"]',
			sendMailClickedHandler);
		$('#ticket-table-body').on('click',
			'[data-action="changeTicketStatus"]',
			changeTicketStatusClickedHandler);
	}

	$(document).ready(init);
	return {};
})();
