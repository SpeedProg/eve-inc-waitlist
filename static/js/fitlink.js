// all related globals are prefixed with "eveui_" to try to avoid collision
// for clarity and consistency:
// " are only used for html attribute values
// ' are used for javascript values
// ` used whenever interpolation is required
'use strict';
// config stuff ( can be overridden in a script block or js file of your choice )
var eveui_use_localstorage = eveui_use_localstorage || 4000000;
var eveui_preload_initial = eveui_preload_initial || 50;
var eveui_preload_interval = eveui_preload_interval || 10;
var eveui_mode = eveui_mode || 'multi_window'; // expand_all, expand, multi_window, modal
var eveui_allow_edit = eveui_allow_edit || false;
var eveui_fit_selector = eveui_fit_selector || '[href^="fitting:"],[data-dna]';
var eveui_item_selector = eveui_item_selector || '[href^="item:"],[data-itemid]';
var eveui_char_selector = eveui_char_selector || '[href^="char:"],[data-charid]';
var eveui_urlify = eveui_urlify || function (dna) {
    return 'https://o.smium.org/loadout/dna/' + encodeURI(dna);
};
var eveui_imageserver = eveui_imageserver || function (image_ref) {
    if (image_ref.startsWith('Character')) {
        return 'https://imageserver.eveonline.com/' + encodeURI(image_ref) + '.jpg';
    }
    return 'https://imageserver.eveonline.com/' + encodeURI(image_ref) + '.png';
};
/* icons from https://github.com/primer/octicons */
var eveui_style = eveui_style || '<style>' + ".eveui_window{position:fixed;line-height:1;background:#eee;color:#000;border:1px solid;opacity:.95;display:flex;flex-direction:column}.eveui_modal_overlay{cursor:pointer;position:fixed;background:#000;top:0;left:0;right:0;bottom:0;z-index:10;opacity:.5}.eveui_title{width:100%;background:#ccc;cursor:move;white-space:nowrap;margin-right:2em}.eveui_scrollable{padding-right:17px;text-align:left;overflow:auto}.eveui_content{display:inline-block;margin:2px;max-width:30em}.eveui_content .eveui_title{display:flex}.eveui_content table{border-collapse:collapse}.eveui_content td{vertical-align:top;padding:0 2px}.eveui_content .eveui_edit{display:none}.eveui_content.eveui_edit .eveui_edit{display:inline-block}.eveui_edit .eveui_edit_icon{display:none}.eveui_itemselect{width:100%;position:absolute}.eveui_itemselect input{width:100%;min-width:20em;padding:0}.eveui_rowcontent{position:relative}.eveui_flexgrow{flex-grow:1}.eveui_fit_header{align-items:center}.eveui_line_spacer{line-height:.5em}.eveui_right{text-align:right}.eveui_icon{display:inline-block;margin:1px;vertical-align:middle;height:1em;width:1em;background-position:center;background-repeat:no-repeat;background-size:contain}.eveui_item_icon{height:20px;width:20px}.eveui_ship_icon{height:32px;width:32px}.eveui_close_icon{cursor:pointer;position:absolute;top:0;right:0;background-image:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0uOTMgMi4zNDNMMi4zNDIuOTI5IDE1LjA3IDEzLjY1NmwtMS40MTQgMS40MTR6Ii8+PHBhdGggZD0iTTIuMzQzIDE1LjA3TC45MjkgMTMuNjU4IDEzLjY1Ni45M2wxLjQxNCAxLjQxNHoiLz48L3N2Zz4=)}.eveui_info_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTQ0OCAzODRjMzUgMCA2NC0yOSA2NC02NHMtMjktNjQtNjQtNjQtNjQgMjktNjQgNjQgMjkgNjQgNjQgNjR6bTAtMzIwQzIwMSA2NCAwIDI2NSAwIDUxMnMyMDEgNDQ4IDQ0OCA0NDggNDQ4LTIwMSA0NDgtNDQ4UzY5NSA2NCA0NDggNjR6bTAgNzY4Yy0xNzcgMC0zMjAtMTQzLTMyMC0zMjBzMTQzLTMyMCAzMjAtMzIwIDMyMCAxNDMgMzIwIDMyMC0xNDMgMzIwLTMyMCAzMjB6bTY0LTMyMGMwLTMyLTMyLTY0LTY0LTY0aC02NGMtMzIgMC02NCAzMi02NCA2NGg2NHYxOTJjMCAzMiAzMiA2NCA2NCA2NGg2NGMzMiAwIDY0LTMyIDY0LTY0aC02NFY1MTJ6Ii8+PC9zdmc+)}.eveui_plus_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI2NDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTM4NCA0NDhWMTkySDI1NnYyNTZIMHYxMjhoMjU2djI1NmgxMjhWNTc2aDI1NlY0NDhIMzg0eiIgLz4KPC9zdmc+Cg==)}.eveui_minus_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTAgNDQ4djEyOGg1MTJWNDQ4SDB6IiAvPgo8L3N2Zz4K)}.eveui_more_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI3NjgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTAgNTc2aDEyOHYtMTI4aC0xMjh2MTI4eiBtMC0yNTZoMTI4di0xMjhoLTEyOHYxMjh6IG0wIDUxMmgxMjh2LTEyOGgtMTI4djEyOHogbTI1Ni0yNTZoNTEydi0xMjhoLTUxMnYxMjh6IG0wLTI1Nmg1MTJ2LTEyOGgtNTEydjEyOHogbTAgNTEyaDUxMnYtMTI4aC01MTJ2MTI4eiIgLz4KPC9zdmc+Cg==)}.eveui_edit_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTcwNCA2NEw1NzYgMTkybDE5MiAxOTIgMTI4LTEyOEw3MDQgNjR6TTAgNzY4bDAuNjg4IDE5Mi41NjJMMTkyIDk2MGw1MTItNTEyTDUxMiAyNTYgMCA3Njh6TTE5MiA4OTZINjRWNzY4aDY0djY0aDY0Vjg5NnoiIC8+Cjwvc3ZnPgo=)}.eveui_copy_icon{cursor:pointer;background-image:url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTcwNCA4OTZoLTY0MHYtNTc2aDY0MHYxOTJoNjR2LTMyMGMwLTM1LTI5LTY0LTY0LTY0aC0xOTJjMC03MS01Ny0xMjgtMTI4LTEyOHMtMTI4IDU3LTEyOCAxMjhoLTE5MmMtMzUgMC02NCAyOS02NCA2NHY3MDRjMCAzNSAyOSA2NCA2NCA2NGg2NDBjMzUgMCA2NC0yOSA2NC02NHYtMTI4aC02NHYxMjh6IG0tNTEyLTcwNGMyOSAwIDI5IDAgNjQgMHM2NC0yOSA2NC02NCAyOS02NCA2NC02NCA2NCAyOSA2NCA2NCAzMiA2NCA2NCA2NCAzMyAwIDY0IDAgNjQgMjkgNjQgNjRoLTUxMmMwLTM5IDI4LTY0IDY0LTY0eiBtLTY0IDUxMmgxMjh2LTY0aC0xMjh2NjR6IG00NDgtMTI4di0xMjhsLTI1NiAxOTIgMjU2IDE5MnYtMTI4aDMyMHYtMTI4aC0zMjB6IG0tNDQ4IDI1NmgxOTJ2LTY0aC0xOTJ2NjR6IG0zMjAtNDQ4aC0zMjB2NjRoMzIwdi02NHogbS0xOTIgMTI4aC0xMjh2NjRoMTI4di02NHoiIC8+Cjwvc3ZnPgo=)}.copy_only{position:absolute;display:inline-block;line-height:0;font-size:0}.nocopy::after{content:attr(data-content)}.whitespace_nowrap{white-space:nowrap}.float_left{float:left}.float_right{float:right}" + '</style>';
var eveui;
(function (eveui) {
    mark('script start');
    // variables
    var $ = jQuery;
    var mouse_x = 0;
    var mouse_y = 0;
    var drag_element = null;
    var drag_element_x = 0;
    var drag_element_y = 0;
    var current_zindex = 100;
    var preload_timer;
    var preload_quota = eveui_preload_initial;
    var cache = {};
    var eve_version;
    var localstorage_timer;
    var localstorage_pending = {};
    var requests_pending = 0;
    var itemselect_lastupdate = 0;
    if (typeof (Storage) === 'undefined') {
        // disable localstorage if unsupported/blocked/whatever
        eveui_use_localstorage = -1;
    }
    // insert required DOM elements / styles
    $('head').append(eveui_style);
    // click handlers to create/close windows
    $(document).on('click', '.eveui_window .eveui_close_icon', function (e) {
        $(this).parent().remove();
        if ($('.eveui_window').length === 0) {
            $('.eveui_modal_overlay').remove();
        }
    });
    $(document).on('click', '.eveui_modal_overlay', function (e) {
        $('.eveui_window').remove();
        $(this).remove();
    });
    $(document).on('click', eveui_fit_selector, function (e) {
        e.preventDefault();
        preload_quota = eveui_preload_initial;
        // hide window if it already exists
        if (this.eveui_window && document.contains(this.eveui_window[0])) {
            this.eveui_window.remove();
            return;
        }
        var dna = $(this).attr('data-dna') || this.href.substring(this.href.indexOf(':') + 1);
        var eveui_name = $(this).attr('data-title') || $(this).text().trim();
        switch (eveui_mode) {
            case 'expand':
            case 'expand_all':
                $(this).attr('data-eveui-expand', 1);
                expand();
                break;
            default:
                this.eveui_window = fit_window(dna, eveui_name);
                break;
        }
    });
    $(document).on('click', eveui_item_selector, function (e) {
        e.preventDefault();
        // hide window if it already exists
        if (this.eveui_window && document.contains(this.eveui_window[0])) {
            this.eveui_window.remove();
            return;
        }
        var item_id = $(this).attr('data-itemid') || this.href.substring(this.href.indexOf(':') + 1);
        // create loading placeholder
        switch (eveui_mode) {
            case 'expand':
            case 'expand_all':
                $(this).attr('data-eveui-expand', 1);
                expand();
                break;
            default:
                this.eveui_window = item_window(item_id);
                break;
        }
    });
    $(document).on('click', eveui_char_selector, function (e) {
        e.preventDefault();
        // hide window if it already exists
        if (this.eveui_window && document.contains(this.eveui_window[0])) {
            this.eveui_window.remove();
            return;
        }
        var char_id = $(this).attr('data-charid') || this.href.substring(this.href.indexOf(':') + 1);
        // create loading placeholder
        switch (eveui_mode) {
            case 'expand':
            case 'expand_all':
                $(this).attr('data-eveui-expand', 1);
                expand();
                break;
            default:
                this.eveui_window = char_window(char_id);
                break;
        }
    });
    // info buttons, copy buttons, etc
    $(document).on('click', '.eveui_minus_icon', function (e) {
        e.preventDefault();
        var item_id = $(this).closest('[data-eveui-itemid]').attr('data-eveui-itemid');
        var dna = $(this).closest('[data-eveui-dna]').attr('data-eveui-dna');
        var re = new RegExp(':' + item_id + ';(\\d+)');
        var new_quantity = parseInt(dna.match(re)[1]) - 1;
        if (new_quantity > 0) {
            dna = dna.replace(re, ':' + item_id + ';' + new_quantity);
        }
        else {
            dna = dna.replace(re, '');
        }
        $(this).closest('[data-eveui-dna]').attr('data-eveui-dna', dna);
        cache_fit(dna).done(function () {
            var eveui_window = $(".eveui_window[data-eveui-dna=\"" + dna + "\"]");
            eveui_window.find('.eveui_content ').html(format_fit(dna));
            $(window).trigger('resize');
        });
    });
    $(document).on('click', '.eveui_plus_icon', function (e) {
        e.preventDefault();
        var item_id = $(this).closest('[data-eveui-itemid]').attr('data-eveui-itemid');
        var dna = $(this).closest('[data-eveui-dna]').attr('data-eveui-dna');
        var re = new RegExp(":" + item_id + ";(\\d+)");
        var new_quantity = parseInt(dna.match(re)[1]) + 1;
        if (new_quantity > 0) {
            dna = dna.replace(re, ":" + item_id + ";" + new_quantity);
        }
        else {
            dna = dna.replace(re, '');
        }
        $(this).closest('[data-eveui-dna]').attr('data-eveui-dna', dna);
        cache_fit(dna).done(function () {
            var eveui_window = $(".eveui_window[data-eveui-dna=\"" + dna + "\"]");
            eveui_window.find('.eveui_content ').html(format_fit(dna));
            $(window).trigger('resize');
        });
    });
    $(document).on('click', '.eveui_edit_icon', function (e) {
        e.preventDefault();
        $(this).closest('.eveui_content').addClass('eveui_edit');
        $(this).remove();
    });
    $(document).on('click', '.eveui_more_icon', function (e) {
        e.preventDefault();
        var item_id = $(this).closest('[data-eveui-itemid]').attr('data-eveui-itemid');
        // hide window if it already exists
        if (this.eveui_itemselect && document.contains(this.eveui_itemselect[0])) {
            this.eveui_itemselect.remove();
            return;
        }
        $('.eveui_itemselect').remove();
        var eveui_itemselect = $("<span class=\"eveui_itemselect\"><input type=\"text\" list=\"eveui_itemselect\" placeholder=\"" + $(this).closest('[data-eveui-itemid]').find('.eveui_rowcontent').text() + "\" /><datalist id=\"eveui_itemselect\" /></span>");
        eveui_itemselect.css('z-index', current_zindex++);
        this.eveui_itemselect = eveui_itemselect;
        $(this).closest('tr').find('.eveui_rowcontent').prepend(this.eveui_itemselect);
        eveui_itemselect.find('input').focus();
        if (typeof (item_id) === 'undefined') {
            return;
        }
        var request_timestamp = performance.now();
        // get market group id for selected item
        cache_request('crest/market/types/' + item_id, "https://crest-tq.eveonline.com/market/types/" + item_id + "/").done(function () {
            var data = cache['crest/market/types/' + item_id];
            var market_group = data.marketGroup.id_str;
            // get items with the same market group
            cache_request('crest/market/groups/' + market_group, "https://crest-tq.eveonline.com/market/types/?group=https://crest-tq.eveonline.com/market/groups/" + market_group + "/").done(function () {
                if (request_timestamp > itemselect_lastupdate) {
                    itemselect_lastupdate = request_timestamp;
                }
                else {
                    return;
                }
                var data = cache['crest/market/groups/' + market_group];
                var datalist = $('.eveui_itemselect datalist');
                data.items.sort(function (a, b) { return a.type.name.localeCompare(b.type.name); });
                for (var i in data.items) {
                    datalist.append("<option label=\"" + data.items[i].type.name + "\">(" + data.items[i].type.id_str + ")</option>");
                }
            });
        });
    });
    $(document).on('input', '.eveui_itemselect input', function (e) {
        var eveui_itemselect = $(this).closest('.eveui_itemselect');
        var input_str = $(this).val();
        if (input_str.slice(0, 1) === '(' && input_str.slice(-1) === ')') {
            // numeric input is expected to mean selected item
            input_str = input_str.slice(1, -1);
            var item_id = $(this).closest('[data-eveui-itemid]').attr('data-eveui-itemid');
            var dna_1 = $(this).closest('[data-eveui-dna]').attr('data-eveui-dna');
            if (typeof (item_id) === 'undefined') {
                // append new item
                dna_1 = dna_1.slice(0, -2) + ":" + input_str + ";1::";
            }
            else {
                // replace existing item
                var re = new RegExp("^" + item_id + ":");
                dna_1 = dna_1.replace(re, input_str + ":");
                re = new RegExp(":" + item_id + ";");
                dna_1 = dna_1.replace(re, ":" + input_str + ";");
            }
            $(this).closest('[data-eveui-dna]').attr('data-eveui-dna', dna_1);
            cache_fit(dna_1).done(function () {
                var eveui_window = $(".eveui_window[data-eveui-dna=\"" + dna_1 + "\"]");
                eveui_window.find('.eveui_content ').html(format_fit(dna_1));
                $(window).trigger('resize');
            });
            $('.eveui_itemselect').remove();
        }
        else {
            // search for matching items
            if (input_str.length < 3) {
                return;
            }
            var request_timestamp_1 = performance.now();
            // get item ids that match input
            $.ajax({
                url: "https://esi.tech.ccp.is/v1/search/",
                cache: true,
                data: {
                    search: $(this).val(),
                    categories: 'inventorytype'
                }
            }).done(function (data) {
                if (typeof (data.inventorytype) === 'undefined') {
                    return;
                }
                var arg = {
                    ids: data.inventorytype.slice(0, 50)
                };
                // get names for required item ids
                $.ajax({
                    url: "https://esi.tech.ccp.is/v1/universe/names/",
                    cache: true,
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(arg)
                }).done(function (data) {
                    if (request_timestamp_1 > itemselect_lastupdate) {
                        itemselect_lastupdate = request_timestamp_1;
                    }
                    else {
                        return;
                    }
                    var datalist = eveui_itemselect.find('datalist');
                    data.sort(function (a, b) { return a.name.localeCompare(b.name); });
                    datalist.empty();
                    for (var i in data) {
                        datalist.append("<option label=\"" + data[i].name + "\">(" + data[i].id + ")</option>");
                    }
                });
            });
        }
    });
    // close itemselect window on any outside click
    $(document).on('click', function (e) {
        if ($(e.target).closest('.eveui_itemselect,.eveui_more_icon').length > 0) {
            return;
        }
        $('.eveui_itemselect').remove();
    });
    $(document).on('click', '.eveui_copy_icon', function (e) {
        clipboard_copy($(this).closest('.eveui_content'));
    });
    // custom window drag handlers
    $(document).on('mousedown', '.eveui_window', function (e) {
        $(this).css('z-index', current_zindex++);
        ;
    });
    $(document).on('mousedown', '.eveui_title', function (e) {
        e.preventDefault();
        drag_element = $(this).parent();
        drag_element_x = mouse_x - drag_element.position().left;
        drag_element_y = mouse_y - drag_element.position().top;
        drag_element.css('z-index', current_zindex++);
        ;
    });
    $(document).on('mousemove', function (e) {
        mouse_x = e.clientX;
        mouse_y = e.clientY;
        if (drag_element === null) {
            return;
        }
        drag_element.css('left', mouse_x - drag_element_x);
        drag_element.css('top', mouse_y - drag_element_y);
    });
    $(document).on('mouseup', function (e) {
        drag_element = null;
    });
    $(window).on('resize', function (e) {
        // resize handler to try to keep windows onscreen
        $('.eveui_window').each(function () {
            var eveui_window = $(this);
            var eveui_content = eveui_window.find('.eveui_content');
            if (eveui_content.height() > window.innerHeight - 50) {
                eveui_window.css('height', window.innerHeight - 50);
            }
            else {
                eveui_window.css('height', '');
            }
            if (eveui_content.width() > window.innerWidth - 40) {
                eveui_window.css('width', window.innerWidth - 40);
            }
            else {
                eveui_window.css('width', '');
            }
            if (eveui_window[0].getBoundingClientRect().bottom > window.innerHeight) {
                eveui_window.css('top', window.innerHeight - eveui_window.height() - 25);
            }
            if (eveui_window[0].getBoundingClientRect().right > window.innerWidth) {
                eveui_window.css('left', window.innerWidth - eveui_window.width() - 10);
            }
        });
        if (eveui_mode === 'modal') {
            var eveui_window = $('[data-eveui-modal]');
            eveui_window.css('top', window.innerHeight / 2 - eveui_window.height() / 2);
            eveui_window.css('left', window.innerWidth / 2 - eveui_window.width() / 2);
        }
    });
    mark('event handlers set');
    function eve_version_query() {
        mark('eve version request');
        $.ajax("https://crest-tq.eveonline.com/", {
            dataType: 'json',
            cache: true,
        }).done(function (data) {
            eve_version = data.serverVersion;
            mark('eve version response ' + eve_version);
            if (eveui_use_localstorage > 0 && typeof (localStorage['eveui_cache']) !== 'undefined') {
                // load localstorage cache if applicable
                var localstorage_cache_1 = JSON.parse(localStorage.getItem('eveui_cache'));
                $.each(localstorage_cache_1, function (k, v) {
                    if (k.startsWith('EVE')) {
                        // version key
                        if (k === eve_version) {
                            $.extend(cache, v);
                        }
                        else {
                            delete localstorage_cache_1[k];
                        }
                    }
                    else {
                        // timestamp key
                        if (Number(k) > Date.now()) {
                            $.extend(cache, v);
                        }
                        else {
                            delete localstorage_cache_1[k];
                        }
                    }
                });
                localStorage.setItem('eveui_cache', JSON.stringify(localstorage_cache_1));
                mark("localstorage cache loaded " + Object.keys(cache).length + " entries");
            }
            $(document).ready(function () {
                mark('expanding fits');
                expand();
            });
            // lazy preload timer
            preload_timer = setTimeout(lazy_preload, eveui_preload_interval);
            mark('preload timer set');
        }).fail(function (xhr) {
            mark('eve version request failed');
            setTimeout(eve_version_query, 10000);
        });
    }
    eve_version_query();
    function new_window(title) {
        if (title === void 0) { title = '&nbsp;'; }
        var eveui_window = $("<span class=\"eveui_window\"><div class=\"eveui_title\">" + title + "</div><span class=\"eveui_icon eveui_close_icon\" /><span class=\"eveui_scrollable\"><span class=\"eveui_content\">Loading...</span></span></span>");
        if (eveui_mode === 'modal' && $('.eveui_modal_overlay').length === 0) {
            $('body').append("<div class=\"eveui_modal_overlay\" />");
            eveui_window.attr('data-eveui-modal', 1);
        }
        eveui_window.css('z-index', current_zindex++);
        eveui_window.css('left', mouse_x + 10);
        eveui_window.css('top', mouse_y - 10);
        return eveui_window;
    }
    function mark(mark) {
        // log script time with annotation for performance metric
        console.log('eveui: ' + performance.now().toFixed(3) + ' ' + mark);
    }
    function format_fit(dna, eveui_name) {
        // generates html for a fit display
        var high_slots = {};
        var med_slots = {};
        var low_slots = {};
        var rig_slots = {};
        var subsystem_slots = {};
        var other_slots = {};
        var items = dna.split(':');
        // ship name and number of slots
        var ship_id = parseInt(items.shift());
        var ship = cache['crest/inventory/types/' + ship_id];
        ship.hiSlots = 0;
        ship.medSlots = 0;
        ship.lowSlots = 0;
        for (var i in ship.dogma.attributes) {
            var attr = cache['crest/inventory/types/' + ship_id].dogma.attributes[i];
            if (attr.attribute.name === 'hiSlots') {
                ship[attr.attribute.name] = attr.value;
            }
            else if (attr.attribute.name === 'medSlots') {
                ship[attr.attribute.name] = attr.value;
            }
            else if (attr.attribute.name === 'lowSlots') {
                ship[attr.attribute.name] = attr.value;
            }
            else if (attr.attribute.name === 'rigSlots') {
                ship[attr.attribute.name] = attr.value;
            }
            else if (attr.attribute.name === 'maxSubSystems') {
                ship[attr.attribute.name] = attr.value;
            }
        }
        // categorize items into slots
        outer: for (var i in items) {
            if (items[i].length === 0) {
                continue;
            }
            var match = items[i].split(';');
            var item_id = match[0];
            var quantity = parseInt(match[1]);
            var item = cache['crest/inventory/types/' + item_id];
            for (var j in item.dogma.attributes) {
                var attr = item.dogma.attributes[j];
                if (attr.attribute.name === 'hiSlotModifier') {
                    ship.hiSlots += attr.value;
                }
                if (attr.attribute.name === 'medSlotModifier') {
                    ship.medSlots += attr.value;
                }
                if (attr.attribute.name === 'lowSlotModifier') {
                    ship.lowSlots += attr.value;
                }
            }
            for (var j in item.dogma.effects) {
                var effect = item.dogma.effects[j].effect;
                if (effect.name === 'hiPower') {
                    high_slots[item_id] = quantity;
                    continue outer;
                }
                else if (effect.name === 'medPower') {
                    med_slots[item_id] = quantity;
                    continue outer;
                }
                else if (effect.name === 'loPower') {
                    low_slots[item_id] = quantity;
                    continue outer;
                }
                else if (effect.name === 'rigSlot') {
                    rig_slots[item_id] = quantity;
                    continue outer;
                }
                else if (effect.name === 'subSystem') {
                    subsystem_slots[item_id] = quantity;
                    continue outer;
                }
            }
            other_slots[item_id] = quantity;
        }
        function item_rows(fittings, slots_available) {
            // generates table rows for listed slots
            var html = '';
            var slots_used = 0;
            for (var item_id in fittings) {
                var item = cache['crest/inventory/types/' + item_id];
                slots_used += fittings[item_id];
                if (slots_available) {
                    html += "<tr class=\"copy_only\"><td>" + (item.name + '<br />').repeat(fittings[item_id]);
                }
                else {
                    html += "<tr class=\"copy_only\"><td>" + item.name + " x" + fittings[item_id] + "<br />";
                }
                html += "<tr class=\"nocopy\" data-eveui-itemid=\"" + item_id + "\"><td><img src=\"" + eveui_imageserver('Type/' + item_id + '_32') + "\" class=\"eveui_icon eveui_item_icon\" /><td class=\"eveui_right\">" + fittings[item_id] + "<td colspan=\"2\"><div class=\"eveui_rowcontent\">" + item.name + "</div><td class=\"eveui_right whitespace_nowrap\"><span data-itemid=\"" + item_id + "\" class=\"eveui_icon eveui_info_icon\" /><span class=\"eveui_icon eveui_plus_icon eveui_edit\" /><span class=\"eveui_icon eveui_minus_icon eveui_edit\" /><span class=\"eveui_icon eveui_more_icon eveui_edit\" />";
            }
            if (typeof (slots_available) !== 'undefined') {
                if (slots_available > slots_used) {
                    html += "<tr class=\"nocopy\"><td class=\"eveui_icon eveui_item_icon\" /><td class=\"eveui_right whitespace_nowrap\">" + (slots_available - slots_used) + "<td colspan=\"2\"><div class=\"eveui_rowcontent\">Empty</div><td class=\"eveui_right\"><span class=\"eveui_icon eveui_more_icon eveui_edit\" />";
                }
                if (slots_used > slots_available) {
                    html += "<tr class=\"nocopy\"><td class=\"eveui_icon eveui_item_icon\" /><td class=\"eveui_right\">" + (slots_available - slots_used) + "<td><div class=\"eveui_rowcontent\">Excess</div>";
                }
            }
            return html;
        }
        var html = "<table><thead><tr class=\"eveui_fit_header\" data-eveui-itemid=\"" + ship_id + "\"><td colspan=\"2\"><img src=\"" + eveui_imageserver('Type/' + ship_id + '_32') + "\" class=\"eveui_icon eveui_ship_icon\" /><td><div class=\"eveui_rowcontent\"><span class=\"eveui_startcopy\" />[<a target=\"_blank\" href=\"" + eveui_urlify(dna) + "\">" + ship.name + ", " + (eveui_name || ship.name) + "</a>]<br/></div><td class=\"eveui_right whitespace_nowrap nocopy\" colspan=\"2\">" + (eveui_allow_edit ? '<span class="eveui_icon eveui_edit_icon" />' : '') + "<span class=\"eveui_icon eveui_copy_icon\" /><span data-itemid=\"" + ship_id + "\" class=\"eveui_icon eveui_info_icon\" /><span class=\"eveui_icon eveui_edit\" /><span class=\"eveui_icon eveui_edit\" /><span class=\"eveui_icon eveui_more_icon eveui_edit\" /></thead><tbody class=\"whitespace_nowrap\">" + item_rows(high_slots, ship.hiSlots) + "<tr><td class=\"eveui_line_spacer\">&nbsp;" + item_rows(med_slots, ship.medSlots) + "<tr><td class=\"eveui_line_spacer\">&nbsp;" + item_rows(low_slots, ship.lowSlots) + "<tr><td class=\"eveui_line_spacer\">&nbsp;" + item_rows(rig_slots, ship.rigSlots) + "<tr><td class=\"eveui_line_spacer\">&nbsp;" + item_rows(subsystem_slots, ship.maxSubSystems) + "<tr><td class=\"eveui_line_spacer\">&nbsp;" + item_rows(other_slots) + "</tbody></table><span class=\"eveui_endcopy\" />";
        return html;
    }
    eveui.format_fit = format_fit;
    function fit_window(dna, eveui_name) {
        // creates and populates a fit window
        var eveui_window = new_window('Fit');
        eveui_window.addClass('fit_window');
        eveui_window.attr('data-eveui-dna', dna);
        $('body').append(eveui_window);
        $(window).trigger('resize');
        // load required items and set callback to display
        mark('fit window created');
        cache_fit(dna).done(function () {
            eveui_window.find('.eveui_content ').html(format_fit(dna, eveui_name));
            $(window).trigger('resize');
            mark('fit window populated');
        });
        return eveui_window;
    }
    eveui.fit_window = fit_window;
    function format_item(item_id) {
        var item = cache['crest/inventory/types/' + item_id];
        var html = "<table class=\"whitespace_nowrap\"><tr><td>" + item.name;
        for (var i in item.dogma.attributes) {
            var attr = item.dogma.attributes[i];
            html += '<tr>';
            html += '<td>' + attr.attribute.name;
            html += '<td>' + attr.value;
        }
        html += '</table>';
        return html;
    }
    eveui.format_item = format_item;
    function item_window(item_id) {
        // creates and populates an item window
        var eveui_window = new_window('Item');
        eveui_window.attr('data-eveui-itemid', item_id);
        eveui_window.addClass('item_window');
        switch (eveui_mode) {
            default:
                $('body').append(eveui_window);
                break;
        }
        mark('item window created');
        // load required items and set callback to display
        cache_request('crest/inventory/types/' + item_id, "https://crest-tq.eveonline.com/inventory/types/" + item_id + "/").done(function () {
            eveui_window.find('.eveui_content').html(format_item(item_id));
            $(window).trigger('resize');
            mark('item window populated');
        }).fail(function () {
            eveui_window.remove();
        });
        $(window).trigger('resize');
        return eveui_window;
    }
    eveui.item_window = item_window;
    function format_char(char_id) {
        var character = cache['crest/characters/' + char_id];
        var html = "<table><tr><td colspan=\"2\"><img class=\"float_left\" src=\"" + eveui_imageserver('Character/' + character.id + '_128') + "\" height=\"128\" width=\"128\" />" + character.name + "<hr /><img class=\"float_left\" src=\"" + eveui_imageserver('Corporation/' + character.corporation.id_str + '_64') + "\" height=\"64\" width=\"64\" />Member of " + character.corporation.name + "<tr><td>Bio:<td>" + character.description.replace(/<font[^>]+>/g, '<font>') + "</table>";
        return html;
    }
    eveui.format_char = format_char;
    function char_window(char_id) {
        var eveui_window = new_window('Character');
        eveui_window.attr('data-eveui-charid', char_id);
        eveui_window.addClass('char_window');
        switch (eveui_mode) {
            default:
                $('body').append(eveui_window);
                break;
        }
        mark('char window created');
        // load required chars and set callback to display
        cache_request('crest/characters/' + char_id, "https://crest-tq.eveonline.com/characters/" + char_id + "/").done(function () {
            eveui_window.find('.eveui_content').html(format_char(char_id));
            $(window).trigger('resize');
            mark('char window populated');
        }).fail(function () {
            eveui_window.remove();
        });
        $(window).trigger('resize');
        return eveui_window;
    }
    eveui.char_window = char_window;
    function expand() {
        // expand any fits marked with a data-eveui-expand attribute ( or all, if expand_all mode )
        var expand_filter = '[data-eveui-expand]';
        if (eveui_mode === "expand_all") {
            expand_filter = '*';
        }
        $(eveui_fit_selector).filter(expand_filter).each(function () {
            var selected_element = $(this);
            if (selected_element.closest('.eveui_content').length > 0) {
                // if element is part of eveui content already, don't expand, otherwise we might get a really fun infinite loop
                return;
            }
            var dna = selected_element.attr('data-dna') || this.href.substring(this.href.indexOf(':') + 1);
            cache_fit(dna).done(function () {
                var eveui_name = $(this).text().trim();
                var eveui_content = $("<span class=\"eveui_content eveui_fit\">" + format_fit(dna, eveui_name) + "</span>");
                eveui_content.attr('data-eveui-dna', dna);
                selected_element = selected_element.replaceWith(eveui_content);
                mark('fit window expanded');
            });
        });
        $(eveui_item_selector).filter(expand_filter).each(function () {
            var selected_element = $(this);
            if (selected_element.closest('.eveui_content').length > 0) {
                // if element is part of eveui content already, don't expand, otherwise we might get a really fun infinite loop
                return;
            }
            var item_id = selected_element.attr('data-itemid') || this.href.substring(this.href.indexOf(':') + 1);
            cache_request('crest/inventory/types/' + item_id, "https://crest-tq.eveonline.com/inventory/types/" + item_id + "/").done(function () {
                selected_element.replaceWith("<span class=\"eveui_content eveui_item\">" + format_item(item_id) + "</span>");
                mark('item window expanded');
            });
        });
        $(eveui_char_selector).filter(expand_filter).each(function () {
            var selected_element = $(this);
            if (selected_element.closest('.eveui_content').length > 0) {
                // if element is part of eveui content already, don't expand, otherwise we might get a really fun infinite loop
                return;
            }
            var char_id = selected_element.attr('data-charid') || this.href.substring(this.href.indexOf(':') + 1);
            cache_request('crest/characters/' + char_id, "https://crest-tq.eveonline.com/characters/" + char_id + "/").done(function () {
                selected_element.replaceWith("<span class=\"eveui_content eveui_char\">" + format_char(char_id) + "</span>");
                mark('char window expanded');
            });
        });
    }
    eveui.expand = expand;
    function lazy_preload() {
        // preload timer function
        preload_timer = setTimeout(lazy_preload, 5000);
        if (requests_pending >= 10) {
            return;
        }
        if (preload_quota > 0) {
            $(eveui_fit_selector).not('[data-eveui-cached]').each(function (i) {
                var elem = $(this);
                var dna = elem.data('dna') || this.href.substring(this.href.indexOf(':') + 1);
                var promise = cache_fit(dna);
                // skip if already cached
                if (promise.state() === 'resolved') {
                    elem.attr('data-eveui-cached', 1);
                }
                else {
                    preload_quota--;
                    promise.always(function () {
                        clearTimeout(preload_timer);
                        preload_timer = setTimeout(lazy_preload, eveui_preload_interval);
                    });
                    return false;
                }
            });
        }
    }
    function cache_fit(dna) {
        // caches all items required to process the specified fit
        var pending = [];
        var items = dna.split(':');
        for (var item in items) {
            if (items[item].length === 0) {
                continue;
            }
            var match = items[item].split(';');
            var item_id = match[0];
            pending.push(cache_request('crest/inventory/types/' + item_id, "https://crest-tq.eveonline.com/inventory/types/" + item_id + "/"));
        }
        return $.when.apply(null, pending);
    }
    function cache_request(key, url) {
        if (typeof (cache[key]) === 'object') {
            if (typeof (cache[key].promise) === 'function') {
                // item is pending, return the existing deferred object
                return cache[key];
            }
            else {
                // if item is already cached, we can return a resolved promise
                return $.Deferred().resolve();
            }
        }
        requests_pending++;
        return cache[key] = $.ajax(url, {
            dataType: 'json',
            cache: true,
        }).done(function (data) {
            // store data in session cache
            cache[key] = data;
            // store data in localstorage where applicable
            if (eveui_use_localstorage > 0) {
                var version = void 0;
                if (key.startsWith('crest/inventory/types')) {
                    // inventory/types key should be reliably cachable until such time as the version changes
                    version = eve_version;
                }
                if (typeof version === 'undefined') {
                    // default is to use the standard browser cache
                    return;
                }
                if (typeof (localstorage_pending[version]) !== 'object') {
                    localstorage_pending[version] = {};
                }
                localstorage_pending[version][key] = data;
                // timer to throttle localstorage updates
                clearTimeout(localstorage_timer);
                localstorage_timer = setTimeout(function () {
                    var localstorage_cache = JSON.parse(localStorage.getItem('eveui_cache')) || {};
                    $.extend(true, localstorage_cache, localstorage_pending);
                    var localstorage_cache_json = JSON.stringify(localstorage_cache);
                    if (localstorage_cache_json.length > eveui_use_localstorage) {
                        mark('localstorage limit exceeded');
                        return;
                    }
                    try {
                        localStorage.setItem('eveui_cache', localstorage_cache_json);
                        mark('localstorage updated ' + Object.keys(localstorage_pending).length);
                    }
                    catch (err) {
                    }
                    localstorage_pending = {};
                }, 5000);
            }
        }).fail(function (xhr) {
            delete cache[key];
        }).always(function () {
            requests_pending--;
        });
    }
    function clipboard_copy(element) {
        // copy the contents of selected element to clipboard
        // while excluding any elements with 'nocopy' class
        // and including otherwise-invisible elements with 'copyonly' class
        $('.nocopy').hide();
        $('.copyonly').show();
        var selection = window.getSelection();
        var range = document.createRange();
        if (element.find('.eveui_startcopy').length) {
            range.setStart(element.find('.eveui_startcopy')[0], 0);
            range.setEnd(element.find('.eveui_endcopy')[0], 0);
        }
        else {
            range.selectNodeContents(element[0]);
        }
        selection.removeAllRanges();
        selection.addRange(range);
        document.execCommand('copy');
        selection.removeAllRanges();
        $('.nocopy').show();
        $('.copyonly').hide();
    }
    // additional shims for older browsers
    /* from https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/String/repeat */
    if (!String.prototype.repeat) {
        String.prototype.repeat = function (count) {
            'use strict';
            if (this == null) {
                throw new TypeError('can\'t convert ' + this + ' to object');
            }
            var str = '' + this;
            count = +count;
            if (count != count) {
                count = 0;
            }
            if (count < 0) {
                throw new RangeError('repeat count must be non-negative');
            }
            if (count == Infinity) {
                throw new RangeError('repeat count must be less than infinity');
            }
            count = Math.floor(count);
            if (str.length == 0 || count == 0) {
                return '';
            }
            // Ensuring count is a 31-bit integer allows us to heavily optimize the
            // main part. But anyway, most current (August 2014) browsers can't handle
            // strings 1 << 28 chars or longer, so:
            if (str.length * count >= 1 << 28) {
                throw new RangeError('repeat count must not overflow maximum string size');
            }
            var rpt = '';
            for (;;) {
                if ((count & 1) == 1) {
                    rpt += str;
                }
                count >>>= 1;
                if (count == 0) {
                    break;
                }
                str += str;
            }
            // Could we try:
            // return Array(count + 1).join(this);
            return rpt;
        };
    }
    /* https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/String/startsWith */
    if (!String.prototype.startsWith) {
        String.prototype.startsWith = function (searchString, position) {
            position = position || 0;
            return this.substr(position, searchString.length) === searchString;
        };
    }
    mark('script end');
})(eveui || (eveui = {}));
