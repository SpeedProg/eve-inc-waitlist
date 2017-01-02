EditableGrid.prototype.updatePaginator = function() {
	var editableGrid = this;

	// get interval
	var interval = this.getSlidingPageInterval(20);
	if (interval === null){
		return;
	}

	// get pages in interval (with links except for the current page)
	var pages = this.getPagesInInterval(interval,
		function(pageIndex, isCurrent) {
			if (isCurrent) {
				return $($.parseHTML(`<li class="page-item active"><a class="page-link" href="#">${pageIndex}</a></li>`)[0]);
			}
			return $($.parseHTML(`<li class="page-item"><a class="page-link" href="#">${pageIndex}</a></li>`)[0].on('click',
				function(){
					editableGrid.setPageIndex(pageIndex);
				}
			));
		}
	);

	// "first" link
	var link = $("#paginator > li:first-child");
	if (!this.canGoBack() && !link.hasClass("disabled")) {
		link.addClass("disabled");
	} else if (this.canGoBack() && link.hasClass("disabled")) {
		link.removeClass("disabled");
	}
	

	// "prev" link
	link = $("#paginator > li:nth-child(2)");
	if (!this.canGoBack() && !link.hasClass("disabled")) {
		link.addClass("disabled");
	} else if (this.canGoBack() && link.hasClass("disabled")) {
		link.removeClass("disabled");
	}
	
	// next
	link = $("#paginator > li:nth-last-child(2)");
	if (!this.canGoForward() && !link.hasClass("disabled")) {
		link.addClass("disabled");
	} else if (this.canGoForward() && link.hasClass("disabled")) {
		link.removeClass("disabled");
	}

	// "last" link
	link = $("#paginator > li:nth-last-child(1)");
	if (!this.canGoForward() && !link.hasClass("disabled")) {
		link.addClass("disabled");
	} else if (this.canGoForward() && link.hasClass("disabled")) {
		link.removeClass("disabled");
	}

	// remove old pages
	var pageLinks = $("#paginator > li").slice(2);
	pageLinks = pageLinks.slice(0, pageLinks.length-2);
	pageLinks.remove();

	// pages
	// we need to insert them in front of the next button
	var nextButton = $("#paginator > li:nth-last-child(2)");
	for (let p = 0; p < pages.length; p++) {
		nextButton.before(pages[p]);
	}
};

EditableGrid.prototype.initializeGrid = function() {
	console.log("Init Grid");
	var editableGrid = this;
	this.tableRendered = function() {
		this.updatePaginator();
	};
	
	// first page
	var link = $("#paginator > li:first-child");
	if (!this.canGoBack()) {
		link.addClass("disabled");
	}
	link.on("click", function(event) {
		if ($(event.target).hasClass("disabled")) {
			return;
		}
		editableGrid.firstPage();
	});
	
	// prev page
	link = $("#paginator > li:nth-child(2)");
	if (!this.canGoBack()) {
		link.addClass("disabled");
	}
	link.on("click", function(event) {
		if ($(event.target).hasClass("disabled")) {
			return;
		}
		editableGrid.prevPage();
	});
	if (!this.canGoBack()) {
		link.addClass("disabled");
	}
	
	// next page
	link = $("#paginator > li:nth-last-child(2)");
	link.on("click", function(event) {
		if ($(event.target).hasClass("disabled")) {
			return;
		}
		editableGrid.nextPage();
	});
	if (!this.canGoForward()) {
		link.addClass("disabled");
	}
	
	// last page
	link = $("#paginator > li:nth-last-child(1)");
	link.on("click", function(event) {
		if ($(event.target).hasClass("disabled")) {
			return;
		}
		editableGrid.lastPage();
	});
	if (!this.canGoForward()) {
		link.addClass("disabled");
	}
};

$(document).ready(function() {
	var editableGrid = new EditableGrid(
		"CommandCore",
		{
			enableSort: true,
			pageSize: 20,
			maxBars: 20
		},
		$.parseHTML('<i class="fa fa-arrow-down" aria-hidden="true"></i>')[0],
		$.parseHTML('<i class="fa fa-arrow-up" aria-hidden="true"></i>')[0]);

	editableGrid.load({
		metadata: [
			{
				name: "Account Name",
				datatype: "string",
				editable: false
			}, {
				name: "Roles",
				datatype: "string",
				editable: false
			}, {
				name: "Known Alts",
				datatype: "string",
				editable: false
			}
		]
	});

	editableGrid.attachToHTMLTable('commanderlist');
	editableGrid.initializeGrid();
	editableGrid.renderGrid();
	$('#filter').on('keyup', function() {
		editableGrid.filter($('#filter').val());
	});
});
