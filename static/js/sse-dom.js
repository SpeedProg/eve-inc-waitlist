'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.sse_dom = (function () {
	let getMetaData = waitlist.base.getMetaData;
	let loadWaitlist = waitlist.listdom.loadWaitlist;
	let addFitToDom = waitlist.listdom.addFitToDom;
	let addNewEntry = waitlist.listdom.addNewEntry;
	let removeFitFromDom = waitlist.listdom.removeFitFromDom;
	let removeEntryFromDom = waitlist.listdom.removeEntryFromDom;
	let updateMissedInvite = waitlist.listdom.updateMissedInvite;
	let setStatusDom = waitlist.listdom.setStatusDom;
	let clearWaitlists = waitlist.listdom.clearWaitlists;
	let sse = waitlist.sse;

	let settings = {};

	function fitAddedListener(event) {
		let data = JSON.parse(event.data);
		addFitToDom(data.listId, data.entryId, data.fit, data.isQueue, data.userId);
	}

	function entryAddedListener(event) {
		let data = JSON.parse(event.data);
		addNewEntry(data.listId, data.entry, data.groupId, data.isQueue);
		if (data.isQueue && settings.can_manage) {
			sendNotificationForEntry(data);
		}
	}

	function fitRemovedListener(event) {
		var data = JSON.parse(event.data);
		removeFitFromDom(data.listId, data.entryId, data.fitId);
	}

	function entryRemovedListener(event) {
		let data = JSON.parse(event.data);
		removeEntryFromDom(data.listId, data.entryId);
	}

	function missedInviteListener(event) {
		let data = JSON.parse(event.data);
		updateMissedInvite(data.userId);
	}

	function statusChangedListener(event) {
		let data = JSON.parse(event.data);
		// check if we are current disabled
		// and if we are and the new status is not reload main page
		let wlgroup = getMetaData('wl-group-id');
		if(typeof wlgroup !== "undefined") {
			if (!data.enabled) { // this waitlist got disabled
				// clear all the lists
				clearWaitlists();
				// remove the id from meta data
				$('meta[name="wl-group-id"]').remove();
			}
			setStatusDom(data);
		}
	}

	function sendNotificationForEntry(data) {
		if (!("Notification" in window)) {
			return;
		}
		let title = "New X-UP";
		let options = {
			'body': `New X-UP from ${data.entry.character.name}`
		};
		// if we have permission
		if (Notification.permission === "granted") {
			new Notification(title, options);
		// if we are not denied (user didn't select yet
		} else if (Notification.permission !== 'denied') {
			Notification.requestPermission(function (permission) {
				// If the user accepts, let's create a notification
				if (permission === "granted") {
					new Notification(title, options);
				}
			});
		}
	}

	sse.addEventListener("fit-added", fitAddedListener);
	sse.addEventListener("fit-removed", fitRemovedListener);

	sse.addEventListener("entry-added", entryAddedListener);
	sse.addEventListener("entry-removed", entryRemovedListener);

	sse.addEventListener("invite-missed", missedInviteListener);

	sse.addEventListener("status-changed", statusChangedListener);

	function init() {
		loadWaitlist();
		settings.can_manage = getMetaData('can-fleetcomp') === "True";
	}

	$(document).ready(init);

	return {};
})();