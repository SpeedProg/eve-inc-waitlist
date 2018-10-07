'use strict';
if (!waitlist) {
	var waitlist = {};
}
if (!waitlist.permission) {
	waitlist.permission = {};
}

waitlist.permission.config = (function () {

	const getMetaData = waitlist.base.getMetaData;
	const displayMessage = waitlist.base.displayMessage;

	const settings = {
		'urls': {
			'change': getMetaData('url.api.permission.change')
		}
	};



	function handleCheckboxChange(event) {
		const checkbox = $(event.target);
		const perm_name = checkbox.attr('data-perm-name');
		const role_name = checkbox.attr('data-role-name');
		const state = checkbox.prop('checked');
		setPermission(role_name, perm_name, state)
	}

	function setPermission(role_name, perm_name, state) {
		const data = {
			async: true,
			dataType: "text",
			error: function() {
				displayMessage($.i18n('wl-permissions-setting-failed'), "danger");
			},
			method: "POST",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			data: {
				'perm_name': perm_name,
				'role_name': role_name,
				'state': state
			}
		};
		$.ajax(settings.urls.change, data);
	}

	function init() {
		$('[data-action="changePermission"]').on("change", handleCheckboxChange);
	}

	$(document).ready(init);

	return {};
})();