'use strict';
if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.ship_assignment) {
	waitlist.ship_assignment = {};
}

waitlist.ship_assignment.check_edit = (function () {

	function init() {
		let check_select = $("#check_type");
		check_select.on("change", typeSelectHandler);
		updateHiddenElements(parseInt(check_select.val(), 10));
	}

	function typeSelectHandler(event) {
		updateHiddenElements(parseInt($(event.target).val(), 10));
	}

	function updateHiddenElements(type_id) {
		if (isNaN(type_id)) return;
		if (type_id > 3) {
			$("#check_add_modifier, #check_add_rest_type_ids, #check_add_rest_invgroup_ids, #check_add_rest_mgroup_ids").parent().prop("hidden", false);
		} else {
			$("#check_add_modifier, #check_add_rest_type_ids, #check_add_rest_invgroup_ids, #check_add_rest_mgroup_ids").parent().prop("hidden", true);
		}
	}

	$(document).ready(init);
})();
