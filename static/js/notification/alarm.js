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

	function updateCache() {
		getGroupsData(initiateFromGroupsData);
	}

	function onCacheUpdate(cache) {
		// update table
		// wl-stats-body
		let tableBody = $('#wl-stats-body');
		let tableHeader = $('#wl-stats-body');
		let tableHeaderGroupNode = $('#wl-stats-group').copy();

		let listnameSet = Set();
		for(let group of cache.groups.values()) {
			for(let list of group.lists) {
				listnameSet.add(list.name);
			}
		}
		// we want to keep the order
		let listnameList = Array.from(listnameSet);

		let thNodes = [tableHeaderGroupNode];
		for(let listname of listnameList) {
			// we create them this way to prevent any html injections using names
			let thNode = document.createElement("th");
			thNode.textContent = listname;
			thNodes.append(thNode[0]);
		}

		tableHeader.empty();
		for(let node of thNodes) {
			tableHeader.append(node);
		}

		tableBody.empty();
		for (let group of cache.groups.values()) {
			//  we need to inser ${group.groupName} with a set function to prevent HTML injection
			// all the others should return numbers only!
			let rowNode = $(document.createElement("tr"));
			let rowThNode = $.parseHTML('<th scope="row"></th>');
			// set the text content to prevent injection
			rowThNode[0].textContent = group.groupDisplayName;
			rowNode.append($.parseHTML("<td>${group.enabled}</td>"));
			for(let listname of listnameList) {
				const sublist = group.lists.find(l => l.name == listname);
				const sublistcount = getNumberForWaitlistById(sublist.id);
				const tdNode = typeof sublistcount !== "undefined" ? document.createElement("td") : $.parseHTML(`<td>${sublistcount}</td>`);
				rowNode.append(tdNode)
			}
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

			const valueMap = new Map();
			for(let list of group.lists) {
				valueMap.set(list.name, getNumberForWaitlistById(list.id));
			}
			valueMap.set('open', group.enabled);
			let result = expr.evaluate(valueMap);
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

	function addAlarmExpression(_event) {
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

	function triggerAlarm(_group) {
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