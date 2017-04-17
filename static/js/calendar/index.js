if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.calendar) {
	waitlist.calendar = {};
}

waitlist.calendar.index = (function () {
	function init() {
		 $('[data-toggle="popover"]').popover();
	}
	$(document).ready(init);
})();