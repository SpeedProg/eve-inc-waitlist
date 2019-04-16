'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.sse = (function() {
	let getMetaData = waitlist.base.getMetaData;
	let displayMessage = waitlist.base.displayMessage;

	let eventListeners = [];

	let settings = {};
	
	let eventSource;
	let errorCount = 0;
	
	// we use this to track if we open successfully connections way to fast
	let lastSseOpen = new Date();
	function handleSSEError(event) {
		event.target.close();
		errorCount++;
		if (errorCount < 2) { // our first error reconnect this instant
			connectSSE(errorCount);
		// error 2-5, try reconnect after 2s
		} else if (errorCount >= 2 && errorCount <= 5) {
			setTimeout(connectSSE.bind(null, errorCount), 2000);
		} else if (errorCount >= 6 && errorCount <= 10) { // > 5 errors try reconnect after 10s
			setTimeout(connectSSE.bind(null, errorCount), 10000);
		// more then 10 reconnects don't try anymore
		} else {
			displayMessage($.i18n('wl-error-to-many-sse-errors'), 'danger');
		}
	}

	function handleSSEOpen() {
	  let currentTS = new Date();
	  if (currentTS - lastSseOpen < 1800) {
  	  // we are reconnecting way to fast
  	  errorCount = 11;
	  } else {
	    if (errorCount > 1) {
		    // refresh the page using json, to pull ALL the date, we might have
		    // missed sth
		    waitlist.listdom.loadWaitlist();
	    }
	    errorCount = 0; // reset error counter
		}
		lastSseOpen = currentTS;
	}

	function connectSSE(count = 0) {
		let wlgroup = getMetaData('wl-group-id');
		if(typeof wlgroup !== "undefined") {
			eventSource = getSSE("waitlistUpdates,gong,statusChanged", wlgroup, count);
		} else {
			eventSource = getSSE("statusChanged", undefined, count);
		}
	}

	function getSSE(events, groupId, count = 0) {
    console.log("getSSE");
		let url = getMetaData('api-sse')+"?events="+encodeURIComponent(events)+"&connect_try="+count;
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



