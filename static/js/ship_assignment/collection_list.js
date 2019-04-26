'use strict';
if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.ship_assignment) {
	waitlist.ship_assignment = {};
}

waitlist.ship_assignment.collection_list = (function () {

  let addSubwaitlistPopulationHandler = waitlist.ship_assignment.collection.addSubwaitlistPopulationHandler;
  let doInitialSubwaitlistPopulation = waitlist.ship_assignment.collection.doInitialSubwaitlistPopulation;

	function init() {
	  doInitialSubwaitlistPopulation("#wl_group_id_select", "#default_target_id");
	  addSubwaitlistPopulation("#wl_group_id_select", "#default_target_id");
	}

	$(document).ready(init);
})();
