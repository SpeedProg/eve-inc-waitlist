'use strict';

if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.calendar) {
	waitlist.calendar = {};
}

waitlist.calendar = (function() {
	function init() {
		$('#startpicker').datetimepicker({
			icons: {
				time: "fa fa-clock-o",
				date: "fa fa-calendar",
				up: "fa fa-arrow-up",
				down: "fa fa-arrow-down",
				previous: 'fa fa-chevron-left',
				next: 'fa fa-chevron-right',
				today: 'fa fa-calendar-o',
				clear: 'fa fa-trash',
				close: 'fa fa-times'
			},
			format: "YYYY/MM/DD HH:mm"
		});
	}
	$(document).ready(init);
	return {};
})();
