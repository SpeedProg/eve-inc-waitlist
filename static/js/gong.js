'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.gong = (function(){

	function playGong() {
		var sound = document.getElementById('sound');
		sound.currentTime = 0;
		sound.play();
	}

	function gongEnabled() {
		 return document.getElementById("gongbutton").checked;
	}

	function gongClicked() {
		var sound = document.getElementById("sound");
		if (document.getElementById("gongbutton").checked) {
			sound.removeAttribute("hidden");
			sound.volume = 0.5;
			sessionStorage.setItem('gong', 'open');
		} else {
			sound.setAttribute("hidden", "");
			sessionStorage.removeItem('gong');
		}
	}

	function gongSetup() {
		var gongbutton = document.getElementById("gongbutton");
		// Check if browser supports event source
		if (!!window.EventSource && gongbutton) {
			// Add click handler and check Session Storage
			gongbutton.addEventListener("click", gongClicked);
			if (sessionStorage.getItem('gong')) {
				gongbutton.checked = true;
				gongClicked();
			}
		} else {
			// If not remove button
			gongbutton.parentNode.parentNode.remove();
		}
	}
	
	document.addEventListener('DOMContentLoaded', gongSetup);
	
	return {
		playGong: playGong,
		isGongEnabled: gongEnabled
	};
})();