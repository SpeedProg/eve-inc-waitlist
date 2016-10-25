'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.dropdown = (function() {
	function minusPlus(event) {
		$(event).removeClass("fa-minus-square").addClass("fa-plus-square");
	}

	function plusMinus(event) {
		$(event).removeClass("fa-plus-square").addClass("fa-minus-square");
	}

	function waitlistCollapseHandler(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
		var id = target.attr("id");
		var togglerSelector = target.data("tog-icon");
		if (togglerSelector !== undefined || togglerSelector !== null) {
			localStorage.setItem(id, 'closed');
			minusPlus(togglerSelector);
		}
	}

	function waitlistExpandeHandler(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
		var id = target.attr("id");
		var togglerSelector = target.data("tog-icon");
		if (togglerSelector !== undefined || togglerSelector !== null) {
			localStorage.removeItem(id);
			plusMinus(togglerSelector);
		}
	}

	function statusCollapseHandler(event) {
		event.stopPropagation();
		var togglerSelector = $(event.currentTarget).data("tog-icon");
		if (togglerSelector !== undefined || togglerSelector !== null) {
			minusPlus(togglerSelector);
		}
	}

	function statusExpandHandler(event) {
		event.stopPropagation();
		var togglerSelector = $(event.currentTarget).data("tog-icon");
		if (togglerSelector !== undefined || togglerSelector !== null) {
			plusMinus(togglerSelector);
		}
	}

	function init() {
		// setup waitlist close/opne event handlers
		$('#waitlists').on('show.bs.collapse', '.collapse',
			waitlistExpandeHandler);
		$('#waitlists').on('hide.bs.collapse', '.collapse',
			waitlistCollapseHandler);

		// setup status close/open event handlers
		$('#status').on('show.bs.collapse', '.collapse',
			statusExpandHandler);
		$('#status').on('hide.bs.collapse', '.collapse',
			statusCollapseHandler);
	}

	$(document).ready(init);

	return {};
})();
