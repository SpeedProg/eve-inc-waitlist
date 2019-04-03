/**
 * Actions Cell Renderer
 * @constructor
 * @class Class to render a cell action buttons
 */
function ActionCellRenderer(config) { this.init(config); }
ActionCellRenderer.prototype = new CellRenderer();

ActionCellRenderer.prototype.render = function(cell, value)
{

	let roles_column_name = this.column.optionValuesForRender["rolesColumnName"];
	
	// we don't know in what row we actually are
	let actions = new Actions(cell, value, roles_column_name, this.editablegrid, null);
	
	let account_id = actions.account_id;
	let disabled = actions.disabled;
	let had_welcome_mail = actions.had_mail;
	let target_char_id = actions.target_id;
	let sender_username = actions.sender_name;
	let target_username = actions.target_name;
	console.log('AccId: '+account_id+ " Disabled: "+disabled);
	let roles_column_idx = this.editablegrid.getColumnIndex(roles_column_name);

	let status_text_key = disabled ? 'wl-enable' : 'wl-disable';
	let status_button = $.parseHTML(`<button type="button" class="btn btn-sm btn-warning mr-1" data-type="${disabled ? "acc-enable" : "acc-disable" }" data-id="${ account_id }"></button>`)[0];
	status_button.textContent = $.i18n(status_text_key);
	let edit_button = $.parseHTML(`<button type="button" class="btn btn-sm btn-secondary mr-1" data-action="editAccount" data-accId="${account_id}"></button>`)[0];
	edit_button.textContent = $.i18n('wl-edit');
	
	cell.appendChild(status_button);
	cell.appendChild(edit_button);
	let roles_string = this.editablegrid.getValueAt(cell.rowIndex, roles_column_idx);
	let roles_list = RoleFilter.rolesGridValueToList(roles_string);
	
	let is_tbadge = roles_list.includes('tbadge');
	let is_rbadge = roles_list.includes('resident');
	if (!had_welcome_mail) {
		let user_type = is_tbadge ? 'tbadge' : is_rbadge ? 'resident' : 'other';
		let welcome_mail_button = $.parseHTML(`<button type="button" class="btn btn-sm btn-info" data-action="sendAuthMail" data-characterid="${target_char_id}" data-userType="${user_type}"></button>`)[0];
		welcome_mail_button.setAttribute('data-username', sender_username);
		welcome_mail_button.setAttribute('data-accusername', target_username);
		welcome_mail_button.textContent = $.i18n('wl-welcome-mail-button-text');
		
		cell.appendChild(welcome_mail_button);
	}
};

ActionCellRenderer.prototype.getDisplayValue = function(rowIndex, value)
{
	return value;
};
