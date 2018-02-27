EditableGrid.prototype.initializeGrid = function() {
  this.setCellRenderer("Account Name", new AccountCellRenderer());
};

$(document).ready(function() {
  let getMetaData = waitlist.base.getMetaData;
  var canViewProfile = getMetaData('can-view-profile') === "True";
	var editableGrid = new EditableGrid(
		"CommandCore",
		{
			enableSort: true,
			pageSize: 10,
			maxBars: 5
		});

	editableGrid.load({
		metadata: [
			{
				name: "Account Name",
				datatype: "string",
				editable: false,
				values: [{"value": "canViewProfile", "label": canViewProfile}]
			}, {
				name: "Roles",
				datatype: "string",
				editable: false
			}, {
				name: "Known Alts",
				datatype: "string",
				editable: false
			}
		]
	});

	editableGrid.attachToHTMLTable('commanderlist');
	editableGrid.initializePaginator();
	editableGrid.initializeGrid();
	editableGrid.renderGrid();
	$('#filter').on('keyup', function() {
		editableGrid.filter($('#filter').val());
	});
});
