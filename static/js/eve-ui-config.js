eveui_mode = 'modal';
var eveui_imageserver = function(image_ref) {
	if (image_ref.startsWith('Character')) {
		return eve_image(encodeURI(image_ref), 'jpg');
	}
	return eve_image(encodeURI(image_ref), 'png');
};
// fix for getting names for modules from ccp api that are in the users browser language
$.ajaxSetup({
	beforeSend: function(xhr, settings) {
		if (settings.url.includes('/universe/types/')) {
			xhr.setRequestHeader('Accept-Language', 'en-us, en;q=0.9');
		}
	}
});
