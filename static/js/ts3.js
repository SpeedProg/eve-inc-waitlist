'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.ts3 = (function () {
	var getMetaData = waitlist.base.getMetaData;
	function testPoke() {
		$.get(getMetaData('api-ts-test'));
	}
	function init () {
		// setup fit button handler related to linemembers
	    $("body").on('click', '[data-action="test-poke"]', testPoke);
	}

    $(document).ready(init);
	return {};
})();

