'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.gong = (function() {

	const addListener = waitlist.sse.addEventListener;
	const gongbutton = document.getElementById("gongbutton");
	const sound = document.getElementById("sound");

	function playGong() {
		if (gongbutton.checked) {
			sound.currentTime = 0;
			sound.play();
		}
	}

	function gongClicked() {
		if (gongbutton.checked) {
			sound.removeAttribute("hidden");
			sound.volume = 0.5;
			sessionStorage.setItem('gong', 'open');
		} else {
			sound.setAttribute("hidden", "");
			sound.pause();
			sessionStorage.removeItem('gong');
		}
	}

	function gongSetup() {
		// Check if browser supports event source
		if (!!window.EventSource && gongbutton) {
			// Add click handler & add eventlistener & check Session Storage
			addListener("invite-send", playGong);
			gongbutton.addEventListener("click", gongClicked);
			if (sessionStorage.getItem('gong')) {
				gongbutton.checked = true;
				gongClicked();
			}
		} else {
			// If not remove button
			if (gongbutton) {
				gongbutton.parentNode.parentNode.remove();
			}
		}
	}

	$(document).ready(gongSetup);
	return {};
})();