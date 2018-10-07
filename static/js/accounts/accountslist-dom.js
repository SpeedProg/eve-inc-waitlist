let swa_client = SwaggerClient(
	{
		url: "/spec/v1/swagger.json",
		requestInterceptor : function(req) {
			req.headers['X-CSRFToken'] = waitlist.base.getMetaData('csrf-token');
			return req;
		}
	}
);

class AccountRow {
	constructor(accountId, grid) {
		this.accountId = accountId;
		this.id = `account-${accountId}`
		this.element = document.getElementById(this.id);
		this.grid = grid;
	}
	
	set status(value) {
		this.setColumn('status', value)
		this.grid.refreshGrid();
	}
	
	get name() {
		return this.getColumn('account-name');
	}
	
	get defaultCharName() {
		return this.getColumn('current-character');
	}
	
	get rolesIdx() {
		return this.getColumnIdx('roles');
	}
	
	getColumnIdx(name) {
		return this.grid.getColumnIndex(name);

	}
	
	getColumn(name) {
		let data = this.grid.dataUnfiltered != null ? this.grid.dataUnfiltered : this.grid.data;
		// find the data row
		let rowdata = data.find(e => e.id == this.id);
		console.log("Get columnIdex for "+name);
		console.log(rowdata);
		console.log(this.grid);
		let columnIndex = this.grid.getColumnIndex(name);
		console.log('Got idx '+columnIndex+' for '+name);
		return rowdata.columns[columnIndex];
	}
	
	setColumn(name, value) {
		let griddata = this.grid.dataUnfiltered != null ? this.grid.dataUnfiltered : this.grid.data;
		// find the data row
		let rowdata = griddata.find(e => e.id == this.id);
		let columIndex = this.grid.getColumnIndex(name);
		rowdata.columns[columnIndex] = value;
	}
}

class AltEntry {
	constructor(account_id, character_id, character_name, can_change_link) {
		if (account_id instanceof HTMLElement) {
			setDataFromHtml(account_id);
		} else {
			this.account_id = account_id;
			this.character_id = character_id;
			this.character_name = character_name;
			this.can_change_link = can_change_link;
			this.html = undefined;
			this.remove_button = undefined;
			this.alts_list = undefined;
		}
	}

	setDataDirect(account_id, character_id, character_name, can_change_link) {
		this.account_id = account_id;
		this.character_id = character_id;
		this.character_name = character_name;
		this.can_change_link = can_change_link;
	}

	setDataFromHtml(element) {
		if (!(element instanceof HTMLElement) || element.tagName !== 'SPAN') {
			throw new Error('Not a HTMLElement of tagName SPAN.');
		}

		this.html = element;
		let span_id = element.getAttribute('id');
		let span_id_parts = span_id.split('-');
		if (span_id_parts[0] !== 'altentry') {
			throw new Error("Given element is not an AltEntry");
		}
		let account_id = Number(span_id_parts[1]);
		let character_id = Number(span_id_parts[2]);
		let character_name = "";
		if (element.childNodes.length > 1) {
			this.can_change_link = true;
			character_name = element.childNodes[1].nodeValue;
		}
		else {
			this.can_change_link = false;
			character_name = element.childNodes[0].nodeValue;
		}
		this.account_id = account_id;
		this.character_name = character_name;
		this.character_id = character_id;
	}

	setAltsList(alts_list) {
		if (this.alts_list !== undefined) {
			this.alts_list.removeAltEntryByCharacterId(this.character_id);
		}
		this.alts_list = alts_list;
	}

	get element() {
		if (this.html === undefined) {
			this.html = this.createHtml();
		}
		return this.html;
	}

	remove_alt_button_handler(event) {
		let alt_entry = this;
		console.log(`Removing characterId=${this.character_id} from accountId=${this.account_id}`);
		swa_client.then(
			function(client) {
				client.apis.Accounts.delete_accounts_account_id({'account_id': alt_entry.account_id,
					'character_id': alt_entry.character_id,
					'requestInterceptor':
						function(req) {
						req.headers['X-CSRFToken'] = waitlist.base.getMetaData('csrf-token');
						return req;
					}
				}).then(
					function(event) {
						alt_entry.alts_list.removeAltEntryByCharacterId(alt_entry.character_id);
						waitlist.base.displayMessage("Alt removed", "success");
					}
				).catch(
					function(event) {
						waitlist.base.displayMessage(`Failed to remove alt: ${event.obj.error}`, "danger");
					}
				);
			}
		);
	}

	createHtml() {
		let alt_container = document.createElement('span');
		alt_container.setAttribute('id', `altentry-${this.account_id}-${this.character_id}`);
		alt_container.setAttribute('class', 'mr-2');
		if (this.can_change_link) {
			let remove_button = document.createElement('i');
			remove_button.setAttribute('class', 'fa fa-remove text-danger');
			remove_button.addEventListener('click', this.remove_alt_button_handler.bind(this));
			this.remove_button = remove_button;
			alt_container.appendChild(remove_button);
		}
		let nameNode = document.createTextNode(this.character_name);
		alt_container.appendChild(nameNode);
		return alt_container;
	}
}

class AltsList {
	constructor(account_id, can_change_link) {
		if (account_id instanceof HTMLElement){
			setDataFromHtml(account_id);
		} else {
			this.account_id = account_id;
			this.can_change_link = can_change_link;
			this.alt_entries = [];
			this.html = undefined;
			this.add_button = undefined;
		}
	}

	setDataFromHtml(element) {
		if (!(element instanceof HTMLElement) || element.tagName !== "DIV") {
			throw new Error("Not a HTMLElement of tagName DIV.");
		}
		let id_string = element.getAttribute('id');
		let id_parts = id_string.split('-');
		if (id_parts[0] !== "altslist") {
			throw new Error("Element is not an altslist");
		}

		this.html = element;

		this.account_id = Number(id_parts[1]);

		if (element.lastChild !== null &&
			element.lastChild.tagName == 'I' &&
			element.lastChild.getAttribute('data-action') == 'addAlt') {
			this.can_change_link = true;
			this.add_button = element.lastChild;
		} else {
			this.can_change_link = false;
		}

		for(let child of element.childNodes) {
			if (child.tagName === 'SPAN') {
				let alt_entry = new AltEntry(child);
				this.alt_entries.push(alt_entry);
			}
		}

	}

	setDataDirect(account_id, can_change_link, alt_entries) {
		this.account_id = account_id;
		this.can_change_link = can_change_link;
		if (alt_entries !== undefined) {
			for(let alt_entry of alt_entries) {
				addAltEntry(alt_entry);
			}
		}
	}

	addAltByData(character_id, character_name) {
		let alt_entry = new AltEntry(this.account_id, character_id, character_name, this.can_change_link);
		alt_entry.setAltsList(this);
		this.alt_entries.push(alt_entry);
		this.addAltEntryToElementIfNeeded(alt_entry);
	}

	addAltEntry(entry) {
		entry.setAltsList(this);
		this.alt_entries.push(entry);
		this.addAltEntryToElementIfNeeded(entry);
	}

	addAltEntryToElementIfNeeded(alt_entry) {
		if (this.html !== undefined) {
			if (this.can_change_link) {
				this.html.insertBefore(alt_entry.element, this.add_button)
			} else {
				this.html.appendChild(alt_entry.element);
			}
		}
	}

	removeAltEntryFromElementIfNeeded(alt_entry) {
		if (this.html !== undefined) {
			alt_entry.element.remove();
		}
	}

	removeAltEntryByCharacterId(character_id) {
		let alt_entry = this.getAltEntryByCharacterId(character_id);
		if (alt_entry !== null) {
			let alt_entry_idx = this.alt_entries.indexOf(alt_entry);
			this.alt_entries.splice(alt_entry_idx, 1);
			this.removeAltEntryFromElementIfNeeded(alt_entry);
		}
	}

	getAltEntryByCharacterId(character_id) {
		for(let alt_entry of this.alt_entries) {
			if (alt_entry.character_id === character_id) {
				return alt_entry;
			}
		}
		return null;
	}

	get element() {
		if (this.html === undefined) {
			this.html = this.createHtml();
		}
		return this.html;
	}

	add_button_handler(event) {
		let alts_list = this;
		swa_client.then(function(client){
			let account_id = alts_list.account_id;

			let input_field = document.createElement('input');
			input_field.setAttribute('type', 'text');
			input_field.setAttribute('class', 'form-control');
			input_field.setAttribute('placeholder', $.i18n('wl-add-alt-placehonder'));

			alts_list.element.appendChild(input_field);
			input_field = $(input_field);

			input_field.on('keyup', function(e) {
				if(e.keyCode == 13) { // enter
					let char_name = e.currentTarget.value;
					e.currentTarget.value = $.i18n('wl-please-wait');
					client.apis.Accounts.post_accounts_account_id({'account_id': account_id,
						'character_identifier': {'character_name': char_name}})
						.then(function(event) {
							waitlist.base.displayMessage($.i18n('wl-alt-added'), "success");
							input_field.remove();
							alts_list.addAltByData(event.obj.character_id, event.obj.character_name);
						})
						.catch(function(event) {
							if (typeof(event.response) !== "undefined" &&
								typeof(event.response.obj) !== "undefined" &&
								typeof(event.response.obj.error) !== "undefined"){
								waitlist.base.displayMessage($.i18n('wl-add-alt-failed', ' :' + event.response.obj.error), "danger");
							} else {
								waitlist.base.displayMessage($.i18n('wl-add-alt-failed', ''), "danger");
							}
							input_field.remove();
						});
				} else if (e.keyCode == 27) { // esc remove input
					input_field.remove();
				}
			});

		}).catch(function(event) {
			console.log("SwaggerError");
			console.log(event);
		});
	}

	remove_alt_button_handler(event) {

	}

	createHtml() {
		let alts_list = document.createElement('div');
		alts_list.setAttribute('id', 'altslist-'+this.account_id);

		for(let alt_entry of this.alt_entries) {
			alts_list.appendChild(alt_entry.element);
		}

		if (this.can_change_link) {
			this.add_button = document.createElement("i");
			this.add_button.setAttribute("class", "fa fa-plus-square text-success");
			this.add_button.setAttribute("data-account-id", this.account_id);
			this.add_button.setAttribute("data-action", "addAlt");
			this.add_button.addEventListener('click', this.add_button_handler.bind(this));
			alts_list.appendChild(this.add_button);
		}
		return alts_list;
	}

}