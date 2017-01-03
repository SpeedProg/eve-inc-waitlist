eveui_mode = 'modal';
var eveui_imageserver = function(image_ref) {
	if (image_ref.startsWith('Character')) {
		return eve_image(encodeURI(image_ref), 'jpg');
	}
	return eve_image(encodeURI(image_ref), 'png');
};