'use strict';
if (!getMetaData){
	var getMetaData = function (name) {
		return $('meta[name="'+name+'"]').attr('content');
	};
}
function testTSPoke() {
    $.get(getMetaData('api-ts-test'));
}