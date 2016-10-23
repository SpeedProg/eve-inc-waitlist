'use strict';
if (!getMetaData){
	var getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
}

if (!waitlist) {
	var waitlist = {};
}

waitlist.ts3 = (function () {
	var getMetaData = waitlist.base.getMetaData;
	function testPoke() {
		$.get(getMetaData('api-ts-test'));
	}
	return {};
})();