'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.dropdown = (function() {

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
	}

	function init() {
		// Setup open & close event handler
		$("#content").on("hide.bs.collapse show.bs.collapse", ".collapse",
			dropdownHandler);
	}

	$(document).ready(init);
	return {};
})();
