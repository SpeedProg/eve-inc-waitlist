var getMetaData = function (name) {
	return $('meta[name="'+name+'"]').attr('content');
}

function handleSSEError(event) {
	event.target.close();
	var sse = getGongSSE();
}

function getGongSSE() {
	var sse = new EventSource(getMetaData('gong-event'));
    sse.onmessage = function(message) {
    	var sound = document.getElementById('sound');
    	sound.volume = 0.5;
    	sound.currentTime = 0;
    	sound.play();
    }
    sse.onerror = handleSSEError;
    return sse;
}

function noSSE() {
	var nosse = '<div class="alert alert-danger" role="alert"><p class="text-xs-center">We have had to disable <strong>features</strong> please consider upgrading your<a href="http://caniuse.com/#feat=eventsource"> browser</a>!</p></div>'
	document.getElementById("gong").innerHTML = nosse;
}

var sseSource = undefined;

function gongClicked(event) {
	var sound = $( document.getElementById("sound") );
	if (event.target.checked) {
    	sseSource = getGongSSE();
    	$.cookie("gong", 'open', { expires: 1 });
		sound.removeAttr('hidden');
    } else {
    	if (sseSource != undefined) {
	        sseSource.close();
        }
        $.removeCookie('gong');
		sound.attr('hidden', '');
    }
}

$(function gongStart() {
	var gongbutton = $( document.getElementById("gongbutton") );
	// Check if gongbutton exists
	if (gongbutton) {
		// Check if browser does not support SSE
		if (typeof window.EventSource === "undefined") {
			// If not remove button and warn
			noSSE();
			gongbutton.closest('li').remove();
		} else {
			// Setup Gong Button and Check Cookie
			gongbutton.on("click", gongClicked);
			if ($.cookie('gong')) {
				gongbutton.click();
		}
	}
	}
});
