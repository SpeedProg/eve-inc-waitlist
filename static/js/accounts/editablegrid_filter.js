class RoleFilter extends Filter {
	constructor(roleName) {
		super();
		this.roleName = roleName;
	}
	
	shouldInclude(row, ridx, grid) {
		let roleIdx = grid.getColumnIndex('roles');
		let roleString = row.columns[roleIdx];
		let accId = row.id.substring(8);
		console.log("Account Id: "+accId+ " RIdx: "+ ridx);
		let value = grid.getValueAt(ridx, roleIdx);
		let roles_node = $.parseHTML('<div>'+value+'</div>')[0];
		
		// remove the new node
		if (roles_node.children.length > 0 && roles_node.children[0].nodeName === "SPAN") {
			roles_node.children[0].remove()
		}
		let roles = roles_node.textContent;
		roles = roles.replace(/[\t\n\r]/g, ''); // clean up tabs and newlines
		roles = roles.split(', ');
		roles = roles.map(role => role.trim());
		console.log(roles);
		console.log("Role we want: " + this.roleName);
		let should_include = roles.includes(this.roleName);
		console.log("Should include " + should_include);
		return should_include;
	}
}
