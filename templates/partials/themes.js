'use strict';
// this code is directly included into the base.html because the css element
// needs to be included during the first pass
// otherwise people will see a unstyled page flash
if (!waitlist) {
	var waitlist = {};
}

waitlist.themes = (function() {
	let settings = {
		'css_element_id': 'theme-css',
		'select_id': 'theme-selector',
		'setting_key_prefix': 'themes-',
		'default_theme_id': 'default',
		'themes': {
			'default': {
				id: 'default',
				path: {% assets "themes.default" %}'{{ ASSET_URL }}'{% endassets %},
				type: 'local',
				integrity: null,
				crossorigin: null,
			},
			'dark': {
				id: 'dark',
				path: {% assets "themes.dark" %}'{{ ASSET_URL }}'{% endassets %},
				type: 'local',
				integrity: null,
				crossorigin: null,
			},
			'dark_purple': {
				id: 'dark_purple',
				path: {% assets "themes.dark_purple" %}'{{ ASSET_URL }}'{% endassets %},
				type: 'local',
				integrity: null,
				crossorigin: null,
			}
		},
	};

	// file_name = null == standard file
	function setTheme(theme_id) {
		localStorage.setItem(settings.setting_key_prefix + "id", theme_id);

		let new_element = false;
		let theme_element = document.getElementById(settings.css_element_id);
		// we got none yet
		if (theme_element === null) {
			// add one
			let parser = new DOMParser();
			let htmlPart = parser.parseFromString(
			    '<html><body><link rel="stylesheet" href="" id="' + settings.css_element_id
			        + '"></body></html>', "text/html");
			theme_element = htmlPart.getElementById(settings.css_element_id);
			new_element = true;
		}

		let pure_element = theme_element;
		let theme = settings.themes[theme_id];
		// lets check if we have a local or remote theme
		if (theme.type === 'remote'
		    && theme.integrity !== null
		    && (!pure_element.hasAttribute('integrity') || !pure_element
		        .getAttribute('integrity') !== theme.integrity)) {
			pure_element.setAttribute('integrity', theme.integrity);
		}
		if (theme.type === 'remote'
		    && theme.crossorigin !== null
		    && (!pure_element.hasAttribute('crossorigin') || !pure_element
		        .getAttribute('crossorigin') !== theme.crossorigin)) {
			pure_element.setAttribute('crossorigin', theme.crossorigin);
		}

		if ((theme.type === 'local' || theme.integrity === null)
		    && pure_element.hasAttribute('integrity')) {
			pure_element.removeAttribute('integrity')
		}
		if ((theme.type === 'local' || theme.crossorigin === null)
		    && pure_element.hasAttribute('crossorigin')) {
			pure_element.removeAttribute('crossorigin');
		}
		// lets set the href
		let href = theme.path;
		pure_element.setAttribute('href', href);
		if (new_element) {

			document.write(pure_element.outerHTML);
			// let headElement = document.getElementsByTagName("head")[0];
			// let themLoaderElement = document.getElementById("themeloader");
			// themLoaderElement.insertAdjacentHTML("afterend",
			// pure_element.outerHTML)
			// headElement.insertAfter(pure_element, themLoaderElement);
		}
	}

	function selectionChangeHandler(event) {
		let theme_id = event.target.value;
		setTheme(theme_id);
	}

	function setUpTheme() {
		let theme_id = localStorage.getItem(settings.setting_key_prefix + "id");
		
		if (theme_id === null || theme_id === "null" || !(theme_id in settings.themes) ) {
			// set the default theme
			theme_id = settings.default_theme_id;
		}

		let theme = settings.themes[theme_id];

		setTheme(theme_id);
		
		// set selection after dome is done
		// and then setup a handler for theme selection
		document.addEventListener('DOMContentLoaded', function() {
			setSelectionAfterPageReady(theme_id);
			let selector = document.getElementById(settings.select_id);
			selector.addEventListener('change', selectionChangeHandler);
		});
	}

	function initThemeAfterPageReady() {
		let selector = $('#theme-selector')[0];
		let firstOption = selector[selector.selectedIndex];
		let file = firstOption.getAttribute('value');
		let type = firstOption.getAttribute('data-type');
		let integrity = firstOption.hasAttribute('data-integrity') ? firstOption
		    .getAttribute('data-integrity')
		    : null;
		let crossorigin = firstOption.hasAttribute('data-crossorigin') ? firstOption
		    .getAttribute('data-crossorigin')
		    : null;
		setTheme(file, type, integrity, crossorigin);
	}

	function setSelectionAfterPageReady(theme_id) {
		let selector = document.getElementById(settings.select_id);
		let foundTheme = false;
		for (let idx = 0; idx < selector.length; idx++) {
			if (selector[idx].getAttribute('value') === theme_id) {
				selector[idx].selected = true;
				foundTheme = true;
				break;
			}
		}

		if (!foundTheme) {
			console.error('No theme with value ' + theme_id + ' was found in selector, this should never happen.');
				
		}

	}

	// this
	setUpTheme();
	// nothing to export
	return {};
})();