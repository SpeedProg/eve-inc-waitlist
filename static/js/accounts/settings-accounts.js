'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.accounts = (function() {
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;
	
	var sendMail = waitlist.IGBW.sendMail;

	function disableAccount(accountId, onsuccess){
		var settings = {
				async: true,
				dataType: "text",
				error: function() {
					displayMessage("error", "Disabling Account failed!");
				},
				method: "POST",
				data: {
					id: accountId,
					disabled: true
				},
				success: onsuccess,
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				}
		};
		$.ajax(getMetaData('api-account-disable'), settings);
	}

	function enableAccount(accountId, onsuccess){
		var settings = {
				async: true,
				dataType: "text",
				error: function() {
					displayMessage("error", "Enabling Account failed!");
				},
				method: "POST",
				data: {
					id: accountId,
					disabled: false
				},
				success: onsuccess,
				headers: {
					'X-CSRFToken': getMetaData('csrf-token')
				}
		};
		$.ajax(getMetaData('api-account-disable'), settings);
	}

	function enableAccountHandler(event) {
		var source = $(event.currentTarget);
		var id = Number(source.data('id'));
		enableAccount(id, function() {
			var row_id = "#account-"+id;
			var row = $(row_id);
			row.removeClass("table-warning");
			source.attr("data-type", "acc-disable");
			source.text("Disable");
		});
	}
	
	function disableAccountHandler(event) {
		var source = $(event.currentTarget);
		var id = Number(source.data('id'));
		disableAccount(id, function() {
			var row_id = "#account-"+id;
			var row = $(row_id);
			row.addClass("table-warning");
			source.attr("data-type", "acc-enable");
			source.text("Enable");
		});
	}
	
	function editAccountHandler(event) {
		var target = $(event.currentTarget);
		var accId = target.attr('data-accId');
		editAccount(accId);
	}
	
	function sendAuthMailHandler(event) {
		var target = $(event.currentTarget);
		var charId = Number(target.attr('data-characterid'));
		var token = target.attr('data-token');
		var senderUsername = target.attr('data-username');
		var targetUsername = target.attr('data-accusername');
		var targetUserType = target.attr('data-userType');
		sendAuthMail(charId, token, senderUsername, targetUsername, targetUserType);
		var charTr = target.closest('tr');
		var accId = parseInt(charTr.attr('id').substring('account-'.length));
		var needsMailTag = $(`#acc-${accId}-needsmail`, charTr);
		needsMailTag.remove();
	}
	
	
	function setUpEventhandlers() {
		var accountTable = $('#account-table-body');
		accountTable.on('click', '[data-type="acc-enable"]', enableAccountHandler);
		accountTable.on('click', '[data-type="acc-disable"]', disableAccountHandler);
		accountTable.on('click', '[data-action="editAccount"]', editAccountHandler);
		accountTable.on('click', '[data-action="sendAuthMail"]', sendAuthMailHandler);
	}

	function editAccount(accountId) {
		var name = $('#acc-'+accountId+"-name").text();
		var roles = $('#acc-'+accountId+'-roles').text();
		var default_char_name = $('#acc-'+accountId+'-cchar').text();
		$('#acc-edit-name').val(name);
		// this is more complicated
		// $('#acc-edit-roles')
		roles = roles.split(", ");
		// map the roles he has to a dict so we can fast and easy check for them
		// later
		var has_roles = {};
		for (let role in roles) {
			has_roles[roles[role]] = true;
		}

		var edit_roles_select = document.getElementById('acc-edit-roles');
		for (var i=0; i < edit_roles_select.options.length; i++) {
			var option = edit_roles_select.options[i];
			var val = option.value;
			if (val in has_roles) {
				option.selected = true;
			} else {
				option.selected = false;
			}
		}
		$('#acc-edit-cchar').val(default_char_name);
		$('#acc-edit-id').val(accountId);
		$('#modal-account-edit').modal('toggle');
	}
	function noclick() {
		$('.noclick').click(function(e){
			e.preventDefault();
		});
	}

	function sendAuthMail(charId, token, sig, username, type) {
		var link_prefix = window.location.protocol + '//' + window.location.host;
		var link = link_prefix+'/tokenauth?token='+token;
		var mail = "";
		var topic = "";
		switch(type){
		case "resident":
		case "tbadge":
			mail = getMetaData(`mail-${type}-body`);
			topic =  getMetaData(`mail-${type}-topic`);
			break;
		default:
			mail = getMetaData('mail-other-body');
			topic = getMetaData('mail-other-topic');
		}
		mail = mail.replace("$recv$", username).replace("$link$", link).replace("$sig$", sig);
		topic = topic.replace("$recv$", username).replace("$link$", link).replace("$sig$", sig);
		//
		// [{"recipient_id": ID, "recipient_type": "alliance|character|corporation|mailing_list"}]
		sendMail([{"recipient_id": charId, "recipient_type": "character"}], topic, mail);
	}
	
	function setUpTable() {
		var editableGrid = new EditableGrid(
			"Accounts",
			{
				enableSort: true,
				pageSize: 10,
				maxBars: 5
			},
			$.parseHTML('<i class="fa fa-arrow-down" aria-hidden="true"></i>')[0],
			$.parseHTML('<i class="fa fa-arrow-up" aria-hidden="true"></i>')[0]);

		editableGrid.load({
			metadata: [
				{
					name: "Actions",
					datatype: "html",
					editable: false
				}, {
					name: "Account Name",
					datatype: "html",
					editable: false
				}, {
					name: "Roles",
					datatype: "string",
					editable: false
				}, {
					name: "Current Char",
					datatype: "string",
					editable: false
				}, {
					name: "Alts",
					datatype: "string",
					editable: false
				}, {
					name: "#",
					datatype: "integer",
					editable: false
				}
			]
		});

		editableGrid.attachToHTMLTable('acctable');
		editableGrid.initializeGrid();
		editableGrid.renderGrid();
		$('#filter').on('keyup', function() {
			editableGrid.filter($('#filter').val());
		});
	}
	
	function init() {
		noclick();
		setUpEventhandlers();
		setUpTable();
	}

	$(document).ready(init);
	return {};
})();