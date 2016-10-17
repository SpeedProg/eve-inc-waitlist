'use strict';

var eveui_use_localstorage = eveui_use_localstorage || 4e6,
    eveui_preload_initial = eveui_preload_initial || 50,
    eveui_preload_interval = eveui_preload_interval || 10,
    eveui_mode = eveui_mode || "multi_window",
    eveui_allow_edit = eveui_allow_edit || !1,
    eveui_fit_selector = eveui_fit_selector || '[href^="fitting:"],[data-dna]',
    eveui_item_selector = eveui_item_selector || '[href^="item:"],[data-itemid]',
    eveui_char_selector = eveui_char_selector || '[href^="char:"],[data-charid]',
    eveui_urlify = eveui_urlify || function(dna) {
        return "https://o.smium.org/loadout/dna/" + encodeURI(dna)
    },
    eveui_autocomplete_endpoint = eveui_autocomplete_endpoint || function(str) {
        return "https://zkillboard.com/autocomplete/typeID/" + encodeURI(str) + "/"
    },
    eveui_style = eveui_style || "\n\t<style>\n\t\t/* eveui_css_start */\n\t\t.eveui_window {\n\t\t\tposition: fixed;\n\t\t\tline-height: 1;\n\t\t\tbackground: #eee;\n\t\t\tborder: 1px solid;\n\t\t\topacity: 0.95;\n\t\t\tdisplay: flex;\n\t\t\tflex-direction: column;\n\t\t}\n\t\t.eveui_modal_overlay {\n\t\t\tcursor: pointer;\n\t\t\tposition: fixed;\n\t\t\tbackground: #000;\n\t\t\ttop: 0;\n\t\t\tleft: 0;\n\t\t\tright: 0;\n\t\t\tbottom: 0;\n\t\t\tz-index: 10;\n\t\t\topacity: 0.5;\n\t\t}\n\t\t.eveui_title {\n\t\t\twidth: 100%;\n\t\t\tbackground: #ccc;\n\t\t\tcursor: move;\n\t\t\twhite-space: nowrap;\n\t\t\tmargin-right: 2em;\n\t\t}\n\t\t.eveui_scrollable {\n\t\t\tpadding-right: 17px;\n\t\t\ttext-align: left;\n\t\t\toverflow: auto;\n\t\t}\n\t\t.eveui_content {\n\t\t\tdisplay: inline-block;\n\t\t\tmargin: 2px;\n\t\t\tmax-width: 30em;\n\t\t}\n\t\t.eveui_content div {\n\t\t\tdisplay: flex;\n\t\t}\n\t\t.eveui_content table {\n\t\t\tborder-collapse: collapse;\n\t\t}\n\t\t.eveui_content td {\n\t\t\tvertical-align: top;\n\t\t\tpadding: 0 2px;\n\t\t}\n\t\t.eveui_flexgrow {\n\t\t\tflex-grow: 1;\n\t\t}\n\t\t.eveui_fit_header {\n\t\t\talign-items: center;\n\t\t}\n\t\t.eveui_line_spacer {\n\t\t\tline-height: 0.5em;\n\t\t}\n\t\t.eveui_right {\n\t\t\ttext-align: right;\n\t\t}\n\t\t.eveui_icon {\n\t\t\tdisplay: inline-block;\n\t\t\tmargin: 1px;\n\t\t\tvertical-align: middle;\n\t\t\theight: 1em;\n\t\t\twidth: 1em;\n\t\t\tbackground-position: center;\n\t\t\tbackground-repeat: no-repeat;\n\t\t\tbackground-size: contain;\n\t\t}\n\t\t.eveui_item_icon {\n\t\t\theight: 20px;\n\t\t\twidth: 20px;\n\t\t}\n\t\t.eveui_ship_icon {\n\t\t\theight: 32px;\n\t\t\twidth: 32px;\n\t\t}\n\t\t.eveui_close_icon {\n\t\t\tcursor: pointer;\n\t\t\tposition: absolute;\n\t\t\ttop: 0;\n\t\t\tright: 0;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHg9IjciIHk9Ii0xIiB0cmFuc2Zvcm09Im1hdHJpeCgwLjcwNzEgLTAuNzA3MSAwLjcwNzEgMC43MDcxIC0zLjMxMzUgNy45OTk1KSIgd2lkdGg9IjIiIGhlaWdodD0iMTcuOTk5Ii8+CjxyZWN0IHg9IjciIHk9Ii0wLjk5OSIgdHJhbnNmb3JtPSJtYXRyaXgoLTAuNzA3MSAtMC43MDcxIDAuNzA3MSAtMC43MDcxIDcuOTk4OCAxOS4zMTQyKSIgd2lkdGg9IjIiIGhlaWdodD0iMTcuOTk5Ii8+PC9zdmc+Cg==);\n\t\t}\n\t\t.eveui_info_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTQ0OCAzODRjMzUgMCA2NC0yOSA2NC02NHMtMjktNjQtNjQtNjQtNjQgMjktNjQgNjQgMjkgNjQgNjQgNjR6IG0wLTMyMGMtMjQ3IDAtNDQ4IDIwMS00NDggNDQ4czIwMSA0NDggNDQ4IDQ0OCA0NDgtMjAxIDQ0OC00NDgtMjAxLTQ0OC00NDgtNDQ4eiBtMCA3NjhjLTE3NyAwLTMyMC0xNDMtMzIwLTMyMHMxNDMtMzIwIDMyMC0zMjAgMzIwIDE0MyAzMjAgMzIwLTE0MyAzMjAtMzIwIDMyMHogbTY0LTMyMGMwLTMyLTMyLTY0LTY0LTY0cy0zMiAwLTY0IDAtNjQgMzItNjQgNjRoNjRzMCAxNjAgMCAxOTIgMzIgNjQgNjQgNjQgMzIgMCA2NCAwIDY0LTMyIDY0LTY0aC02NHMwLTE2MCAwLTE5MnoiIC8+Cjwvc3ZnPgo=);\n\t\t}\n\t\t.eveui_plus_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI2NDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTM4NCA0NDhWMTkySDI1NnYyNTZIMHYxMjhoMjU2djI1NmgxMjhWNTc2aDI1NlY0NDhIMzg0eiIgLz4KPC9zdmc+Cg==);\n\t\t}\n\t\t.eveui_minus_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTAgNDQ4djEyOGg1MTJWNDQ4SDB6IiAvPgo8L3N2Zz4K);\n\t\t}\n\t\t.eveui_more_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI3NjgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTAgNTc2aDEyOHYtMTI4aC0xMjh2MTI4eiBtMC0yNTZoMTI4di0xMjhoLTEyOHYxMjh6IG0wIDUxMmgxMjh2LTEyOGgtMTI4djEyOHogbTI1Ni0yNTZoNTEydi0xMjhoLTUxMnYxMjh6IG0wLTI1Nmg1MTJ2LTEyOGgtNTEydjEyOHogbTAgNTEyaDUxMnYtMTI4aC01MTJ2MTI4eiIgLz4KPC9zdmc+Cg==);\n\t\t}\n\t\t.eveui_edit_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTcwNCA2NEw1NzYgMTkybDE5MiAxOTIgMTI4LTEyOEw3MDQgNjR6TTAgNzY4bDAuNjg4IDE5Mi41NjJMMTkyIDk2MGw1MTItNTEyTDUxMiAyNTYgMCA3Njh6TTE5MiA4OTZINjRWNzY4aDY0djY0aDY0Vjg5NnoiIC8+Cjwvc3ZnPgo=);\n\t\t}\n\t\t.eveui_copy_icon {\n\t\t\tcursor: pointer;\n\t\t\tbackground-image: url(data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjEwMjQiIHdpZHRoPSI4OTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZD0iTTcwNCA4OTZoLTY0MHYtNTc2aDY0MHYxOTJoNjR2LTMyMGMwLTM1LTI5LTY0LTY0LTY0aC0xOTJjMC03MS01Ny0xMjgtMTI4LTEyOHMtMTI4IDU3LTEyOCAxMjhoLTE5MmMtMzUgMC02NCAyOS02NCA2NHY3MDRjMCAzNSAyOSA2NCA2NCA2NGg2NDBjMzUgMCA2NC0yOSA2NC02NHYtMTI4aC02NHYxMjh6IG0tNTEyLTcwNGMyOSAwIDI5IDAgNjQgMHM2NC0yOSA2NC02NCAyOS02NCA2NC02NCA2NCAyOSA2NCA2NCAzMiA2NCA2NCA2NCAzMyAwIDY0IDAgNjQgMjkgNjQgNjRoLTUxMmMwLTM5IDI4LTY0IDY0LTY0eiBtLTY0IDUxMmgxMjh2LTY0aC0xMjh2NjR6IG00NDgtMTI4di0xMjhsLTI1NiAxOTIgMjU2IDE5MnYtMTI4aDMyMHYtMTI4aC0zMjB6IG0tNDQ4IDI1NmgxOTJ2LTY0aC0xOTJ2NjR6IG0zMjAtNDQ4aC0zMjB2NjRoMzIwdi02NHogbS0xOTIgMTI4aC0xMjh2NjRoMTI4di02NHoiIC8+Cjwvc3ZnPgo=);\n\t\t}\n\t\t.copy_only {\n\t\t\tposition: absolute;\n\t\t\tdisplay:inline-block;\n\t\t\tline-height: 0;\n\t\t\tfont-size: 0;\n\t\t}\n\t\t.nocopy::after {\n\t\t\tcontent: attr(data-content);\n\t\t}\n\t\t.whitespace_nowrap {\n\t\t\twhite-space: nowrap;\n\t\t}\n\t\t.float_left {\n\t\t\tfloat: left;\n\t\t}\n\t\t.float_right {\n\t\t\tfloat: right;\n\t\t}\n\t\t/* eveui_css_end */\n\t</style>\n",
    eveui;
! function(eveui) {
    function eve_version_query() {
        mark("eve version request"), $.ajax("https://crest-tq.eveonline.com/", {
            dataType: "json",
            cache: !0
        }).done(function(data) {
            if (eve_version = data.serverVersion, mark("eve version response " + eve_version), eveui_use_localstorage > 0) {
                var localstorage_cache = JSON.parse(localStorage.getItem("eveui_cache"));
                $.each(localstorage_cache, function(k, v) {
                    k.startsWith("EVE") ? k === eve_version ? $.extend(cache, v) : delete localstorage_cache[k] : Number(k) > Date.now() ? $.extend(cache, v) : delete localstorage_cache[k]
                }), localStorage.setItem("eveui_cache", JSON.stringify(localstorage_cache)), mark("localstorage cache loaded " + Object.keys(cache).length + " entries")
            }
            $(document).ready(function() {
                mark("expanding fits"), expand()
            }), preload_timer = setTimeout(lazy_preload, eveui_preload_interval), mark("preload timer set")
        }).fail(function(xhr) {
            mark("eve version request failed"), setTimeout(eve_version_query, 1e4)
        })
    }

    function new_window(title) {
        void 0 === title && (title = "&nbsp;");
        var eveui_window = $('\n\t\t\t<span class="eveui_window">\n\t\t\t\t<div class="eveui_title">' + title + '</div>\n\t\t\t\t<span class="eveui_icon eveui_close_icon" />\n\t\t\t\t<span class="eveui_scrollable">\n\t\t\t\t\t<span class="eveui_content">\n\t\t\t\t\t\tLoading...\n\t\t\t\t\t</span>\n\t\t\t\t</span>\n\t\t\t</span>\n\t\t');
        return "modal" === eveui_mode && 0 === $(".eveui_modal_overlay").length && ($("body").append('<div class="eveui_modal_overlay" />'), eveui_window.attr("data-eveui-modal", 1)), eveui_window.css("z-index", current_zindex++), eveui_window.css("left", mouse_x + 10), eveui_window.css("top", mouse_y - 10), eveui_window
    }

    function mark(mark) {

    }

    function format_fit(dna, eveui_name) {
        function item_rows(fittings, slots_available) {
            var html = "",
                slots_used = 0;
            for (var item_id in fittings) slots_used += fittings[item_id], html += slots_available ? '\n\t\t\t\t\t\t<tr class="copy_only">\n\t\t\t\t\t\t<td>\n\t\t\t\t\t\t\t' + (cache["inventory/types/" + item_id].name + "<br />").repeat(fittings[item_id]) + '\n\t\t\t\t\t\t<tr class="nocopy" data-eveui-itemid="' + item_id + '">\n\t\t\t\t\t\t\t<td><img src="https://imageserver.eveonline.com/Type/' + item_id + '_32.png" class="eveui_icon eveui_item_icon" />\n\t\t\t\t\t\t\t<td class="eveui_right">' + fittings[item_id] + "\n\t\t\t\t\t\t\t<td>" + cache["inventory/types/" + item_id].name + "\n\t\t\t\t\t\t" : '\n\t\t\t\t\t\t<tr class="copy_only">\n\t\t\t\t\t\t<td>\n\t\t\t\t\t\t\t' + cache["inventory/types/" + item_id].name + " x" + fittings[item_id] + '<br />\n\t\t\t\t\t\t<tr class="nocopy" data-eveui-itemid="' + item_id + '">\n\t\t\t\t\t\t\t<td><img src="https://imageserver.eveonline.com/Type/' + item_id + '_32.png" class="eveui_icon eveui_item_icon" />\n\t\t\t\t\t\t\t<td class="eveui_right">' + fittings[item_id] + "\n\t\t\t\t\t\t\t<td>" + cache["inventory/types/" + item_id].name + "\n\t\t\t\t\t\t", html += '\n\t\t\t\t\t<td class="eveui_right whitespace_nowrap"><span data-itemid="' + item_id + '" class="eveui_icon eveui_info_icon" />\n\t\t\t\t\t', eveui_allow_edit && (html += '\n\t\t\t\t\t\t<span class="eveui_icon eveui_plus_icon" />\n\t\t\t\t\t\t<span class="eveui_icon eveui_minus_icon" />\n\t\t\t\t\t\t<span class="eveui_icon eveui_more_icon" />\n\t\t\t\t\t\t');
            return "undefined" != typeof slots_available && (slots_available > slots_used && (html += '\n\t\t\t\t\t\t<tr class="nocopy">\n\t\t\t\t\t\t\t<td class="eveui_icon eveui_item_icon" />\n\t\t\t\t\t\t\t<td class="eveui_right whitespace_nowrap">' + (slots_available - slots_used) + "\n\t\t\t\t\t\t\t<td>Empty\n\t\t\t\t\t\t", eveui_allow_edit && (html += '<td class="eveui_right"><span class="eveui_more_icon" />')), slots_used > slots_available && (html += '\n\t\t\t\t\t\t<tr class="nocopy">\n\t\t\t\t\t\t\t<td class="eveui_icon eveui_item_icon" />\n\t\t\t\t\t\t\t<td class="eveui_right">' + (slots_available - slots_used) + "\n\t\t\t\t\t\t\t<td>Excess\n\t\t\t\t\t\t")), html
        }
        var high_slots = {},
            med_slots = {},
            low_slots = {},
            rig_slots = {},
            subsystem_slots = {},
            other_slots = {},
            items = dna.split(":"),
            ship_id = parseInt(items.shift()),
            ship = cache["inventory/types/" + ship_id];
        for (var i in ship.dogma.attributes) {
            var attr = cache["inventory/types/" + ship_id].dogma.attributes[i];
            "hiSlots" == attr.attribute.name ? ship[attr.attribute.name] = attr.value : "medSlots" == attr.attribute.name ? ship[attr.attribute.name] = attr.value : "lowSlots" == attr.attribute.name ? ship[attr.attribute.name] = attr.value : "rigSlots" == attr.attribute.name ? ship[attr.attribute.name] = attr.value : "maxSubSystems" == attr.attribute.name && (ship[attr.attribute.name] = attr.value)
        }
        outer: for (var item in items)
            if (0 != items[item].length) {
                var match = items[item].split(";"),
                    item_id = match[0],
                    quantity = parseInt(match[1]);
                for (var i in cache["inventory/types/" + item_id].dogma.effects) {
                    if ("hiPower" == cache["inventory/types/" + item_id].dogma.effects[i].effect.name) {
                        high_slots[item_id] = quantity;
                        continue outer
                    }
                    if ("medPower" == cache["inventory/types/" + item_id].dogma.effects[i].effect.name) {
                        med_slots[item_id] = quantity;
                        continue outer
                    }
                    if ("loPower" == cache["inventory/types/" + item_id].dogma.effects[i].effect.name) {
                        low_slots[item_id] = quantity;
                        continue outer
                    }
                    if ("rigSlot" == cache["inventory/types/" + item_id].dogma.effects[i].effect.name) {
                        rig_slots[item_id] = quantity;
                        continue outer
                    }
                    if ("subSystem" == cache["inventory/types/" + item_id].dogma.effects[i].effect.name) {
                        subsystem_slots[item_id] = quantity;
                        continue outer
                    }
                }
                other_slots[item_id] = quantity
            }
        var html = "";
        return html += '\n\t\t\t<table>\n\t\t\t<thead>\n\t\t\t<tr class="eveui_fit_header" data-eveui-itemid="' + ship_id + '">\n\t\t\t<td colspan="2"><img src="https://imageserver.eveonline.com/Type/' + ship_id + '_32.png" class="eveui_icon eveui_ship_icon" />\n\t\t\t<td>\n\t\t\t\t<span class="eveui_startcopy" />[' + cache["inventory/types/" + ship_id].name + ',\n\t\t\t\t<a target="_blank" href="' + eveui_urlify(dna) + '">' + (eveui_name || cache["inventory/types/" + ship_id].name) + '</a>]\n\t\t\t<td class="eveui_right whitespace_nowrap">\n\t\t\t<span class="eveui_icon clipboard_copy_icon" />\n\t\t\t<span data-itemid="' + ship_id + '" class="eveui_icon eveui_info_icon" />\n\t\t\t', eveui_allow_edit && (html += '\n\t\t\t\t<span class="eveui_icon" />\n\t\t\t\t<span class="eveui_icon" />\n\t\t\t\t<span class="eveui_icon eveui_more_icon" />\n\t\t\t\t'), html += '\n\t\t\t</thead>\n\t\t\t<tbody class="whitespace_nowrap">\n\t\t\t' + item_rows(high_slots, ship.hiSlots) + '\n\t\t\t<tr><td class="eveui_line_spacer">&nbsp;\n\t\t\t' + item_rows(med_slots, ship.medSlots) + '\n\t\t\t<tr><td class="eveui_line_spacer">&nbsp;\n\t\t\t' + item_rows(low_slots, ship.lowSlots) + '\n\t\t\t<tr><td class="eveui_line_spacer">&nbsp;\n\t\t\t' + item_rows(rig_slots, ship.rigSlots) + '\n\t\t\t<tr><td class="eveui_line_spacer">&nbsp;\n\t\t\t' + item_rows(subsystem_slots, ship.maxSubsystems) + '\n\t\t\t<tr><td class="eveui_line_spacer">&nbsp;\n\t\t\t' + item_rows(other_slots) + '\n\t\t\t</tbody>\n\t\t\t</table>\n\t\t\t<span class="eveui_endcopy" />\n\t\t\t'
    }

    function fit_window(dna, eveui_name) {
        var eveui_window = new_window("Fit");
        return eveui_window.addClass("fit_window"), eveui_window.attr("data-eveui-dna", dna), $("body").append(eveui_window), $(window).trigger("resize"), mark("fit window created"), cache_fit(dna).done(function() {
            var eveui_window = $('.eveui_window[data-eveui-dna="' + dna + '"]');
            eveui_window.find(".eveui_content ").html(format_fit(dna, eveui_name)), $(window).trigger("resize"), mark("fit window populated")
        }), eveui_window
    }

    function format_item(item_id) {
        var item = cache["inventory/types/" + item_id],
            html = "";
        html += '<table class="whitespace_nowrap">', html += "<tr><td>" + item.name;
        for (var i in item.dogma.attributes) {
            var attr = item.dogma.attributes[i];
            html += "<tr>", html += "<td>" + attr.attribute.name, html += "<td>" + attr.value
        }
        return html += "</table>"
    }

    function item_window(item_id) {
        var eveui_window = new_window("Item");
        switch (eveui_window.attr("data-eveui-itemid", item_id), eveui_window.addClass("item_window"), eveui_mode) {
            default: $("body").append(eveui_window)
        }
        return mark("item window created"), cache_request("inventory/types/" + item_id).done(function() {
            var eveui_window = $('.eveui_window[data-eveui-itemid="' + item_id + '"]');
            eveui_window.find(".eveui_content").html(format_item(item_id)), $(window).trigger("resize"), mark("item window populated")
        }).fail(function() {
            var eveui_window = $('.eveui_window[data-eveui-itemid="' + item_id + '"]');
            eveui_window.remove()
        }), $(window).trigger("resize"), eveui_window
    }

    function format_char(char_id) {
        var character = cache["characters/" + char_id],
            html = "";
        return html += "<table>", html += '\n\t\t\t<tr><td colspan="2">\n\t\t\t<img class="float_left" src="https://imageserver.eveonline.com/Character/' + character.id + '_128.jpg" height="128" width="128" />\n\t\t\t' + character.name + '\n\t\t\t<hr />\n\t\t\t<img class="float_left" src="https://imageserver.eveonline.com/Corporation/' + character.corporation.id_str + '_64.png" height="64" width="64" />\n\t\t\tMember of ' + character.corporation.name + "\n\t\t\t<tr><td>Bio:<td>" + character.description.replace(/<font[^>]+>/g, "<font>") + "\n\t\t\t", html += "</table>"
    }

    function char_window(char_id) {
        var eveui_window = new_window("Character");
        switch (eveui_window.attr("data-eveui-charid", char_id), eveui_window.addClass("char_window"), eveui_mode) {
            default: $("body").append(eveui_window)
        }
        return mark("char window created"), cache_request("characters/" + char_id).done(function() {
            var eveui_window = $('.eveui_window[data-eveui-charid="' + char_id + '"]');
            eveui_window.find(".eveui_content").html(format_char(char_id)), $(window).trigger("resize"), mark("char window populated")
        }).fail(function() {
            var eveui_window = $('.eveui_window[data-eveui-charid="' + char_id + '"]');
            eveui_window.remove()
        }), $(window).trigger("resize"), eveui_window
    }

    function expand() {
        var expand_filter = "[data-eveui-expand]";
        "expand_all" == eveui_mode && (expand_filter = "*"), $(eveui_fit_selector).filter(expand_filter).each(function() {
            var selected_element = $(this);
            if (!(selected_element.closest(".eveui_content").length > 0)) {
                var dna = selected_element.attr("data-dna") || this.href.substring(this.href.indexOf(":") + 1);
                cache_fit(dna).done(function() {
                    var eveui_name = $(this).text().trim();
                    selected_element.replaceWith('<span class="eveui_content eveui_fit">' + format_fit(dna, eveui_name) + "</span>"), mark("fit window expanded")
                })
            }
        }), $(eveui_item_selector).filter(expand_filter).each(function() {
            var selected_element = $(this);
            if (!(selected_element.closest(".eveui_content").length > 0)) {
                var item_id = selected_element.attr("data-itemid") || this.href.substring(this.href.indexOf(":") + 1);
                cache_request("inventory/types/" + item_id).done(function() {
                    selected_element.replaceWith('<span class="eveui_content eveui_item">' + format_item(item_id) + "</span>"), mark("item window expanded")
                })
            }
        }), $(eveui_char_selector).filter(expand_filter).each(function() {
            var selected_element = $(this);
            if (!(selected_element.closest(".eveui_content").length > 0)) {
                var char_id = selected_element.attr("data-charid") || this.href.substring(this.href.indexOf(":") + 1);
                cache_request("characters/" + char_id).done(function() {
                    selected_element.replaceWith('<span class="eveui_content eveui_char">' + format_char(char_id) + "</span>"), mark("char window expanded")
                })
            }
        })
    }

    function lazy_preload() {
        var action_taken = !1;
        preload_quota > 0 && $(eveui_fit_selector).not("[data-eveui-cached]").each(function(i) {
            var elem = $(this),
                dna = elem.data("dna") || this.href.substring(this.href.indexOf(":") + 1),
                cache = cache_fit(dna);
            "resolved" === cache.state() ? elem.attr("data-eveui-cached", 1) : (preload_quota--, action_taken = !0, cache.always(function() {
                clearTimeout(preload_timer), preload_timer = setTimeout(lazy_preload, eveui_preload_interval)
            }))
        }), action_taken || (preload_timer = setTimeout(lazy_preload, 5e3))
    }

    function cache_fit(dna) {
        var pending = [],
            items = dna.split(":");
        for (var item in items)
            if (0 != items[item].length) {
                var match = items[item].split(";"),
                    item_id = match[0];
                pending.push(cache_request("inventory/types/" + item_id))
            }
        return $.when.apply(null, pending)
    }

    function cache_request(endpoint) {
        return "object" == typeof cache[endpoint] ? "function" == typeof cache[endpoint].promise ? cache[endpoint] : $.Deferred().resolve() : cache[endpoint] = $.ajax("https://crest-tq.eveonline.com/" + endpoint + "/", {
            dataType: "json",
            cache: !0
        }).done(function(data) {
            if (cache[endpoint] = data, eveui_use_localstorage > 0) {
                var key;
                if (endpoint.startsWith("inventory/types") && (key = eve_version), "undefined" == typeof key) return;
                "object" != typeof localstorage_pending[key] && (localstorage_pending[key] = {}), localstorage_pending[key][endpoint] = data, clearTimeout(localstorage_timer), localstorage_timer = setTimeout(function() {
                    var localstorage_cache = JSON.parse(localStorage.getItem("eveui_cache")) || {};
                    $.extend(!0, localstorage_cache, localstorage_pending);
                    var localstorage_cache_json = JSON.stringify(localstorage_cache);
                    if (localstorage_pending = {}, localstorage_cache_json.length > eveui_use_localstorage) return void mark("localstorage limit exceeded");
                    try {
                        localStorage.setItem("eveui_cache", localstorage_cache_json), mark("localstorage updated")
                    } catch (err) {}
                }, 5e3)
            }
        }).fail(function(xhr) {
            404 == xhr.status || 403 == xhr.status || delete cache[endpoint]
        })
    }

    function clipboard_copy(element) {
        $(".nocopy").hide(), $(".copyonly").show();
        var selection = window.getSelection(),
            range = document.createRange();
        element.find(".eveui_startcopy").length ? (range.setStart(element.find(".eveui_startcopy")[0], 0), range.setEnd(element.find(".eveui_endcopy")[0], 0)) : range.selectNodeContents(element[0]), selection.removeAllRanges(), selection.addRange(range), document.execCommand("copy"), selection.removeAllRanges(), $(".nocopy").show(), $(".copyonly").hide()
    }
    mark("script start");
    var preload_timer, localstorage_timer, $ = jQuery,
        mouse_x = 0,
        mouse_y = 0,
        drag_element = null,
        drag_element_x = 0,
        drag_element_y = 0,
        current_zindex = 100,
        preload_quota = eveui_preload_initial,
        cache = {},
        eve_version = void 0,
        localstorage_pending = {};
    "undefined" == typeof Storage && (eveui_use_localstorage = -1), $("head").append(eveui_style), $(document).on("click", ".eveui_window .eveui_close_icon", function(e) {
        $(this).parent().remove(), 0 == $(".eveui_window").length && $(".eveui_modal_overlay").remove()
    }), $(document).on("click", ".eveui_modal_overlay", function(e) {
        $(".eveui_window").remove(), $(this).remove()
    }), $(document).on("click", eveui_fit_selector, function(e) {
        if (e.preventDefault(), preload_quota = eveui_preload_initial, this.eveui_window && document.contains(this.eveui_window[0])) return void this.eveui_window.remove();
        var dna = $(this).attr("data-dna") || this.href.substring(this.href.indexOf(":") + 1),
            eveui_name = $(this).attr("data-title") || $(this).text().trim();
        switch (eveui_mode) {
            case "expand":
            case "expand_all":
                $(this).attr("data-eveui-expand", 1), expand();
                break;
            default:
                this.eveui_window = fit_window(dna, eveui_name)
        }
    }), $(document).on("click", eveui_item_selector, function(e) {
        if (e.preventDefault(), this.eveui_window && document.contains(this.eveui_window[0])) return void this.eveui_window.remove();
        var item_id = $(this).attr("data-itemid") || this.href.substring(this.href.indexOf(":") + 1);
        switch (eveui_mode) {
            case "expand":
            case "expand_all":
                $(this).attr("data-eveui-expand", 1), expand();
                break;
            default:
                this.eveui_window = item_window(item_id)
        }
    }), $(document).on("click", eveui_char_selector, function(e) {
        if (e.preventDefault(), this.eveui_window && document.contains(this.eveui_window[0])) return void this.eveui_window.remove();
        var char_id = $(this).attr("data-charid") || this.href.substring(this.href.indexOf(":") + 1);
        switch (eveui_mode) {
            case "expand":
            case "expand_all":
                $(this).attr("data-eveui-expand", 1), expand();
                break;
            default:
                this.eveui_window = char_window(char_id)
        }
    }), $(document).on("click", ".eveui_minus_icon", function(e) {
        e.preventDefault();
        var item_id = $(this).closest("[data-eveui-itemid]").attr("data-eveui-itemid"),
            dna = $(this).closest("[data-eveui-dna]").attr("data-eveui-dna"),
            re = new RegExp(":" + item_id + ";(\\d+)"),
            new_quantity = parseInt(dna.match(re)[1]) - 1;
        dna = new_quantity > 0 ? dna.replace(re, ":" + item_id + ";" + new_quantity) : dna.replace(re, ""), $(this).closest("[data-eveui-dna]").attr("data-eveui-dna", dna), fit_window(dna)
    }), $(document).on("click", ".eveui_plus_icon", function(e) {
        e.preventDefault();
        var item_id = $(this).closest("[data-eveui-itemid]").attr("data-eveui-itemid"),
            dna = $(this).closest("[data-eveui-dna]").attr("data-eveui-dna"),
            re = new RegExp(":" + item_id + ";(\\d+)"),
            new_quantity = parseInt(dna.match(re)[1]) + 1;
        dna = new_quantity > 0 ? dna.replace(re, ":" + item_id + ";" + new_quantity) : dna.replace(re, ""), $(this).closest("[data-eveui-dna]").attr("data-eveui-dna", dna), fit_window(dna)
    }), $(document).on("click", ".eveui_more_icon", function(e) {
        e.preventDefault();
        var eveui_window = ($(this).closest("[data-eveui-itemid]").attr("data-eveui-itemid"), $(this).closest("[data-eveui-dna]").attr("data-eveui-dna"), $('\n\t\t\t<span class="eveui_window" style="position:absolute">\n\t\t\t\t<span class="eveui_close_icon" />\n\t\t\t\t<span class="eveui_content">\n\t\t\t\t\tAutocomplete goes here\n\t\t\t\t</span>\n\t\t\t</span>\n\t\t\t'));
        eveui_window.css("z-index", current_zindex++), $(this).parent().after(eveui_window)
    }), $(document).on("click", ".clipboard_copy_icon", function(e) {
        clipboard_copy($(this).closest(".eveui_window"))
    }), $(document).on("mousedown", ".eveui_window", function(e) {
        $(this).css("z-index", current_zindex++)
    }), $(document).on("mousedown", ".eveui_title", function(e) {
        e.preventDefault(), drag_element = $(this).parent(), drag_element_x = mouse_x - drag_element.position().left, drag_element_y = mouse_y - drag_element.position().top, drag_element.css("z-index", current_zindex++)
    }), $(document).on("mousemove", function(e) {
        mouse_x = e.clientX, mouse_y = e.clientY, null !== drag_element && (drag_element.css("left", mouse_x - drag_element_x), drag_element.css("top", mouse_y - drag_element_y))
    }), $(document).on("mouseup", function(e) {
        drag_element = null
    }), $(window).on("resize", function(e) {
        if ($(".eveui_window").each(function() {
                var eveui_window = $(this),
                    eveui_content = eveui_window.find(".eveui_content");
                eveui_content.height() > window.innerHeight - 50 ? eveui_window.css("height", window.innerHeight - 50) : eveui_window.css("height", ""), eveui_content.width() > window.innerWidth - 20 ? eveui_window.css("width", window.innerWidth - 20) : eveui_window.css("width", ""), eveui_window[0].getBoundingClientRect().bottom > window.innerHeight && eveui_window.css("top", window.innerHeight - eveui_window.height() - 25), eveui_window[0].getBoundingClientRect().right > window.innerWidth && eveui_window.css("left", window.innerWidth - eveui_window.width() - 10)
            }), "modal" == eveui_mode) {
            var eveui_window = $("[data-eveui-modal]");
            eveui_window.css("top", window.innerHeight / 2 - eveui_window.height() / 2), eveui_window.css("left", window.innerWidth / 2 - eveui_window.width() / 2)
        }
    }), mark("event handlers set"), eve_version_query(), eveui.format_fit = format_fit, eveui.fit_window = fit_window, eveui.format_item = format_item, eveui.item_window = item_window, eveui.format_char = format_char, eveui.char_window = char_window, eveui.expand = expand, String.prototype.repeat || (String.prototype.repeat = function(count) {
        "use strict";
        if (null == this) throw new TypeError("can't convert " + this + " to object");
        var str = "" + this;
        if (count = +count, count != count && (count = 0), count < 0) throw new RangeError("repeat count must be non-negative");
        if (count == 1 / 0) throw new RangeError("repeat count must be less than infinity");
        if (count = Math.floor(count), 0 == str.length || 0 == count) return "";
        if (str.length * count >= 1 << 28) throw new RangeError("repeat count must not overflow maximum string size");
        for (var rpt = ""; 1 == (1 & count) && (rpt += str), count >>>= 1, 0 != count;) str += str;
        return rpt
    }), String.prototype.startsWith || (String.prototype.startsWith = function(searchString, position) {
        return position = position || 0, this.substr(position, searchString.length) === searchString
    }), mark("script end")
}(eveui || (eveui = {}));