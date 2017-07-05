'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.alarm = (function () {
	let sse = waitlist.sse;
	let cached_data = {
		"groups": new Map(),
		"waitlists": new Map()
	};

	// callback needs to take 1 parameter data, which is the response
	function getWaitlistData(callback) {
		if (typeof wlid === 'undefined') {
			return null;
		}
		$.getJSON(getMetaData('api-waitlists'), callback);
	}

	function getGroupsData(callback) {
		$.getJSON(getMetaData('api-groups'), callback);
	}

	function initiateGroupsData(data) {
		for(let group of data) {
			cached_data["groups"][group.groupID] = group;
		}
		// now load all waitlists
		getWaitlistData(initiateWaitlistsData);
	}

	function initiateWaitlistsData(data) {
		for(let waitlist of data) {
			cached_data["waitlists"][waitlist.id] = waitlist;
		}
	}

	function getEnabledGroupIds() {
		let enabled_group_ids = [];
		for (let vkpair of cached_data.groups) {
			if (kvpair[1].enabled) {
				enabled_group_ids.push(kvpair[0]);
			}
		}
		return enabled_group_ids;
	}

	function getNumberForWaitlistById(waitlistId) {
		return cached_data.waitlists[waitlistId].entryCount;
	}

	function getNumbersForGroupByType(groupId, typeName) {
		let fieldName = typeName+"wlID";
		let waitlistId = cached_data.groups[groupId][fieldName];
		if (waitlistId === null) { // this group does not have this waitlist type
			return 0;
		}
		return getNumberForWaitlistById(waitlistId)
	}

	function getDPSNumbersForGroup(groupId) {
		return getNumbersForGroupByType(groupId, "dps");
	}

	function getSniperNumbersForGroup(groupId) {
		return getNumbersForGroupByType(groupId, "sniper")
	}

	function  getLogiNumbersForGroup(groupId) {
		return getNumbersForGroupByType(groupId, "logi");
	}

	function getOtherNumbersForGroup(groupId) {
		return getNumbersForGroupByType(groupId, "other");
	}

	function init() {
		// we can just call this every 5min to update stats
		// or we use sse to update
		getGroupsData(initiateFromGroupData);
	}
	$(document).ready(init);
	return {};
})();