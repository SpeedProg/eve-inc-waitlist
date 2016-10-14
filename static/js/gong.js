function playGong() {
	var sound = document.getElementById('sound');
	sound.volume = 0.5;
	sound.currentTime = 0;
	sound.play();
}

function gongEnabled() {
	 return $('#gongbutton').prop("checked")
}

function gongClicked(event) {
	var sound = $( document.getElementById("sound") );
	if (event.target.checked) {
    	$.cookie("gong", 'open', { expires: 1 });
		sound.removeAttr('hidden');
    } else {
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
