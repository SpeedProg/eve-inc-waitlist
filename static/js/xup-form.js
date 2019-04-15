'use strict';

$(document).ready(function() {
	var calbsgrp = document.getElementById('grp-cbslvl');
	var logilvlgrp = document.getElementById('grp-logilvl');
	var logi_select = document.getElementById('logi');
	var cbs_select = document.getElementById('cbs');
	var resist_regex = /\[Rattlesnake|fitting:17918|\[Scorpion Navy Issue|fitting:3230|\[Rokh|fitting:24688/;
	var logi_regex = /fitting:11985|\[Basilisk|fitting:11978|\[Scimitar/;
	var checkExtra = function(e) {
		var textarea = $(e.target);
		var currentText = textarea.val();
		if (resist_regex.test(currentText)) {
			$(calbsgrp).show();
			cbs_select.required=true;
		} else {
			$(calbsgrp).hide();
			cbs_select.required=false;
		}
		if (logi_regex.test(currentText)) {
			$(logilvlgrp).show();
			logi_select.required=true;
		} else {
			$(logilvlgrp).hide();
			logi_select.required=false;
		}
		
	}
	var fakeEv = {target: document.getElementById('fittings')};
	fakeEv.target.addEventListener('input', checkExtra, false);
	checkExtra(fakeEv);
});
