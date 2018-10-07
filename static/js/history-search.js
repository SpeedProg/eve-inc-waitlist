'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.history.historysearch = (function() {

	var getMetaData = waitlist.base.getMetaData;
	var createHistoryEntryDOM = waitlist.history.base.createHistoryEntryDOM;

	function loadData(sources, targets, actions, startdate, starttime, enddate, endtime) {
		var data = {};
		if (sources !== null) {
			data.accs = sources;
		}
		if (targets !== null) {
			data.chars = targets;
		}
		if (actions !== null) {
			data.actions = actions;
		}
		data.startdate = startdate;
		data.starttime = starttime;
		data.enddate = enddate;
		data.endtime = endtime;
		$.getJSON(getMetaData('api-history-search'), data, function(data) {
			var hbody = $('#historybody');
			hbody.empty();
			if (data.history.length <= 0) {
				hbody.append('<td cospan="5">'+$.i18n('wl-no-result-found')+'</td>');
				return;
			}
			for (var i = 0; i < data.history.length; i++) {
				var hEntryDOM = createHistoryEntryDOM(data.history[i]);
				hbody.trigger("hentry-adding", hEntryDOM);
				hbody.prepend(hEntryDOM);
				hbody.trigger("hentry-added", hEntryDOM);
			}
			if (data.history.length > 0) {
				data.laststamp = (new Date(Date
				    .parse(data.history[data.history.length - 1].time)))
				    .getTime();
			}
		});
	}

	function search_click_handler() {
		var sources = $('#input-sources').val();
		var targets = $('#input-targets').val();
		var actions = $('#input-actions').val();
		if (actions !== null) {
			actions = actions.join('|');
		}
		let startDate = $('#startDate').val();
		let startTime = $('#startTime').val();
		let endDate = $('#endDate').val();
		let endTime = $('#endTime').val();

		if (sources === "") {
			sources = null;
		}
		if (targets === "") {
			targets = null;
		}
		if (actions === "") {
			actions = null;
		}
		if (startDate === "" || startTime === "") {
			return;
		}
		if (endDate === "" || endTime === "") {
			return;
		}

		loadData(sources, targets, actions, startDate, startTime, endDate, endTime);
	}

	function init() {
		$('#search').on('click', search_click_handler);
		Date.prototype.toDateInputValue = (function() {
			var local = new Date(this);
			local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
			return local.toJSON().slice(0,10);
		});
		let nowValue = new Date();
		document.getElementById('startDate').valueAsDate = nowValue;
		document.getElementById('startTime').valueAsDate = nowValue;
		document.getElementById('endDate').valueAsDate = nowValue;
		document.getElementById('endTime').valueAsDate = nowValue;
	}

	$(document).ready(init);

	// we need nothing to be externally reachable
	return {};
}());