'use strict';
// this code is directly included into the base.html because the css element needs to be included during the first pass
// otherwise people will see a unstyled page flash
if (!waitlist) {
	var waitlist = {};
}

waitlist.themes = (function() {
	let settings = {
		'id': 'theme-css',
		'base_path': "/static/css/",
		'setting_key_prefix': 'themes-',
		'def_type': 'local',
		'def_file': 'bootstrap_purple_001.css',
		'def_integrity': null,
		'def_crossorigin': null

	};
	// file_name = null == standard file
	function setTheme(file_name, type, integrity, crossorigin) {
		localStorage.setItem(settings.setting_key_prefix+"file", file_name);
		localStorage.setItem(settings.setting_key_prefix+"type", type);
		if (integrity === null) {
			localStorage.removeItem(settings.setting_key_prefix+"integrity");
		} else {
			localStorage.setItem(settings.setting_key_prefix+"integrity", integrity);
		}
		if (crossorigin === null) {
			localStorage.removeItem(settings.setting_key_prefix+"crossorigin");
		} else {
			localStorage.setItem(settings.setting_key_prefix+"crossorigin", crossorigin);
		}

		let new_element = false;
		let theme_element = document.getElementById(settings.id);
		// we got none yet
		if (theme_element === null) {
			// add one
			let parser = new DOMParser();
			let htmlPart = parser.parseFromString('<html><body><link rel="stylesheet" href="" id="'+settings.id+'"></body></html>', "text/html");
			theme_element = htmlPart.getElementById(settings.id);
			new_element = true;
		}

		let pure_element = theme_element;

		// lets check if we have a local or remote theme
		if (type === 'remote' && integrity !== null && (!pure_element.hasAttribute('integrity')
			|| !pure_element.getAttribute('integrity') !== integrity)) {
			pure_element.setAttribute('integrity', integrity);
		}
		if (type === 'remote' && crossorigin !== null && (!pure_element.hasAttribute('crossorigin')
			|| !pure_element.getAttribute('crossorigin') !== crossorigin)) {
			pure_element.setAttribute('crossorigin', crossorigin);
		}

		if ((type === 'local' || integrity === null) && pure_element.hasAttribute('integrity')) {
			pure_element.removeAttribute('integrity')
		}
		if ((type === 'local' || crossorigin === null) && pure_element.hasAttribute('crossorigin')) {
			pure_element.removeAttribute('crossorigin');
		}
		// lets set the href
		let href = type === "remote" ? file_name : settings.base_path+file_name;
		pure_element.setAttribute('href', href);
		if (new_element) {

			document.write(pure_element.outerHTML);
			//let headElement = document.getElementsByTagName("head")[0];
			//let themLoaderElement = document.getElementById("themeloader");
			//themLoaderElement.insertAdjacentHTML("afterend", pure_element.outerHTML)
			//headElement.insertAfter(pure_element, themLoaderElement);
		}
	}

	function selectionChangeHandler(event) {
		let url = event.target.value;
		let target_option = event.target.options[event.target.options.selectedIndex];
		let type = target_option.getAttribute('data-type');
		let integrity = target_option.hasAttribute('data-integrity') ? target_option.getAttribute('data-integrity') : null;
		let crossorigin = target_option.hasAttribute('data-crossorigin') ? target_option.getAttribute('data-crossorigin') : null;
		setTheme(this.value, type, integrity, crossorigin); //
	}

	function setCurrentTheme() {
		let file = localStorage.getItem(settings.setting_key_prefix+"file");
		let type = localStorage.getItem(settings.setting_key_prefix+"type");
		let integrity = localStorage.getItem(settings.setting_key_prefix+"integrity");
		let crossorigin = localStorage.getItem(settings.setting_key_prefix+"crossorigin");
		document.addEventListener('DOMContentLoaded', function () {
			setSelectionAfterPageReady(file);
		});
		if (file === null || file === "null") {
			// set the default theme
			setTheme(settings.def_file, settings.def_type, settings.def_integrity, settings.def_crossorigin)
		} else {
			setTheme(file, type, integrity, crossorigin);
		}
	}

	function initThemeAfterPageReady() {
		let selector = $('#theme-selector')[0];
		let firstOption = selector[selector.selectedIndex];
		let file = firstOption.getAttribute('value');
		let type = firstOption.getAttribute('data-type');
		let integrity = firstOption.hasAttribute('data-integrity') ? firstOption.getAttribute('data-integrity') : null;
		let crossorigin = firstOption.hasAttribute('data-crossorigin') ? firstOption.getAttribute('data-crossorigin') : null;
		setTheme(file, type, integrity, crossorigin);
	}

	function setSelectionAfterPageReady(file) {
		let selector = $('#theme-selector')[0];
		for(let idx=0; idx < selector.length; idx++) {
			if (selector[idx].getAttribute('value') === file) {
				selector[idx].selected = true;
			}
		}
	}

	// apply our current theme and set handlers
	function init() {
		let selector = $('#theme-selector');
		selector.on("change", selectionChangeHandler);
	}
	setCurrentTheme();
	document.addEventListener('DOMContentLoaded', init);
	// nothing to export
	return {};
})();