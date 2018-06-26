'use strict';

if (!waitlist) {
	var waitlist = {};
}

waitlist.alarm = (function () {
	// lets import stuff we need from base
	let getMetaData = waitlist.base.getMetaData
	// update listener should be functions that take 1 argument!
	// the argument provided will be this cache
	// they will get called after the cache was updated
	let cached_data = {
		"groups": new Map(),
		"waitlists": new Map(),
		"updateListener": [],
		"addUpdateListener": function (listener) {
			this.updateListener.push(listener)
		},
		"callUpdateListener": function () {
			for (let listener of this.updateListener) {
				listener(this);
			}
		}
	};

	function clearCache() {
		cached_data["groups"].clear();
		cached_data["waitlists"].clear();
	}

	// callback needs to take 1 parameter data, which is the response
	function getWaitlistData(callback) {
		$.getJSON(getMetaData('api-waitlists'), callback);
	}

	function getGroupsData(callback) {
		$.getJSON(getMetaData('api-groups'), callback);
	}

	function initiateFromGroupsData(data) {
		// clearn the cache, then update it
		clearCache();
		for(let group of data) {
			cached_data.groups.set(group.groupID, group);
		}
		// now load all waitlists
		getWaitlistData(initiateWaitlistsData);
	}



	function initiateWaitlistsData(data) {
		for(let waitlist of data) {
			cached_data.waitlists.set(waitlist.id, waitlist);
		}
		// we finished updating the cache here, so lets announce it
		cached_data.callUpdateListener();
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
		let count = cached_data.waitlists.get(waitlistId).entryCount;
		// if it is not a number (some one got some other data in here) return 0
		// this prevents injections later
		if (isNaN(count)) {
			return 0;
		}
		return count;
	}

	function getNumbersForGroupByType(groupId, typeName) {
		let fieldName = typeName+"wlID";
		let waitlistId = cached_data.groups.get(groupId)[fieldName];
		if (waitlistId === null) { // this group does not have this waitlist type
			return 0;
		}
		return getNumberForWaitlistById(waitlistId)
	}

	function getDPSCount(groupId) {
		return getNumbersForGroupByType(groupId, "dps");
	}

	function getSniperCount(groupId) {
		return getNumbersForGroupByType(groupId, "sniper")
	}

	function  getLogiCount(groupId) {
		return getNumbersForGroupByType(groupId, "logi");
	}

	function getOtherCount(groupId) {
		return getNumbersForGroupByType(groupId, "other");
	}
	
	function getXupCount(groupId) {
		return getNumbersForGroupByType(groupId, "xup");
	}

	function updateCache() {
		getGroupsData(initiateFromGroupsData);
	}

	function onCacheUpdate(cache) {
		// update table
		// wl-stats-body
		let tableBody = $('#wl-stats-body');
		tableBody.empty();
		for (let group of cache.groups.values()) {
			//  we need to inser ${group.groupName} with a set function to prevent HTML injection
			// all the others should return numbers only!
			let rowNode = $.parseHTML(`<tr><th scope="row"></th>
<td>${group.enabled}</td>
<td>${getXupCount(group.groupID)}</td>
<td>${getLogiCount(group.groupID)}</td>
<td>${getDPSCount(group.groupID)}</td>
<td>${getSniperCount(group.groupID)}</td>
<td>${getOtherCount(group.groupID)}</td>
</tr>`);
			//  set this way to prevent inserting any injections
			rowNode[0].firstElementChild.textContent = group.groupDisplayName;
			tableBody.append(rowNode);
		}

		addPossibleExpressionTargets(cache);
		let expressionMap = getExpressionMap();
		let parser = new exprEval.Parser();
		for (let group of cache.groups.values()) {
			if (!expressionMap.has(group.groupID)) {
				continue; // skip this group
			}
			let exprStr = expressionMap.get(group.groupID);
			if (exprStr === "") {
				continue;
			}
			let expr = parser.parse(exprStr);
			let result = expr.evaluate({
				'xup': getXupCount(group.groupID),
				'logi': getLogiCount(group.groupID),
				'dps': getDPSCount(group.groupID),
				'sniper': getSniperCount(group.groupID),
				'other': getOtherCount(group.groupID),
				'open': group.enabled
			});
			if (result) {
				triggerAlarm(group);
			}
		}
	}

	function addPossibleExpressionTargets(cache) {
		let exprTargetSelect = document.getElementById('expr-target-select');
		// remove all options
		for (let idx = 0; idx < exprTargetSelect.length; idx++) {
			exprTargetSelect.remove(idx);
		}
		// add all options
		for (let group of cache.groups.values()) {
			let option = document.createElement("option");
			option.text = group.groupDisplayName;
			option.value = group.groupID;
			exprTargetSelect.add(option);
		}
	}

	function addAlarmExpression(event) {
		let button = event.source;
		let exprTargetSelect = document.getElementById('expr-target-select');
		// nothing selected
		if (exprTargetSelect.selectedIndex < 0) {
			return;
		}
		let option = exprTargetSelect.options[exprTargetSelect.selectedIndex];
		let groupID = option.value;
		let groupName = option.text;

		let alarmExprTableBody = document.getElementById('alarm-expr-body');
		let foundAlready = false;
		for(let childTr of alarmExprTableBody.childNodes) {
			if (childTr.nodeType !== Node.ELEMENT_NODE || childTr.tagName !== "TR") {
				continue;
			}
			if (childTr.getAttribute("data-groupid") === groupID) {
				foundAlready = true;
				break;
			}
		}
		if (foundAlready) {
			return;
		}

		let alarmExpressionRow = $.parseHTML(`<tr data-groupid="${groupID}">
<td></td>
<td><input class="w-100" type="text" placeholder="(xup == 0 and logi < 2) or (xup == 2 and dps <= 5)"></td>
<td><input type="checkbox"></td></tr>`)[0];
		// set it like this to avoid injections
		alarmExpressionRow.setAttribute("data-groupname", groupName);
		alarmExpressionRow.firstElementChild.textContent = groupName;
		alarmExprTableBody.appendChild(alarmExpressionRow);
	}

	/**
	 * Get a map containing groupids apped to the entered expressions
	 * @returns {Map} containing groupid as key and entered expression as value
	 */
	function getExpressionMap() {
		const expressionMap = new Map();
		let exprTableBody = document.getElementById('alarm-expr-body');
		let expressionRows = exprTableBody.getElementsByTagName("TR");
		for (let row of expressionRows) {
			// if it is not enabled skip it
			if (!row.getElementsByTagName("input")[1].checked) {
				continue;
			}
			let groupid = parseInt(row.getAttribute("data-groupid"));
			let expr = row.getElementsByTagName("input")[0].value;
			expressionMap.set(groupid, expr);
		}
		return expressionMap;
	}

	function triggerAlarm(group) {
		document.getElementById('alarm').play();
	}

	function init() {
		let exprAddButton = $('#expr-target-add');
		exprAddButton.on('click', addAlarmExpression);

		cached_data.addUpdateListener(onCacheUpdate);
		updateCache();
		// we can just call this every 5min to update stats
		// or we use sse to update

		// 30s == 30 000 ms
		setInterval(updateCache, 30000);
	}

	$(document).ready(init);
	return {};
})();