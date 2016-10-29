'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.history.historysearch = (function() {

	var getMetaData = waitlist.base.getMetaData();
	var createHistoryEntryDOM = waitlist.history.base.createHistoryEntryDOM;

	function loadData(sources, targets, actions, startdate, enddate) {
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
		data.start = startdate;
		data.end = enddate;
		$.getJSON(getMetaData('api-history-search'), data, function(data) {
			var hbody = $('#historybody');
			hbody.empty();
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
		var start = $('#startpicker > input').val();
		var end = $('#endpicker > input').val();

		if (sources === "") {
			sources = null;
		}
		if (targets === "") {
			targets = null;
		}
		if (actions === "") {
			actions = null;
		}
		if (start === "") {
			start = moment().subtract(1, 'day').format("YYYY/MM/DD HH:mm");
		}
		if (end === "") {
			end = moment().format("YYYY/MM/DD HH:mm");
		}

		loadData(sources, targets, actions, start, end);
	}

	function init() {
		$('#search').on('click', search_click_handler);
		$('#startpicker').datetimepicker({
			icons: {
				time: "fa fa-clock-o",
				date: "fa fa-calendar",
				up: "fa fa-arrow-up",
				down: "fa fa-arrow-down",
				previous: 'fa fa-chevron-left',
				next: 'fa fa-chevron-right',
				today: 'fa fa-calendar-o',
				clear: 'fa fa-trash',
				close: 'fa fa-times'
			},
			format: "YYYY/MM/DD HH:mm"
		});
		$('#endpicker').datetimepicker({
			useCurrent: false,
			icons: {
				time: "fa fa-clock-o",
				date: "fa fa-calendar",
				up: "fa fa-arrow-up",
				down: "fa fa-arrow-down",
				previous: 'fa fa-chevron-left',
				next: 'fa fa-chevron-right',
				today: 'fa fa-calendar-o',
				clear: 'fa fa-trash',
				close: 'fa fa-times'
			},
			format: "YYYY/MM/DD HH:mm"
		});
		$("#startpicker").on("dp.change", function(e) {
			$('#endpicker').data("DateTimePicker").minDate(e.date);
		});
		$("#endpicker").on("dp.change", function(e) {
			$('#startpicker').data("DateTimePicker").maxDate(e.date);
		});
	}

	$(document).ready(init);

	// we need nothing to be externally reachable
	return {};
}());