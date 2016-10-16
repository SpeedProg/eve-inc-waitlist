'use strict';
/*
 * Set up click handlers on fittings
 */
function booby() {
    $(document).on("click", ".booby-link", function(){
	    window.open("https://en.wikipedia.org/wiki/Booby", "_blank");
	});
}

document.addEventListener('DOMContentLoaded', booby);
