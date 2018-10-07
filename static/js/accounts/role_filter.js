function registerRoleFilterSelect(editableGrid, selectId){
	let oldFilter = null;
	$('#'+selectId).on('change', function(event){
		let select = event.currentTarget;
		let val = select.value;
		if (oldFilter != null) editableGrid.removeFilter(oldFilter);
		if (val != '') {
			oldFilter = new RoleFilter(val);
			editableGrid.addFilter(oldFilter);
		} else {
			oldFilter = null;
		}
	});
}