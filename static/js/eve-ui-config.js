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

	let last_lang = localStorage.getItem('last_lang');
	if (!last_lang || last_lang != lang_code) {
		localStorage.setItem('last_lang', lang_code);
		$.ajax(`https://esi.tech.ccp.is/v1/status/`, {
			dataType: 'json',
				cache: true,
		}).done(function (data) {
			eve_version = data.server_version;
			let open = indexedDB.open('eveui', eve_version);
			let done = false;
			open.onupgradeneeded = function (e) {
				let db = open.result;
				if (db.objectStoreNames.contains('cache')) {
					db.deleteObjectStore('cache');
				}
				db.createObjectStore('cache', { keyPath: 'path' });
				done = true;
			};
			open.onsuccess = function (event) {
				if (done) {
					return;
				}
				db = open.result;
				let tx = db.transaction('cache', 'readwrite');
				if (db.objectStoreNames.contains('cache')) {
					let store = tx.objectStore('cache');
					store.clear();
				}
			};
		});
	}
}
