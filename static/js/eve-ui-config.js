eveui_mode = 'modal';
var eveui_imageserver = function(image_ref) {
	if (image_ref.startsWith('Character')) {
		return eve_image(encodeURI(image_ref), 'jpg');
	}
	return eve_image(encodeURI(image_ref), 'png');
};
// fix for getting names for modules from ccp api that are in the users browser language
{
	let lang_code = document.getElementById('lang-code').getAttribute('content');
	
	// esi only knows en_us (maybe it accepts en_* too but lets better be sure
	if (lang_code.startsWith('en_') || lang_code == 'en') {
		lang_code = 'en_us';
	}

	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (settings.url.includes('/universe/types/')) {
				xhr.setRequestHeader('Accept-Language', lang_code);
			}
		}
	});
}
