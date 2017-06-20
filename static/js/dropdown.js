'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.dropdown = (function() {

	const
	storage = localStorage;

	function dropdownHandler(event) {
		event.stopPropagation();
		const
		icon = event.target.dataset.togIcon;
		if (event.type === "show") {
			$(icon).addClass("fa-minus-square").removeClass("fa-plus-square");
		}
		if (event.type === "hide") {
			$(icon).addClass("fa-plus-square").removeClass("fa-minus-square");
		}
		if (event.target.id.startsWith("wl-fits-col-")) {
			manageDropdownState(event);
		}
	}

	function manageDropdownState(event) {
		if (event.type === "show") {
			storage.removeItem(event.target.id);
		}
		if (event.type === "hide") {
			storage[event.target.id] = "closed";
		}
	}

	function init() {
		// Setup open & close event handler
		$("#content").on("hide.bs.collapse show.bs.collapse", ".collapse",
			dropdownHandler);

		// Load previous state of the waitlist
		const
		wlists = $("div[id|='wl-fits-col']");
		for (let wlist of wlists){
			if (storage.getItem(wlist.id) !== null) {
				$(wlist).collapse("hide");
			}
		}
	}

	$(document).ready(init);
	return {};
})();
