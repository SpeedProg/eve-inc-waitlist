'use strict';

if (!waitlist) {
	var waitlist = {};
}


waitlist.accounts = (function() {
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;
	
	var sendMail = waitlist.IGBW.sendMail;
	
	let grid = null;

	function disableAccount(accountId, onsuccess){
		var settings = {
				async: true,
				dataType: "text",
				error: function() {
					displayMessage($.i18n('wl-accounts-error-disable-account-failed'), "danger");
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
					displayMessage($.i18n('wl-accounts-error-enabling-account-failed'), "danger");
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
			let accountRow = new AccountRow(id, grid);
			accountRow.status = $.i18n('wl-account-status-active');
		});
	}
	
	function disableAccountHandler(event) {
		var source = $(event.currentTarget);
		var id = Number(source.data('id'));
		disableAccount(id, function() {
			let accountRow = new AccountRow(id, grid);
			accountRow.status = $.i18n('wl-account-status-deactivated');
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
		let account_node = document.getElementById(`account-${accountId}`);
		let account_row = new AccountRow(accountId, grid);
		let name = account_row.name;		
		
		let roles_node = account_node.children[account_row.rolesIdx];
		let has_new_tag = (roles_node.children.length > 0 && roles_node.children[0].nodeName === "SPAN");
		let roles = roles_node.textContent;
		roles = roles.replace(/[\t\n\r]/g, ''); // clean up tabs and newlines
		// if it has a new tag remove the "New" from the beginning
		if (has_new_tag){
			roles = roles.slice(3)
		}
		
		let default_char_name = account_row.defaultCharName;
		$('#acc-edit-name').val(name);
		// this is more complicated
		// $('#acc-edit-roles')
		roles = roles.split(", ");
		roles = roles.map(x => x.trim())
		// map the roles he has to a dict so we can fast and easy check for them
		// later
		let has_roles = {};
		for (let idx in roles) {
			has_roles[roles[idx]] = true;
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
		grid = new EditableGrid(
			"Accounts",
			{
				enableSort: true,
				pageSize: 10,
				maxBars: 5
			},
			$.parseHTML('<i class="fa fa-arrow-down" aria-hidden="true"></i>')[0],
			$.parseHTML('<i class="fa fa-arrow-up" aria-hidden="true"></i>')[0]);

		grid.load({
			metadata: [
				{
					name: 'actions',
					datatype: "string",
					editable: false,
					values: [{"value": "rolesColumnName", "label": "roles"}]
				}, {
					name: 'status',
					datatype: "string",
					editable: false
				}, {
					name: 'account-name',
					datatype: "string",
					editable: false,
					values: [{"value": "canViewProfile", "label": true}]
				}, {
					name: 'roles',
					datatype: "html",
					editable: false
				}, {
					name: 'current-character',
					datatype: "string",
					editable: false
				}, {
					name: 'alts',
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

		grid.attachToHTMLTable('acctable');
		grid.initializePaginator();
		grid.initializeGrid();
		grid.renderGrid();
		let oldFilter = null;
		$('#filter').on('keyup', function() {
			if (oldFilter != null) grid.removeFilter(oldFilter);
			oldFilter = new StringFilter($('#filter').val());
			grid.addFilter(oldFilter);
		});
		registerRoleFilterSelect(grid, 'filterRole');
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
	this.setCellRenderer('account-name', new AccountCellRenderer());
	this.setCellRenderer('alts', new AltCellRenderer());
	this.setCellRenderer('actions', new ActionCellRenderer());
};