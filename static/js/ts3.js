'use strict';
let getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
};
function testTSPoke() {
    $.get(getMetaData('api-ts-test'));
}