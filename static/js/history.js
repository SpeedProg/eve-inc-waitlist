'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.history.comphistory = (function() {

	var getMetaData = waitlist.base.getMetaData;
	var getStamp = waitlist.history.base.getLastRefresh;
	var setStamp = waitlist.history.base.setLastRefresh;
	var createHistoryEntryDOM = waitlist.history.base.createHistoryEntryDOM;

	function refresh() {
		$.getJSON(getMetaData('api-history-changed') + "?last=" + getStamp(),
			function(data) {
				var hbody = $('#historybody');
				for (var i = 0; i < data.history.length; i++) {
					var hEntryDOM = createHistoryEntryDOM(data.history[i]);
					hbody.trigger("hentry-adding", hEntryDOM);
					hbody.prepend(hEntryDOM);
					hbody.trigger("hentry-added", hEntryDOM);
				}
				if (data.history.length > 0) {
					setStamp((new Date(Date
						.parse(data.history[data.history.length - 1].time)))
						.getTime());
				}
			});
	}
	function init() {
		refresh();
		setInterval(refresh, 10000);
	}

	$(document).ready(init);

	// we don't wanna export anything
	return {};
}());
