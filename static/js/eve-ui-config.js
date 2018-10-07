eveui_mode = 'modal';
var eveui_imageserver = function(image_ref) {
	if (image_ref.startsWith('Character')) {
		return eve_image(encodeURI(image_ref), 'jpg');
	}
	return eve_image(encodeURI(image_ref), 'png');
};
// fix for getting names for modules from ccp api that are in the users browser language
eveui_accept_language = document.getElementById('lang-code').getAttribute('content');
if (eveui_accept_language.startsWith('en_') || eveui_accept_language == 'en') {
	eveui_accept_language = 'en_us';
}
