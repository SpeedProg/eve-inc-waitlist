/*
 * Set up click handlers on fittings
 */
 function setupDNA() {
	$(document).on("click", ".fit-link", function(event){
		var dna = this.getAttribute('data-dna');
		IGBW.showFitting(dna);
	 });
	$(document).on("click", ".booby-link", function(event){
		 window.open("https://en.wikipedia.org/wiki/Booby", "_blank");
	 });
}

$(document).ready(function () {
	setupDNA();
});