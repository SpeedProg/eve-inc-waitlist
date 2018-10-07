EditableGrid.prototype.initializeGrid = function() {
	this.setCellRenderer("account-name", new AccountCellRenderer());
};

$(document).ready(function() {
	var oldFilter = null;
	let getMetaData = waitlist.base.getMetaData;
	var canViewProfile = getMetaData('can-view-profile') === "True";
	var editableGrid = new EditableGrid(
		"CommandCore",
		{
			enableSort: true,
			pageSize: 10,
			maxBars: 5
		});

	// make sure translations are loaded
	i18nloaded.then(() => {
		editableGrid.load({
			metadata: [
				{
					name: "account-name",
					datatype: "string",
					editable: false,
					values: [{"value": "canViewProfile", "label": canViewProfile}]
				}, {
					name: "roles",
					datatype: "string",
					editable: false
				}, {
					name: "alts",
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
			if (oldFilter != null) editableGrid.removeFilter(oldFilter);
			oldFilter = new StringFilter($('#filter').val());
			editableGrid.addFilter(oldFilter);
		});
		registerRoleFilterSelect(editableGrid, 'filterRole');
	});
});
