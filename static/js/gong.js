'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.gong = (function() {

	const getMetaData = waitlist.base.getMetaData;
	const displayMessage = waitlist.base.displayMessage;
	const addListener = waitlist.sse.addEventListener;
	const storage = localStorage;
	const gongVersion = "1";
	var gongbutton, sound, gongLoaded, gongAlert, gongURL;

	function playGong() {
		if (gongbutton.checked) {
			sound.currentTime = 0;
			sound.play();
		}
	}

	function gongClicked() {
		if (gongbutton.checked) {
			if (gongAlert === "y") {
				removeGongAlert();
			}
			sound.removeAttribute("hidden");
			storage["gong"] = "open";
		} else {
			sound.setAttribute("hidden", "");
			sound.pause();
			storage.removeItem("gong");
		}
	}

	function removeGongAlert() {
		$("#gong-alert").remove();
	}

	function disableGong() {
		gongbutton.checked = false;
		gongClicked();
		removeGongAlert();
		document.getElementById("gong").remove();
	}

	function gongSetup() {
		// Setup SSE invite-send event
		addListener("invite-send", playGong);
		gongbutton.addEventListener("click", gongClicked);
		sound.volume = 0.5;
		// Checks storage for gong info if not found alert to please enable notification
		if (storage["gong"]) {
			gongbutton.checked = true;
			gongClicked();
		} else {
			displayMessage("To get informed when you are invited please enable browser notifications in the top right.", "info", false, "gong-alert");
			gongAlert = "y";
		}
	}

	function init() {
		gongbutton = document.getElementById("gongbutton");
		sound = document.getElementById("sound");
		gongURL = getMetaData("audio");
		if (gongbutton) {
			if (window.EventSource) {
				gongSetup();
			} else {
				disableGong();
			}
		}
	}

	$(document).ready(init);
	return {
	disableGong: disableGong
	};
})();