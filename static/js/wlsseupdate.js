'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.sse = (function() {
	var getMetaData = waitlist.base.getMetaData;
	var displayMessage = waitlist.base.displayMessage;
	
	var loadWaitlist = waitlist.listdom.loadWaitlist;
	var addFitToDom = waitlist.listdom.addFitToDom;
	var addNewEntry = waitlist.listdom.addNewEntry;
	var removeFitFromDom = waitlist.listdom.removeFitFromDom;
	var removeEntryFromDom = waitlist.listdom.removeEntryFromDom;
	var updateMissedInvite = waitlist.listdom.updateMissedInvite;
	var setStatusDom = waitlist.listdom.setStatusDom;
	var clearWaitlists = waitlist.listdom.clearWaitlists;

	var eventListeners = [];

	var settings = {};
	
	var eventSource;
	var errorCount = 0;
	function handleSSEError(event) {
		event.target.close();
		errorCount++;
		if (errorCount < 2) { // our first error reconnect this instant
			connectSSE();
		} else if (errorCount >= 2 && errorCount <= 5) {  // 2-5 errors, try
															// reconnect after
															// 1s
			setTimeout(connectSSE, 1000);
		} else { // > 5 errors try reconnect after 10s
			setTimeout(connectSSE, 10000);
		}
		event.target.close();
	}

	function handleSSEOpen() {
		if (errorCount > 1) {
			// refresh the page using json, to pull ALL the date, we might have
			// missed sth
			loadWaitlist();
		}
		errorCount = 0; // reset error counter
	}

	function connectSSE() {
		var wlgroup = getMetaData('wl-group-id');
		if(typeof wlgroup !== "undefined") {
			eventSource = getSSE("waitlistUpdates,gong,statusChanged", wlgroup);
		} else {
			eventSource = getSSE("statusChanged");
		}
	}

	function fitAddedListener(event) {
		var data = JSON.parse(event.data);
		addFitToDom(data.listId, data.entryId, data.fit, data.isQueue, data.userId);
	}

	function entryAddedListener(event) {
		var data = JSON.parse(event.data);
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
		var data = JSON.parse(event.data);
		removeEntryFromDom(data.listId, data.entryId);
	}

	function missedInviteListener(event) {
		var data = JSON.parse(event.data);
		updateMissedInvite(data.userId);
	}
	
	function statusChangedListener(event) {
		var data = JSON.parse(event.data);
		// check if we are current disabled
		// and if we are and the new status is not reload main page
		var wlgroup = getMetaData('wl-group-id');
		if(typeof wlgroup === "undefined") {
			if (data.enabled) {
				window.location.reload();
			}
		} else {
			if (!data.enabled) { // this waitlist got disabled
				// kill the current sse and setup a new one
				if (typeof eventSource !== 'undefined') {
					eventSource.close();
					eventSource = getSSE('statusChanged');
				}
				// clear all the lists
				clearWaitlists();
				// remove the id from meta data
				$('meta[name="wl-group-id"]').remove();
			}
			setStatusDom(data);
		}
	}

	function getSSE(events, groupId) {
		var url = getMetaData('api-sse')+"?events="+encodeURIComponent(events);
		if (typeof groupId !== "undefined") {
			url += "&groupId="+encodeURIComponent(groupId);
		}
		var sse = new EventSource(url);
		sse.onerror = handleSSEError;
		sse.onopen = handleSSEOpen;
		
		sse.addEventListener("fit-added", fitAddedListener);
		sse.addEventListener("fit-removed", fitRemovedListener);
		
		sse.addEventListener("entry-added", entryAddedListener);
		sse.addEventListener("entry-removed", entryRemovedListener);

		sse.addEventListener("invite-missed", missedInviteListener);
		
		sse.addEventListener("status-changed", statusChangedListener);

		for (let addedEvents of eventListeners) {
			sse.addEventListener(addedEvents.event, addedEvents.listener);
		}

		return sse;
	}

	function sendNotificationForEntry(data) {
		if (!("Notification" in window)) {
			return;
		}
		var title = "New X-UP";
		var options = {
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

    function addEventListener(event, listener) {
        eventListeners.push({event: event, listener: listener});
        if (typeof eventSource !== 'undefined') {
            eventSource.addEventListener(event, listener);
        }
    }

	function init() {
		settings.can_manage = getMetaData('can-fleetcomp') === "True";
		if (window.EventSource) {
			connectSSE();
		}
		loadWaitlist();
	}
	
	
    $(document).ready(init);
	return {
	addEventListener: addEventListener
	};
})();



