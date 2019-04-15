'use strict';

(function() {
	const css_element_id = 'theme-css';
	const select_id = 'theme-selector';
	const setting_key_prefix = 'themes-';
	const themes = [
		{% for theme in themes %}
		{
			'id': '{{ theme.id }}',
			{% if 'default' in theme and theme.default %}
			'default': true,
			{% endif %}
			{% if 'paths' in theme %}
			{% assets 'theme_' + theme.id %}
			'path': '{{ ASSET_URL }}',
			{% endassets %}
			{% elif 'url' in theme %}
			'path': '{{ theme.url }}',
			{% endif %}
			{% if 'integrity' in theme %}
			'integrity': '{{ theme.integrity }}',
			{% endif %}
			{% if 'crossorigin' in theme %}
			'crossorigin': '{{ theme.crossorigin }}',
			{% endif %}
		},
		{% endfor %}
	];

	function activateTheme(theme) {
		let theme_element = document.getElementById(css_element_id);
		const new_element = (theme_element === null);
		// we got none yet
		if (new_element) {
			// add one
			theme_element = document.createElement("link");
			theme_element.setAttribute('rel', 'stylesheet');
			theme_element.setAttribute('id', css_element_id);
		}

		if (theme.integrity) {
			if (new_element ||
					!theme_element.hasAttribute('integrity') ||
					!theme_element.getAttribute('integrity') !== theme.integrity) {
				theme_element.setAttribute('integrity', theme.integrity);
			}
		} else if (!new_element && theme_element.hasAttribute('integrity')) {
			theme_element.removeAttribute('integrity')
		}

		if (theme.crossorigin) {
			if (new_element ||
					!theme_element.hasAttribute('crossorigin') ||
					!theme_element.getAttribute('crossorigin') !== theme.crossorigin) {
				theme_element.setAttribute('crossorigin', theme.crossorigin);
			}
		} else if (!new_element && theme_element.hasAttribute('crossorigin')) {
			theme_element.removeAttribute('crossorigin')
		}

		theme_element.setAttribute('href', theme.path);

		if (new_element) {
			document.write(theme_element.outerHTML);
		}
	}

	function selectionChangeHandler(event) {
		const theme = themes.find((theme) => theme.id === event.target.value);
		if (theme) {
			if (theme.default) {
				localStorage.removeItem(setting_key_prefix + "id");
			} else {
				localStorage.setItem(setting_key_prefix + "id", theme.id);
			}
			activateTheme(theme);
		}
	}


	function setSelectionAfterPageReady(theme_id, selector) {
		for (let idx = 0; idx < selector.length; idx++) {
			if (selector[idx].getAttribute('value') === theme_id) {
				selector[idx].selected = true;
				return
			}
		}
		console.error('No theme with value ' + theme_id + ' was found in selector, this should never happen.');
	}

	// this
	(function setUpTheme() {
		let local_storage_id = localStorage.getItem(setting_key_prefix + "id");
		let theme;
		if (local_storage_id) {
			theme = themes.find((theme) => theme.id === local_storage_id);
			if (theme) {
				if (theme.default && window.localStorage) {
					localStorage.removeItem(setting_key_prefix + "id");
				}
			} else {
				theme = themes.find((theme) => theme.default);
			}
		} else {
			theme = themes.find((theme) => theme.default);
		}

		activateTheme(theme);
		
		// set selection after dome is done
		// and then setup a handler for theme selection
		document.addEventListener('DOMContentLoaded', function() {
			let selector = document.getElementById(select_id);
			setSelectionAfterPageReady(theme.id, selector);
			selector.addEventListener('change', selectionChangeHandler);
		});
	})();

})();