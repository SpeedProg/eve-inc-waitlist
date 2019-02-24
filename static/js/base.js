'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.base = (() => {

	function buildSwaggerClient(csrf) {
		return SwaggerClient({
			url: "/spec/v1/swagger.json",
			requestInterceptor : (req) => {
				req.headers['X-CSRFToken'] = csrf;
				return req;
			}
		});
	}

	class WaitlistBase {
		get client() {
			if (!this.swagger_client) {
				this.swagger_client = buildSwaggerClient(this.getMetaData('csrf-token')).catch((err) => {
					this.swagger_client = null;
					throw err;
				});
			}
			return this.swagger_client;
		}

		getMetaData(name) {
			return $(`meta[name="${name}"]`).attr('content');
		}

		displayMessage(message, type, html, id) {
			var alertHTML = $($.parseHTML(`<div class="alert alert-dismissible alert-${type}" role="alert">
			<button type="button" class="close" data-dismiss="alert" aria-label="Close">
			<span aria-hidden="true">&times;</span>
			</button>
			<p class="text-center"></p>
			</div>`));
			var textContainer = $('.text-center', alertHTML);
			if (typeof id !== "undefined") {
				alertHTML.attr("id", id);
			}
			if (typeof html !== "undefined") {
				textContainer.html(message);
			} else {
				textContainer.text(message);
			}
			var alertArea = $('#alert-area-base');
			alertArea.append(alertHTML);
		}
	}
	
	const base = new WaitlistBase();

	async function handleLanguageSelection(event) {
		const langCode = event.target.value;
		try {
			const client = await base.client;
			await client.apis.I18n.put_i18n_locale({
				"lang": langCode
			});
			location.reload(true);
		} catch (event) {
			if (typeof(event.response) !== "undefined" &&
				typeof(event.response.obj) !== "undefined" &&
				typeof(event.response.obj.error) !== "undefined") {
					base.displayMessage($.i18n('wl-lang-change-failed', event.response.obj.error), "danger");
			} else {
				base.displayMessage($.i18n('wl-lang-change-failed', langCode), "danger");
			}
		}
	}

	$(document).ready(() => {
		document.getElementById("lang-select")
			.addEventListener("change", handleLanguageSelection);

		if (!window.EventSource) {
			waitlist.base.displayMessage($.i18n('wl-browser-warning-sse'), 'danger', true);
		}
	});

	return base;
})();