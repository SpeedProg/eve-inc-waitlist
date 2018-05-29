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
					displayMessage("Disabling Account failed!", "danger");
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
					displayMessage("Enabling Account failed!", "danger");
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
			const td_status_field_id = "#account-"+id+"-status";
			const td = $(td_status_field_id);
			td.text('Active')
			source.attr("data-type", "acc-disable");
			source.text("Disable");
		});
	}
	
	function disableAccountHandler(event) {
		var source = $(event.currentTarget);
		var id = Number(source.data('id'));
		disableAccount(id, function() {
			const td_status_field_id = "#account-"+id+"-status";
			const td = $(td_status_field_id);
			td.text('Deactivated')
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
		let name = $('#acc-'+accountId+"-name > a").text();
		let roles_node = document.getElementById('acc-'+accountId+'-roles');
		let has_new_tag = (roles_node.childNodes.length > 0 && roles_node.childNodes[0].nodeName === "SPAN");
		let roles = roles_node.textContent;
		
		// if it has a new tag remove the "New" from the beginning
		if (has_new_tag){
			roles = roles.slice(3)
		}
		
		let default_char_name = $('#acc-'+accountId+'-cchar').text();
		$('#acc-edit-name').val(name);
		// this is more complicated
		// $('#acc-edit-roles')
		roles = roles.split(", ");
		// map the roles he has to a dict so we can fast and easy check for them
		// later
		let has_roles = {};
		for (let role in roles) {
			has_roles[roles[role]] = true;
		}

		let edit_roles_select = document.getElementById('acc-edit-roles');
		for (let i=0; i < edit_roles_select.options.length; i++) {
			let option = edit_roles_select.options[i];
			let val = option.value;
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
					name: "Status",
					datatype: "string",
					editable: false
				}, {
					name: "Account Name",
					datatype: "string",
					editable: false,
					values: [{"value": "canViewProfile", "label": true}]
				}, {
					name: "Roles",
					datatype: "html",
					editable: false
				}, {
					name: "Current Char",
					datatype: "string",
					editable: false
				}, {
					name: "Alts",
					datatype: "string",
					editable: false,
					values: [{"value": "canChangeLinks", "label": getMetaData('can-change-links') == 'True'}]
				}, {
					name: "#",
					datatype: "integer",
					editable: false
				}
			]
		});

		editableGrid.attachToHTMLTable('acctable');
		editableGrid.initializePaginator();
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

EditableGrid.prototype.initializeGrid = function() {
	this.setCellRenderer("Account Name", new AccountCellRenderer());
	this.setCellRenderer("Alts", new AltCellRenderer());
};