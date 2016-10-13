var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

var eventSource = undefined;

function handleSSEError(event) {
	console.log("SSE Error Occured");
	event.target.close();
	eventSource = getSSE();
}

function fitAddedListener(event) {
	var data = JSON.parse(event.data);
	addFitToDom(data.listId, data.entryId, data.fit, data.isQueue);
}

function entryAddedListener(event) {
	var data = JSON.parse(event.data);
	addNewEntry(data.listId, data.entry, data.groupId, data.isQueue);
}

function fitRemovedListener(event) {
	var data = JSON.parse(event.data);
	removeFitFromDom(data.listId, data.entryId, data.fitId)
}

function entryRemovedListener(event) {
	var data = JSON.parse(event.data);
	removeEntryFromDom(data.listId, data.entryId);
}

function gongListener(event) {
	if(gongEnabled()) {
		playGong();
	}
}

function noSSE() {
	var nosse = '<div class="alert alert-danger" role="alert"><p class="text-xs-center">We have had to disable <strong>features</strong> please consider upgrading your<a href="http://caniuse.com/#feat=eventsource"> browser</a>!</p></div>'
	document.getElementById("gong").innerHTML = nosse;
}

function getSSE() {
	var sse = new EventSource(getMetaData('api-sse')+"?events="+encodeURIComponent("waitlistUpdates,gong")+"&groupId="+encodeURIComponent(getMetaData("wl-group-id")));
	sse.addEventListener("fit-added", fitAddedListener);
	sse.addEventListener("fit-removed", fitRemovedListener);
	
	sse.addEventListener("entry-added", entryAddedListener);
	sse.addEventListener("entry-removed", entryRemovedListener);
	sse.addEventListener("invite-send", gongListener);
	
	sse.onerror = handleSSEError;
	return sse;
}

$(document).ready(
function() {
	eventSource = getSSE();
	if (refreshWl != undefined) {
		refreshWl();
	}
});
