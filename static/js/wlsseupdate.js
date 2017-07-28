'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.sse = (function() {
	let getMetaData = waitlist.base.getMetaData;

	let eventListeners = [];

	let settings = {};
	
	let eventSource;
	let errorCount = 0;
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
		let wlgroup = getMetaData('wl-group-id');
		if(typeof wlgroup !== "undefined") {
			eventSource = getSSE("waitlistUpdates,gong,statusChanged", wlgroup);
		} else {
			eventSource = getSSE("statusChanged");
		}
	}

	function getSSE(events, groupId) {
		let url = getMetaData('api-sse')+"?events="+encodeURIComponent(events);
		if (typeof groupId !== "undefined") {
			url += "&groupId="+encodeURIComponent(groupId);
		}
		let sse = new EventSource(url);
		sse.onerror = handleSSEError;
		sse.onopen = handleSSEOpen;

		sse.addEventListener("status-changed", statusChangedListener);

		for (let addedEvents of eventListeners) {
			sse.addEventListener(addedEvents.event, addedEvents.listener);
		}

		return sse;
	}

    function addEventListener(event, listener) {
        eventListeners.push({event: event, listener: listener});
        if (typeof eventSource !== 'undefined') {
            eventSource.addEventListener(event, listener);
        }
    }

    function statusChangedListener(event) {
		let data = JSON.parse(event.data);
		// check if we are current disabled
		// and if we are and the new status is not reload main page
		let wlgroup = getMetaData('wl-group-id');
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
			}
		}
	}

	function init() {
		settings.can_manage = getMetaData('can-fleetcomp') === "True";
		if (window.EventSource) {
			connectSSE();
		}
	}
	
	
    $(document).ready(init);
	return {
	addEventListener: addEventListener
	};
})();



