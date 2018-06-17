'use strict';
document
	.addEventListener(
		'DOMContentLoaded',
		function() {
			$('body')
				.on(
					'change',
					'input[type="file"][class="custom-file-input"]',
					function(event) {
						const $input = $(event.currentTarget);
						const target = $input.data('target');
						const $target = $(target);

						if (!$target.length) {
							return console.error(
								'Invalid target for custom file', $input);
						}

						if (!$target.attr('data-content')) {
							return console.error(
									'Invalid `data-content` for custom file target',
									$input);
						}

						// set original content so we can revert
						// if user deselects file
						if (!$target.attr('data-original-content')) {
							$target.attr('data-original-content', $target
								.attr('data-content'));
						}

						const input = $input.get(0);

						let
						name = $.type(input)
							&& $.type(input.files) !== "undefined"
							&& $.type(input.files[0]) !== "undefined"
							&& $.type(input.files[0].name) === "string" ? input.files[0].name
							: $input.val();

						if ($.type(name) === "null" || name === '') {
							name = $target.attr('data-original-content');
						}

						$target.attr('data-content', name);

					});
		});
