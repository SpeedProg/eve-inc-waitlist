'use strict';
if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.ship_assignment) {
	waitlist.ship_assignment = {};
}

waitlist.ship_assignment.collection_edit = (function () {

	let addSubwaitlistPopulationHandler = waitlist.ship_assignment.collection.addSubwaitlistPopulationHandler;

	function init() {
	addSubwaitlistPopulationHandler("#wl_group_id_select", "#default_target_id");
	$("#check_type").on("change", typeSelectHandler);
	}

	function typeSelectHandler(event) {
		let type = parseInt($(event.target).val(), 10);
		if (isNaN(type)) return;
		if (type > 3) {
			$("#check_add_modifier, #check_add_rest_type_ids, #check_add_rest_invgroup_ids, #check_add_rest_mgroup_ids").parent().prop("hidden", false);
		} else {
			$("#check_add_modifier, #check_add_rest_type_ids, #check_add_rest_invgroup_ids, #check_add_rest_mgroup_ids").parent().prop("hidden", true);
		}
	}

	$(document).ready(init);
})();
