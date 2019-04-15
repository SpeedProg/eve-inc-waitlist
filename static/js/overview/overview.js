'use strict';
function GetChartElement() {
	let content_frame = document.getElementById('chart-row');
	let column = document.createElement('div');
	column.setAttribute('class', 'col-xl-6 col-lg-12')
	content_frame.appendChild(column);
	return column;
}

function AddDistinctHullCharacterCombinations(seconds, title) {
	waitlist.base.client.then(
		function(client) {
			client.apis.Statistics.get_statistics_distinct_hull_character({
				'duration_seconds': seconds,
				'requestInterceptor': function(req) {
					req.headers['X-CSRFToken'] = waitlist.base.getMetaData('csrf-token');
					return req;
				}
			}).then(
				function(event) {
					let chartFrame = GetChartElement();
					let myChart = echarts.init(
						chartFrame,
						undefined, {
							'height': 400,
						}
					);
					let option = {
						title: {
							text: title,
							top: 0,
							left: 'center',
							padding: 5,
							textStyle: {
								fontSize: 12,
							},
						},
						tooltip: {},
						series: [{
							name: 'Number of distinct combinations',
							type: 'pie',
							data: event.obj.xnames.map(function(name, idx) {
									return {
										'name': name,
										'value': event.obj.yvalues[idx],
									};
								}).sort(function(a, b) {
									return b.value - a.value;
								})
								.slice(0, 14), // only show first 15
							center: ['50%', '60%'],
							tooltip: {
								formatter: '{b}: {c}({d}%)',
							},
							radius: [0, '50%']
						}]
					};
					myChart.setOption(option);
				}
			).catch(
				function(event) {
					let msg = '';
					if ('obj' in event && 'error' in event.obj) {
						msg = event.obj.error
					} else if ('message' in event) {
						msg = event.message;
					}
					waitlist.base.displayMessage($.i18n('wl-overview-stat-error-hull-char', msg), "danger");
				}
			);
		}
	);
}

function GetApprovalTable(names) {
	let table = document.createElement('table');
	table.setAttribute('class', 'table table-sm');
	
	let thead = document.createElement('thead');
	let th = document.createElement('th');
	th.textContent = $.i18n('wl-account');
	thead.appendChild(th);
	
	let tbody = document.createElement('tbody');
	for (let name of names) {
		let tr = document.createElement('tr');
		let td = document.createElement('td');
		td.textContent = name;
		tr.appendChild(td);
		tbody.appendChild(tr);
	}
	table.appendChild(thead);
	table.appendChild(tbody);
	return table;
}

function AddApprovedFitsByAccount(seconds, title) {
	waitlist.base.client.then(
		function(client) {
			client.apis.Statistics.get_approved_fits_by_account({
				'duration_seconds': seconds,
				'requestInterceptor': function(req) {
					req.headers['X-CSRFToken'] = waitlist.base.getMetaData('csrf-token');
					return req;
				}
			}).then(
				function(event) {
					let show_list = waitlist.base.getMetaData('show_approval_count') != "True";
					let chartFrame = GetChartElement();
					if (show_list) {
						chartFrame.appendChild(GetApprovalTable(event.obj.xnames.slice(0, 14)));
						return;
					}
					
					let myChart = echarts.init(
						chartFrame,
						undefined, {
							'height': 400,
							// 'width': 400,
						}
					);
					let option = {
						title: {
							text: title,
							top: 0,
							left: 'center',
							padding: 5,
							textStyle: {
								fontSize: 12,
							},
						},
						tooltip: {
							formatter: '{b}: {c}',
						},
						xAxis: {
							type: 'value',
							axisLabel: {
								show: true,
							},
						},
						yAxis: {
							type: 'category',
							data: event.obj.xnames.slice(0, 14).reverse(),
							axisLabel: {
								inside: false,
							},
						},
						grid: [{
							x: '30%',
							width: '50%'
						}],
						series: [{
							name: 'Number of approveds',
							type: 'bar',
							data: event.obj.yvalues
								.slice(0, 14)
								.reverse(), // only show first 15
							itemStyle: {
								color: '#91c7ae',
							}
						}],
					};
					myChart.setOption(option)
				}
			).catch(
				function(event) {
					let msg = '';
					if ('obj' in event && 'error' in event.obj) {
						msg = event.obj.error
					} else if ('message' in event) {
						msg = event.message;
					}
					waitlist.base.displayMessage($.i18n('wl-overview-stat-error-fit-by-acc', msg), "danger");
				}
			);
		}
	);
}

function AddJoinedMemebers(seconds, title) {
	waitlist.base.client.then(
		function(client) {
			client.apis.Statistics.get_joined_members({
				'duration_seconds': seconds,
				'requestInterceptor': function(req) {
					req.headers['X-CSRFToken'] = waitlist.base.getMetaData('csrf-token');
					return req;
				}
			}).then(
				function(event) {
					let chartFrame = GetChartElement();
					let myChart = echarts.init(
						chartFrame,
						undefined, {
							'height': 400,
							// 'width': 400,
						}
					);
					let option = {
						title: {
							text: title,
							top: 0,
							left: 'center',
							padding: 5,
							textStyle: {
								fontSize: 12,
							},
						},
						tooltip: {
							formatter: '{b}: {c}',
						},
						xAxis: {
							type: 'category',
							data: event.obj.xnames,
							axisLabel: {
								inside: false,
							},

						},
						yAxis: {
							type: 'value',
							axisLabel: {
								show: true,
							},
						},
						grid: [{
							x: '10%',
							width: '80%'
						}],
						series: [{
							name: 'Characters joined',
							type: 'line',
							data: event.obj.yvalues,
							itemStyle: {
								normal: {
									color: '#61a0a8',
								},
								emphasis: {
									areaStyle: {
										color: '#71b0b8',
										type: 'default',
									},
								},
							}
						}],
					};
					myChart.setOption(option)
				}
			).catch(
				function(event) {
					let msg = '';
					if ('obj' in event && 'error' in event.obj) {
						msg = event.obj.error
					} else if ('message' in event) {
						msg = event.message;
					}
					waitlist.base.displayMessage($.i18n('wl-overview-stat-error-fit-by-acc', msg), "danger");
				}
			);
		}
	);
}


function init_overview() {
	AddApprovedFitsByAccount(2592000, $.i18n('wl-overview-top-commader-time', 15, 30));
	AddDistinctHullCharacterCombinations(2592000, $.i18n("wl-overview-top-distinct-time", 15, 30));
	AddDistinctHullCharacterCombinations(86400, $.i18n("wl-overview-top-distinct-time", 15, 1));
	AddJoinedMemebers(123072000, $.i18n('wl-fleetjoins-per-month'));
}
$(document).ready(init_overview);