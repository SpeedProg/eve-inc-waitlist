'use strict';
if (!waitlist) {
	var waitlist = {};
}

waitlist.fleetview = (function(){
	let exports = {}; // going to hold our exports
	
	let getMetaData = waitlist.base.getMetaData;
	// holds the index database we are using
	let db;

	function setupDB() {
	// setup indexdb to cache charnames / ship types
		const request = indexedDB.open("eve-api-cache", 2);
	// setup handler to ask user why it failed :>
		request.onerror = function (event) {
			alert($.i18n("wl-fleetview-error-indexdb"));
		};
	// if we succeed opening it lets register a general error handler
		request.onsuccess = function (event) {
			db = event.target.result;
			db.onerror = function (event) {
				// Generic error handler for all errors targeted at this database's
				// requests!
				alert($.i18n('wl-fleetview-error-db', event.target.errorCode));
			};
			// aright we are done, lets call the next code
			initializeSite();
		};
	// handler for setting up our object stores if this is the first time opening it
		request.onupgradeneeded = function (event) {
			const db = event.target.result;
			console.log("Creating IndexDB ObjectStores");
			// Create an objectStore for this database
			const characterStore = db.createObjectStore("characters", {keyPath: "characterID"});
			const shipsStore = db.createObjectStore("ships", {keyPath: "id"});
			shipsStore.createIndex('id', 'id', { unique: true });
		};
	}

	function initializeSite() {
		const fleetSelect = $('#fleetSelect');
		fleetSelect.on("change", handleFleetSelected);
		// load initial fleet if the browser set a value
		if (fleetSelect.val() != 'None') {
			$.get(getMetaData('fleet-spy').replace('-1', fleetSelect.val()), function(data, status, xhr) {
				handleData(data);
			});
		}
	}

	function handleData(data) {
		const squadMap = [];
		for(let charId in data) {
			console.log("creating squadMap ", charId);
			let charObj = data[charId];
			// if we have no map for the quad yet, create one
			if (!(charObj['squad_id'] in squadMap)) {
				console.log("Creating map for squad with id ", charObj['squad_id']);
				squadMap[charObj['squad_id']]= {};
			}
			// add the char to the squad
			squadMap[charObj['squad_id']][charId] = charObj;
		}
		// now convert it to arrays:
		const tableData = []; // [0] = th row
		const columnArray = [];
		let columnCount = 0;
		let rowCount = 0;
		for (let squadID in squadMap) {
			columnArray.push(squadID);
			columnCount++;
		}
		console.log("Counted Squads", columnCount);
		tableData.push(columnArray);

		const squadsArray = [];
		// convert the squads to array
		for (let idx in columnArray) {
			console.log("Going over Squad ", idx);
			let squadID = columnArray[idx];
			console.log("SquadID", squadID);
			let squad = [];
			for (let charId in squadMap[squadID]) {
				squad.push(squadMap[squadID][charId]);
			}
			console.log("Adding squad ", squad);
			squadsArray.push(squad);
		}
		let maxLength = 0;
		for(let idx in squadsArray) {
			if (squadsArray[idx].length > maxLength) {
				maxLength = squadsArray[idx].length;
			}
		}
		console.log("MaxLength ", maxLength);
		for(let s=0; s<maxLength; s++) {
			console.log("s ", s);
			const rowArray = [];
			for(let sidx=0; sidx < columnCount; sidx++) {
				if (squadsArray[sidx].length > s) {
					rowArray.push(squadsArray[sidx][s]);
				} else {
					rowArray.push(null);
				}
			}
			tableData.push(rowArray);
		}
		console.log("Row Array ", tableData);

		renderTable(tableData);
	}

	function renderTable(tableData) {
		let headTr = $('#fleet-list-header-tr');
		headTr.empty();
		tableData[0].forEach(function (element) {
			let th = $.parseHTML(`<th>${element}</th>`);
			headTr.append(th);
		});
		let body = $('#fleet-list-body');
		body.empty();
		for(let rowIdx=1; rowIdx < tableData.length; rowIdx++) {
			let html = "<tr>";
			tableData[rowIdx].forEach(function (element) {
				let data = element;
				if (data === null) {
					html += "<td>-</td>";
				} else {
					let timeStr = data['join_time'];
					let timeObj = Date.parse(timeStr);
					let minutes = Math.floor((((new Date()) - timeObj) / 1000) / 60);
					// lets try and resolve the character id to a name
					html += `<td data-charid="${data['character_id']}" data-shiptype="${data['ship_type_id']}">${data['ship_type_id']} - ${data['character_id']} - ${minutes}m</td>`;
				}
			});
			html += "</tr>";
			console.log("Adding row", html);
			body.append($.parseHTML(html));
		}

		// build a shipID map
		let shipIDs = {};
		for(let rowIdx=1; rowIdx < tableData.length; rowIdx++) {
			tableData[rowIdx].forEach(function (element) {
				if (element == null) {
					return;
				}
				if (!(element['ship_type_id'] in shipIDs)) {
					shipIDs[element['ship_type_id']] = true;
				}
				requestCharacterIDTransformation(element['character_id']);
			});
		}
		// make a array out of the ids
		let shipIDArray = [];
		for( let shipID in shipIDs) {
			shipIDArray.push(Number(shipID));
		}
		requestShipIDTransformations(shipIDArray);
	}

	function replaceCharacterID(charID, name) {
			let node = $('td[data-charid="'+charID+'"]');
			let text = node.text();
			let parts = text.split(' - ', 3);
			let newText = parts[0] + ' - ' + name + ' - ' + parts[2];
			node.text(newText);
	}

	function requestShipIDTransformations(shipIDs) {
		let results = [];
		const notFoundIds = [];
		function cmp(a, b) {
			if (a < b) { return -1;}
			if (a > b) { return 1;}
			return 0;
		}
		const sortedIds = shipIDs.sort(cmp);
		let index = db.transaction('ships', 'readonly').objectStore('ships').index('id');
		let cursor = index.openCursor();

		function doOutstandingIdRequest(ids) {
			// there is none lets just do the replace
			if (results.length > 0) {
				replaceShipTypes(results);
			}
			if (notFoundIds.length > 0) {
				const promis = getShipInfo(notFoundIds);
				promis.then(function(value) {
					value.body.forEach(function (element) {
						const nameData = element;
						const shipStore = db.transaction('ships', 'readwrite').objectStore('ships');
						shipStore.add(nameData).onsuccess = function (event) {
							console.log('added ship');
							console.log('event');
						};
					});
					replaceShipTypes(value);
				});
			}
		}

		function replaceShipTypes(data) {
			data.forEach(function (element) {
				let nodes = $('td[data-shiptype="' + element.id + '"]');
				nodes.each(function(idx, n){
					let node = $(n);
					let text = node.text();
					let parts = text.split(' - ', 3);
					let newText = element.name + ' - ' + parts[1] + ' - ' + parts[2];
					node.text(newText);
				});
			});
		}

		cursor.onsuccess = function (event) {
			let cursor = event.target.result;
			if (cursor) {
				let data = cursor.value;
				if (sortedIds.length > 0 && data.id < sortedIds[0]) {
					cursor.continue(sortedIds[0]);
					return;
				}
				while (sortedIds.length > 0 && data.id != sortedIds[0]) {
					notFoundIds.push(sortedIds[0]);
					sortedIds.shift();
				}

				// we have more
				if (sortedIds.length > 0) {
					// we found a value
					results.push(cursor.value);
					sortedIds.shift();
					if (sortedIds.length > 0) {
						cursor.continue(sortedIds[0]);
					} else {
						doOutstandingIdRequest(notFoundIds);
					}
				} else {
					// we are done w/o reaching the end of the cursor
					doOutstandingIdRequest(notFoundIds);
				}
			} else {
				// we are done by reaching the end of the cursor
				sortedIds.forEach(function (element) {
					notFoundIds.push(element);
				});
				doOutstandingIdRequest(notFoundIds);
			}
		}
	}

	function requestCharacterIDTransformation(charID) {
		let objectStore = db.transaction('characters', 'readwrite').objectStore('characters');
		let request = objectStore.get(charID);
		request.onsuccess = function(event) {
			if (!('result' in event.target) || event.target.result === undefined) {
				const promis = getCharacterInfo(charID);
				promis.then(function(value) {
					const character = value.body;
					character.characterID = charID;
					const characterStore = db.transaction('characters', 'readwrite').objectStore('characters');
					characterStore.add(character).onsuccess = function (event) {
						console.log('added');
						console.log('event');
					};
					replaceCharacterID(character.characterID, character.name);
				});
				return;
			}
			console.log(charID+' found in indexdb');
			let charName = event.target.result.name;
			let characterID = event.target.result.characterID;
			replaceCharacterID(characterID, charName);
		};

		request.onerror = function (event) {
			console.log('error getting '+charID+' from indexdb');
		}
	}

	function handleFleetSelected(event) {
		const fleetid = event.target.value;
		if (fleetid != 'None') {
			$.get(getMetaData('fleet-spy').replace('-1', fleetid), function(data, status, xhr) {
				handleData(data);
			});
		}
	}

	function getShipInfo(shipIDs) {
		return exports.esi_client.apis.Universe.post_universe_names({ids: shipIDs}, {responseContentType: 'application/json'});
	}

	function getCharacterInfo(characterID) {
		return exports.esi_client.apis.Character.get_characters_character_id({character_id: characterID}, {responseContentType: 'application/json'});
	}

	$(document).ready(function() {
		new SwaggerClient(getMetaData('local-esi-json'))
		.then((client) => {
			exports.esi_client = client;
		})
		.catch((event) => {
			console.log("SwaggerError");
			console.log(event);
			}
		);
		setupDB();
	});
	return exports;
})();