'use strict';
if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.ship_assignment) {
	waitlist.ship_assignment = {};
}

waitlist.ship_assignment.collection_list = (function () {
	function handleGroupSelected(event) {
		const select = $(event.target);
		const wl_select = $("#default_target_id");
		let enabled_options = wl_select.find("option:not([disabled])");
		enabled_options.prop("hidden", true);
		enabled_options.prop("disabled", true);
		let options_for_selection = wl_select.find("option[data-group=\"" + select.val() + "\"]");
		options_for_selection.prop("disabled", false);
		options_for_selection.prop("hidden", false);
	}

	function init() {
		$('#wl_group_id_select').on("change", handleGroupSelected);
	}

	$(document).ready(init);
})();
