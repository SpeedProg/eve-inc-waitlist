'use strict';

const persist_details = (() => {
	class PersistDetails {
		constructor() {
			this.open = "open";
			this.closed = "closed";
			this.prefix = "persisted_details_";
			this.createListeners = this.createListeners.bind(this);
			this.handleToggle = this.handleToggle.bind(this);
			this.getKey = this.getKey.bind(this);
			this.persist();
		}

		getStorage(details) {
			return window[(details.dataset.storage === "session") ? "sessionStorage" : "localStorage"];
		}
		
		getKey(details) {
			return this.prefix + details.id;
		}

		handleToggle(event) {
			const
			default_open = (event.target.dataset.default === this.open),
			storage = this.getStorage(event.target);
			(event.target.open === default_open)
				? storage.removeItem(this.getKey(event.target))
				: storage.setItem(this.getKey(event.target),
						(default_open) ? this.open : this.closed);
		}
	
		createListeners() {
			let detailsGroup = Array.from(document.getElementsByTagName("details"))
				.filter((details) => details.dataset.action === "persist" && details.id);
			if (!window.localStorage || !window.sessionStorage) {
				detailsGroup = detailsGroup.filter(this.getStorage);
			}
			detailsGroup.forEach((details) => {
				details.removeEventListener("toggle", this.handleToggle);
				const
				storage = this.getStorage(details),
				key = this.getKey(details),
				saved_default = storage.getItem(key),
				default_open = (details.dataset.default === this.open),
				saved_is_open = (saved_default === this.open),
				saved_is_closed = (saved_default === this.closed);
				if (saved_is_open && default_open) {
					// it was default open and matched dom
					details.removeAttribute(this.open);
				} else if (saved_is_closed && !default_open) {
					// it was default closed and matched dom
					details.setAttribute(this.open, this.open);
				} else if (saved_is_open || saved_is_closed) {
					// was valid value tho did not match dom default
					storage.removeItem(key);
				}
				details.addEventListener("toggle", this.handleToggle);
			});
		}

		persist() {
			if (window.localStorage || window.sessionStorage) {
				$(document).ready(this.createListeners);
			}
		}
	}
	const details = new PersistDetails();

	return {
		reload: details.persist,
	};
})();
