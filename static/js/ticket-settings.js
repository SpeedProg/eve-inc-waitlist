'use strict';


if (!waitlist) {
	var waitlist = {};
}

waitlist.ticketsettings = (function (){
	
	var sendMail = waitlist.IGBW.sendMail;
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;
	
	function getTicketElement(ticketId) {
		var el = {
				id: ticketId,
				jqE: $('#fb-'+ticketId)
		};
		el.getTitle = function(){
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
		var title = ticketElement.getTitle();
		var message = ticketElement.getMessage();
		var charID = ticketElement.getCharacterId();
		var charName = ticketElement.getCharacterName();
		sendMail(charID, 
				"Answer to your Waitlist Feedback",
				`Hello ${charName},\nWe read your ticket:\n<font size="10" color="#ffffcc00">${$("<div>").text(title).html()}\n\n${$("<div>").text(message).html()}</font>\n\nregards,\n`
				);
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
				if (typeof data.message !== 'undefined') {
						message += ": " + data.message;
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
		$('#ticket-table-body').on('click', '[data-action="sendTicketMail"]', sendMailClickedHandler);
		$('#ticket-table-body').on('click', '[data-action="changeTicketStatus"]', changeTicketStatusClickedHandler);
	}
	
	
    $(document).ready(init);
	return {};
})();

