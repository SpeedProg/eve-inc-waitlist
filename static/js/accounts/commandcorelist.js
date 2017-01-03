$(document).ready(function() {
	var editableGrid = new EditableGrid(
		"CommandCore",
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
				name: "Account Name",
				datatype: "string",
				editable: false
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
	editableGrid.initializeGrid();
	editableGrid.renderGrid();
	$('#filter').on('keyup', function() {
		editableGrid.filter($('#filter').val());
	});
});
