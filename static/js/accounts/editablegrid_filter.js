class RoleFilter extends Filter {
	constructor(roleName) {
		super();
		this.roleName = roleName;
	}
	
	shouldInclude(row, ridx, grid) {
		let roleIdx = grid.getColumnIndex('roles');
		let roleString = row.columns[roleIdx];
		let accId = row.id.substring(8);
		let roles_node = document.getElementById('acc-' + accId + '-roles');

		let has_new_tag = (roles_node.childNodes.length > 0 && roles_node.childNodes[0].nodeName === "SPAN");
		let roles = roles_node.textContent;
		roles = roles.replace(/[\t\n\r]/g, ''); // clean up tabs and newlines
		// if it has a new tag remove the "New" from the beginning
		if (has_new_tag){
			roles = roles.slice(3)
		}
		roles = roles.split(', ');
		return roles.includes(this.roleName);
	}
}
