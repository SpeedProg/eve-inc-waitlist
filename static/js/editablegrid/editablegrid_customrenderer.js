/**
 * Account cell renderer
 * @constructor
 * @class Class to render a cell with Account names
 */
function AccountCellRenderer(config) { this.init(config); }
AccountCellRenderer.prototype = new CellRenderer();

AccountCellRenderer.prototype.render = function(element, value)
{
	if (this.column.optionValuesForRender["canViewProfile"] === true) {
		let link = document.createElement("a");
		link.setAttribute("href", `/accounts/profile/byname/${value}`);
		link.setAttribute("target", "_blank");
		link.textContent = value;
		element.appendChild(link);
	} else {
		element.textContent = value;
	}
};

AccountCellRenderer.prototype.getDisplayValue = function(rowIndex, value)
{
	return value;
};

/**
 * Alt Character cell renderer
 * @constructor
 * @class Class to render a cell with alt names
 */
function AltCellRenderer(config) { this.init(config); }
AltCellRenderer.prototype = new CellRenderer();

AltCellRenderer.prototype.render = function(element, value)
{

	let account_info = value.split(";");
	let account_id = Number(account_info[0]);
	let alts_list = new AltsList(account_id, this.column.optionValuesForRender["canChangeLinks"]);

	if (account_info[1].trim() !== "") {
		let alts_data = account_info[1].split(",");

		for(let alt_data_string of alts_data) {
			let alt_data = alt_data_string.split(':');
			if (alt_data.length != 2) {
				continue;
			}
			let character_name = alt_data[1];
			let character_id = alt_data[0];
			alts_list.addAltByData(character_id, character_name);
		}
	}
	element.appendChild(alts_list.element);
};

AltCellRenderer.prototype.getDisplayValue = function(rowIndex, value)
{
	let char_infos = value.split(";")[1].split(",");
	let char_names = [];
	for(let char_info of char_infos) {
		char_names.push(char_info.split(":")[1]);
	}
	return char_names.join(", ")
};