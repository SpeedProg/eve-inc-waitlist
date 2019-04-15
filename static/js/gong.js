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
			if (gongLoaded !== true) {
				checkGongCache();
			}
			if (gongAlert === "y") {
				removeGongAlert();
			}
			sound.removeAttribute("hidden");
			storage.gong = "open";
		} else {
			sound.setAttribute("hidden", "");
			sound.pause();
			sound.currentTime = 0;
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
		if (storage.gong) {
			gongbutton.checked = true;
			gongClicked();
		} else {
			displayMessage($.i18n('wl-gong-info'), "info", false, "gong-alert");
			gongAlert = "y";
		}
	}
	
	function setGongSrc() {
		gongLoaded = true;
		var gongBlob = storage.gongFile;
		sound.setAttribute("src", gongBlob);
	}

	function getGong() {
		fetch(gongURL).then(function(response) {
			response.blob().then(function(blob) {
				var reader = new FileReader();
					reader.addEventListener("loadend", function() {
						storage.gongFile = reader.result.toString();
						storage.gongVersion = gongVersion;
						setGongSrc();
					});
				reader.readAsDataURL(blob);
			});
		});
	}

	function checkGongCache() {
		if (storage.gongVersion !== gongVersion || storage.gongFile === undefined) {
			getGong();
		} else {
			setGongSrc();
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