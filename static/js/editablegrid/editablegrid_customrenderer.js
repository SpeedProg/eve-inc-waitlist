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