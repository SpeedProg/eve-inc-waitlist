'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.linemember = (function() {
	var getMetaData = waitlist.base.getMetaData;
	const disableGong = waitlist.gong.disableGong;
	var settings = {};

	function getFitUpdateUrl(fitID) {
		return settings.fit_update_url.replace('-1', fitID);
	}

	function removeSelf() {
		var settings = {
			dataType: "text",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			method: 'DELETE',
			url: getMetaData('url-self-remove-all')
		};
		$.ajax(settings);
	}

	function removeOwnEntry(wlId, charId, entryId) {
		var settings = {
			dataType: "text",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			method: 'DELETE',
			url: "/api/self/wlentry/remove/" + entryId
		};
		$.ajax(settings);
	}

	function removeOwnFit(event) {
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-fit'));
		event.stopPropagation();
		var settings = {
			dataType: "text",
			headers: {
				'X-CSRFToken': getMetaData('csrf-token')
			},
			method: 'DELETE',
			url: "/api/self/fittings/remove/" + fitId
		};
		$.ajax(settings);
	}

	function updateFit(event) {
		event.stopPropagation();
		var target = $(event.currentTarget);
		var fitId = Number(target.attr('data-fit'));
		var updateUrl = getFitUpdateUrl(fitId);
		window.location = updateUrl;
	}

	function removeOwnEntryHandler(event) {
		var target = $(event.currentTarget);
		var wlId = target.attr('data-wlId');
		var charId = target.attr('data-characterid');
		var entryId = target.attr('data-entryId');
		removeOwnEntry(wlId, charId, entryId);
	}

	function removeSelfHandler() {
		removeSelf();
		disableGong();
		$('.wlb').remove();
	}

	function init() {
		settings.fit_update_url = getMetaData('api-fit-update');

		// setup handler for the leave waitlist button
		$('body').on('click', '[data-action="removeSelfFromWaitlists"]',
			removeSelfHandler);

		// setup fit button handler related to linemembers
		$("#waitlists").on("click", '[data-action="remove-own-fit"]',
			removeOwnFit);
		$("#waitlists").on("click", '[data-action="update-fit"]', updateFit);
		$("#waitlists").on('click', '[data-action="removeOwnEntry"]',
			removeOwnEntryHandler);
	}

	$(document).ready(init);

	return {};
})();
