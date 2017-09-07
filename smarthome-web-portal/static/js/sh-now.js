/**
 * Scripts for the Now page
 */
$(function () {
    //Number of alert cards displayed on NOW page
    var alert_card_number = 0;

    // the token dict to store the last alert time for motion, gas, buzz and button sensors
    var alert_token = {};

    // check whether to update the sensor group list
    var dropdown_need_update = false;

    $.sh.now = {
        register_actions: function () {
            console.log('sh-now: register_actions');
            $("a:contains('DISMISS')").on("click", function () {
                //find parent div
                dismiss(this);
            });

            $("label.mdl-icon-toggle").on('click', function (e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                var unit = $(this).children("span:first").html();
                var temp = $(this).parent().prev().find("h1").html();
                if (temp.length == 0) return;
                if (unit == "C") {
                    unit = "F";
                    temp = convertToF(temp, 0);
                }
                else if (unit == "F") {
                    unit = "C";
                    temp = convertToC(temp, 0);
                }
                console.log('unit: ' + unit + ' temp: ' + temp);
                $(this).children("span:first").html(unit);
                $(this).parent().prev().find("h1").html(temp + '°');
            });

            $("#data-container, #alert-container").on('mouseover mouseout', '.mdl-card__title', function (e) {
                // show edit icon on mouse over
                if (e.type == "mouseover")
                    $(this).children(".edit").show();
                else
                    $(this).children(".edit").hide();
            });

            $("#status-container").on('mouseover mouseout', '.mdl-card__supporting-text .mdl-cell', function (e) {
                // show edit icon on mouse over
                if (e.type == "mouseover")
                    $(this).children(".edit").show();
                else
                    $(this).children(".edit").hide();
            });

            $("#alert-container, #status-container, #data-container").off('click', '.edit').on('click', '.edit', function (event) {
                // show text field
                var text = $(this).prev().text();

                var input = $('<input type="text" maxlength="30" value="' + text + '" required="required" />');
                input.data("initial", text);
                $(this).prev().text('').append(input);
                input.select();

                input.keydown(function () {
                    var title = $(this).parent().data("title");
                    var field = this;
                    setTimeout(function () {
                        if (field.value.indexOf(title) !== 0) {
                            $(field).val(title);
                        }
                    }, 1);
                });

                input.on("change focus blur", function () {
                    var prefix = $(this).parent().data("title");
                    var text = $(this).val();
                    var oldVal = $(this).data("initial");
                    var titleObj = $(this).parent();
                    var title = "Only alpha, digits, space, underscore, hyphen and dot are allowed.";
                    if (oldVal == text) {
                        $(this).parent().text(text);
                        $(this).remove();
                        return;
                    }

                    // validate the input
                    var regex = new RegExp('^[a-zA-Z]+[-A-Za-z0-9_. ]{1,30}$');
                    if (!regex.test(text)) {
                        console.log("Input validation failed, try again.");
                        $(this).select();
                        $(this).after('<span class="tooltiptext">' + title + '</span>');
                        return;
                    }

                    $(this).nextAll().remove();

                    // get resource id from different sensor types
                    var resource_id;
                    var sensor_type = "";
                    if ($(this).closest(".demo-card-event").length > 0) {
                        var res_id = $(this).closest(".demo-card-event").attr("id");
                        resource_id = res_id.split('-')[1];
                    }
                    else if ($(this).closest(".status-card").length > 0)
                        resource_id = $(this).closest(".mdl-card__supporting-text").find(".mdl-card__menu").attr("data-ID");
                    else if ($(this).closest(".sensor-card").length > 0) {
                        resource_id = $(this).closest(".sensor-card").find("h1").attr("data-ID");
                        sensor_type = $(this).closest(".sensor-card").find("h1").attr("data-type");
                    }
                    var tag = text.substring(prefix.length, text.length);
                    titleObj.text(text);
                    $(this).remove();

                    $.sh.now.update_sensor_title(resource_id, tag, sensor_type, oldVal, titleObj);
                });
            });

            $("#data-container, #alert-container, #status-container, #activity-container").on('click', 'li', function (e) {
                if ($(e.target).text().indexOf('Add Group') > -1) {
                    showDialog({
                        title: 'Add New Group',
                        content: '<table>\
                                    <tbody>\
                                        <tr><td>Group Name: </td>\
                                            <td><input type="text" pattern="^[a-zA-Z]+[-A-Za-z0-9_. ]{1,30}$" maxlength="30" required></td>\
                                        </tr>\
                                        <tr><td>Color: </td>\
                                            <td>\
                                                <input id="color-picker" type="text"></td>\
                                        </tr>\
                                    </tbody>\
                                  </table>',
                        negative: {
                            title: 'Cancel',
                        },
                        positive: {
                            title: 'Submit',
                            onClick: function () {
                                var textbox = $("#orrsDiag input:required");
                                if ($("#orrsDiag input:valid").length > 1) {
                                    var name = textbox.val();
                                    var color = $("#color-picker").spectrum('get').toHexString();
                                    if (getCookie('gateway_id')) {
                                        var data = {
                                            'name': name,
                                            'color': color,
                                            'gateway_id': parseInt(getCookie('gateway_id')),
                                        };
                                        $.ajax({
                                            url: "/add_sensor_group",
                                            type: "POST",
                                            data: JSON.stringify(data),
                                            dataType: "json",
                                            contentType: "application/json; charset=utf-8",
                                            success: function (data) {
                                                $.sh.now.append_sensor_group(data);
                                                createSnackbar("Sensor group '" + data.name + "' is added.", 'Dismiss');
                                            }
                                        }).fail(function (jqXHR, textStatus, errorThrown) {
                                            createSnackbar("Failed to add sensor group: " + errorThrown, "Dismiss");
                                        });
                                    }
                                }
                            }
                        }
                    });
                    $('#color-picker').spectrum({
                        showPaletteOnly: true,
                        showPalette: true,
                        hideAfterPaletteSelect: true,
                        color: 'blanchedalmond',
                        palette: [
                            ['black', 'white', 'blanchedalmond',
                                'rgb(255, 128, 0);', 'hsv 100 70 50'],
                            ['red', 'yellow', 'green', 'blue', 'violet']
                        ],
                    });
                }
                else {
                    var color = $(this).css("color");
                    var gid = $(this).data("cid");
                    var title = $(this).closest(".mdl-card__title");
                    if (title.length == 0)
                        title = $(this).closest(".mdl-card__supporting-text");
                    var buttonId = title.find("button").attr('id');
                    var bid = buttonId.split('-').pop();
                    var buttonElem = $("button[id$=" + bid + "]");

                    // invalid select
                    if (buttonElem.css('background-color') == color) return;

                    if (gid == 0) gid = null;
                    var value = {
                        'resource_id': bid,
                        'value': {
                            "sensor_group_id": gid,
                        }
                    }
                    $.sh.now._update_sensor_group(value, color, buttonElem);
                }
            });

            // update brillo rgbled
            $("#brillo-container").on('change', ".basic", function (e, color) {
                /* data format :
                 { "rgbValue" : [255,255,255] }
                 */
                var value = {
                    'rgbValue': convertToStr(color)
                };
                // console.log("res id:" + $(this).data('id'));
                // console.log("value: " + value);
                update_sensor_status($(this).data('id'), value, $(this), function (data) {
                    console.log(data);
                    var ret = data.status;
                    if (ret) {
                        console.log("Brillo rgbled color is updated.");
                        createSnackbar('Brillo rgbled color is updated.', 'Dismiss');
                    }
                });
            });

            // update brillo playlist
            $("#brillo-container").on('change', "select", function () {
                /* data format :
                 { "select" : 0 }
                 */
                var value = {
                    "select": parseInt($(this).val())
                };
                // console.log("res id:" + $(this).parent().data('id'));
                // console.log("value: " + value);
                update_sensor_status($(this).data('id'), value, $(this), function (data) {
                    var ret = data.status;
                    if (ret) {
                        createSnackbar('Brillo mp3player playlist is updated.', 'Dismiss');
                    }
                });
            });

            // update brillo play/pause
            $("#brillo-container").on('click', "button", function () {
                /* data format :
                 { "state" : "Paused" }
                 */
                var buttonId = $(this).attr('id');
                var resId = buttonId.split('-').pop();
                var playlist = $(this).parent().find("select");
                var value;
                if (buttonId.indexOf("brillo-pause") == 0) {
                    if (playlist.val()) {
                        if ($(this).children("i").html() == "play_arrow")
                            value = {
                                "state": "Playing"
                            };
                        if ($(this).children("i").html() == "pause")
                            value = {
                                "state": "Paused"
                            };
                    }
                    else {
                        createSnackbar('Brillo mp3player has no song selected.', 'Dismiss');
                        return false;
                    }
                }
                else if (buttonId.indexOf("brillo-clear") == 0) {
                    if (playlist.val()) {
                        value = {
                            "state": "Idle"
                        }
                    }
                    else {
                        createSnackbar('Brillo mp3player is already in Idle state.', 'Dismiss');
                        return false;
                    }
                }
                if (value) {
                    update_sensor_status(parseInt(resId), value, null, function (data) {
                        var ret = data.status;
                        if (ret) {
                            createSnackbar('Brillo mp3player state is updated.', 'Dismiss');
                        }
                    });
                }
            });

            // update brillo brightness
            $("#brillo-container").on('mouseup', ".brightness", function () {
                /* data format :
                 { "brightness" : 10 }
                 */
                var value = {
                    "brightness": parseInt($(this).val())
                };
                // console.log("res id:" + $(this).parent().data('id'));
                // console.log("value: " + value);
                update_sensor_status($(this).data('id'), value, $(this), function (data) {
                    var ret = data.status;
                    if (ret) {
                        createSnackbar('Brillo mp3player brightness is updated.', 'Dismiss');
                    }
                });
            });

            // update brillo volume
            $("#brillo-container").on('mouseup', ".volume", function () {
                /* data format :
                 { "volume" : 10 }
                 */
                var value = {
                    "volume": parseInt($(this).val())
                };
                // console.log("res id:" + $(this).parent().data('id'));
                // console.log("value: " + value);
                update_sensor_status($(this).data('id'), value, $(this), function (data) {
                    var ret = data.status;
                    if (ret) {
                        createSnackbar('Brillo mp3player volume is updated.', 'Dismiss');
                    }
                });
            });

            // update brillo volume mute
            $("#brillo-container").on('click', "label", function (e) {
                /* data format :
                 { "mute" : true }
                 */
                var switchIcon = $(this).children("input");
                var value = {
                    "mute": switchIcon[0].checked
                };
                // console.log("res id:" + $(this).parent().data('id'));
                // console.log("value: " + value);
                update_sensor_status(switchIcon.data('id'), value, null, function (data) {
                    var ret = data.status;
                    if (ret) {
                        createSnackbar('Brillo mp3player mute status is updated', 'Dismiss');
                    }
                });
                return false;
            });

            $("#generic-container").on('click', '.edit', function () {
                // show text field
                var text = $(this).closest("td").prev().text();
                var tbody = $(this).closest("tbody");
                var row = $(this).closest("tr");
                var pos = row.position();

                // calculate div top
                var top = pos.top - tbody.position().top;
                if (row.index() % 2 !== 0) {
                    top = top - row.height();
                }
                if (row.index === tbody.children('tr').length - 1) {
                    top = top - row.height();
                }

                var div = document.createElement('div');
                var DATA_TYPE = ['-----', 'int', 'float', 'string', 'bool', 'null', 'array', 'dict'];
                var options = '';
                $.each(DATA_TYPE, function (indx, elem) {
                    options += String.format('<option value={0}>{1}</option>', indx, elem);
                });

                $(div).addClass("overlay")
                    .html(String.format('<input type="text" required="required" placeholder="{0}">\
                    <select>\
                    {1}\
                    </select>\
                    <i class="material-icons update">save</i>\
                    <i class="material-icons cancel">cancel</i>', text, options))
                    .css({
                        position: 'absolute',
                        top: top,
                        left: pos.left,
                        width: row.width(),
                        height: row.height(),
                        "z-index": 10000,
                        "background-color": "Silver",
                        opacity: 0.8
                    })
                    .appendTo($(this).closest("tr"));
                $(div).click(function (e) {
                    e.stopPropagation();
                });

                $(div).children(".update").click(function () {
                    // input validation
                    var text = $(this).parent().find("input").val();
                    var input = $(this).parent().find("input");
                    var select = $(this).parent().find("select");
                    var key = $(this).closest("tr").find("td:first").text();
                    var resource_id = $(this).closest("table").data("id");
                    var overlay = $(this).closest(".overlay");
                    var data = {};

                    //reset validation
                    input[0].setCustomValidity("");
                    select[0].setCustomValidity("");

                    if (text.length == 0) {
                        input[0].setCustomValidity("Value is empty.");
                        input.select();
                        return;
                    }

                    switch (select[0].value) {
                        case "0":
                            select.select();
                            select[0].setCustomValidity("Data type is empty.");
                            return;
                        case "1":
                            // int
                            if ($.isNumeric(text)) {
                                data[key] = parseInt(text);
                            }
                            else {
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            break;
                        case "2":
                            // float
                            if ($.isNumeric(text)) {
                                data[key] = parseFloat(text).toFixed(2);
                            }
                            else {
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            break;
                        case "3":
                            // string
                            data[key] = text;
                            if (!isJSON(JSON.stringify(data))) {
                                //the json is not ok
                                //var title = "Expecting 'STRING', 'NUMBER', 'NULL', 'TRUE', 'FALSE', '{', '['. ";
                                delete data[key];
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            break;
                        case "4":
                            // bool
                            var bool = JSON.parse(text);
                            if (bool !== true && bool !== false) {
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            else
                                data[key] = bool;
                            break;
                        case "5":
                            // null
                            var nul = JSON.parse(text);
                            if (nul !== null) {
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            else
                                data[key] = nul;
                            break;
                        case "6":
                        case "7":
                            // array, dict
                            if (!isJSON(text)) {
                                //the json is not ok
                                input[0].setCustomValidity("Value and data type mismatches.");
                                input.select();
                                return;
                            }
                            else
                                data[key] = JSON.parse(text);
                            break;
                    }

                    console.log("the post json data: " + JSON.stringify(data));
                    update_sensor_status(resource_id, data, null, function (data) {
                        createSnackbar('Resource ' + resource_id + '\'s property is updated.', 'Dismiss');
                        overlay.remove();
                    });
                });

                $(div).children(".cancel").click(function () {
                    $(this).parent().remove();
                });

                $(div).children("select, input").on("change", function () {
                    $(this)[0].setCustomValidity("");
                });

                $(div).find("input").select();
            });
        },
        _update_sensor_group: function (value, color, buttonElem) {
            $.ajax({
                type: "POST",
                url: "/update_sensor_attr",
                contentType: 'application/json',
                data: JSON.stringify(value),
                success: function (data) {
                    var resource_id = data.resource_id;
                    if (resource_id) {
                        buttonElem.css('background', color);
                        createSnackbar('Sensor group for resource ' + resource_id + ' is updated.', 'Dismiss');
                    }
                }
            }).done(function () {
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error("Failed to update sensor group: " + errorThrown);
                createSnackbar("Server error: " + errorThrown, 'Dismiss');
            });
        },
        update_sensor_title: function (resource_id, title, sensor_type, oldVal, titleObj) {
            if (sensor_type.length > 0)
                sensor_type = sensor_type.toLowerCase();
            $.ajax({
                type: "POST",
                url: "/update_sensor_attr",
                contentType: 'application/json',
                data: JSON.stringify({
                    "resource_id": resource_id,
                    "type": sensor_type.toLowerCase(),
                    "value": {'tag': title},
                }),
                success: function (data) {
                    // console.log(data);
                    // data = JSON.parse(data);
                    var resource_id = data.resource_id;
                    if (resource_id) {
                        createSnackbar('Sensor ' + resource_id + ' is updated.', 'Dismiss');
                    }
                }
            }).done(function () {
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error("Failed to update status " + errorThrown);
                createSnackbar("Server error: " + errorThrown, 'Dismiss');
                //change the title back if fail
                $(titleObj).text(oldVal);
            });
        },
        update_sensor_group: function () {
            if (dropdown_need_update) {
                $.getJSON("/get_groups", function (data) {
                    var grps = data.sensor_groups;
                    $(".sensor-card ul, .demo-card-event ul, .status-card ul").each(function () {
                        var ulElem = $(this);
                        if (isArray(grps)) {
                            ulElem.html("");
                            $('<li/>').addClass('mdl-menu__item')
                                .addClass('mdl-menu__item--full-bleed-divider')
                                .css('color', '#fff')
                                .data('cid', 0)
                                .html("<span>Clear Group</span>")
                                .appendTo(ulElem);
                            $.each(grps, function (idx, group) {
                                $('<li/>').addClass('mdl-menu__item')
                                    .css('color', group['color'])
                                    .data('cid', group['id'])
                                    .html("<span>" + group['name'] + "</span>")
                                    .appendTo(ulElem);
                            });
                            $('<li/>').addClass('mdl-menu__item--full-bleed-divider-top')
                                .addClass('mdl-menu__item')
                                .css('color', '#fff')
                                .html("<span>Add Group</span>")
                                .appendTo(ulElem);
                        }
                    });
                    dropdown_need_update = false;
                }).fail(function (jqXHR, textStatus, errorThrown) {
                    console.error("Failed to update status " + errorThrown);
                });
            }
        },
        append_sensor_group: function (data) {
            $(".sensor-card ul, .demo-card-event ul, .status-card ul").each(function () {
                var len = $(this).children("li").length;
                var liElem = $(this).children("li:eq(" + (len - 2) + ")");
                $('<li/>').addClass('mdl-menu__item')
                    .css('color', data['color'])
                    .data('cid', data['id'])
                    .html("<span>" + data['name'] + "</span>")
                    .insertAfter(liElem);
            });
        },
        clear_data: function (data) {
            var types = ["status", "data", "activity"];
            var sensor_list = [];
            types.forEach(function (type) {
                $.each(data[type], function (key, value_list) {
                    if(type == "activity"){
                        if(value_list.resource_id != null)
                            sensor_list.push(value_list.resource_id.toString());
                    }
                    else{
                        value_list.forEach(function (value) {
                            var id = value.resource_id.toString();
                            if (!sensor_list.includes(id))
                                sensor_list.push(id);
                        });
                    }
                });
            });
            $('#data-container .sensor-card h1').each(function () {
                var ID = $(this).attr('data-ID');
                if (!sensor_list.includes(ID)) {
                    // remove the sensor card
                    // console.log('remove sensor:' + ID);
                    $(this).closest(".sensor-card").remove();
                }
            });
            $('.status-card .mdl-card__menu').each(function () {
                var ID = $(this).attr('data-ID');
                if (!sensor_list.includes(ID)) {
                    $(this).closest(".status-card").remove();
                }
            });
            $('#activity-container .sensor-card h1').each(function () {
                var ID = $(this).attr('data-ID');
                if (!sensor_list.includes(ID)) {
                    $(this).closest(".sensor-card").remove();
                }
            });
            $.sh.now.clear_brillo_data(data);
            $.sh.now.clear_generic_data(data);
        },
        clear_brillo_data: function (data) {
            if (Object.keys(data["brillo"]).length > 0) {
                $('#brillo-container').show();
                var sensor_list = Object.keys(data["brillo"]);
                $('#brillo-container .mdl-card__supporting-text').each(function () {
                    var ID = $(this).attr('id');
                    if (!sensor_list.includes(ID)) {
                        $(this).parent(".demo-card-data").remove();
                    }
                });
            }
            else {
                $('#brillo-container').hide();
            }
        },
        clear_generic_data: function (data) {
            if (Object.keys(data["data"]).length > 0)
                $('#data-container').show();
            else
                $('#data-container').hide();
            var g_list = Object.keys(data["generic"]);
            $('#generic-container .mdl-card__supporting-text table').each(function () {
                var ID = $(this).data('id') + '';
                if (!g_list.includes(ID)) {
                    $(this).closest(".generic").remove();
                }
            });
        },
        dismiss_alert_card: function (obj) {
            dismiss(obj);
            alert_card_number--;
            console.log("number of alert cards " + alert_card_number);
            if (alert_card_number <= 0) {
                $("#alert-status-title-quiet").show();
                $("#alert-status-title-alerts").hide();
            }
        },
        update_car_alert: function (data, show_uuid) {
            var uuid_txt = "";
            var time;
            if (data.value.length == 0) return;
            time = getTime(data.value, utc_offset, timezone);
            if (show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "ELECTRIC CAR ";
            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

            if ($("#" + card_id).length > 0) {
                //find the car card and update time
                if (time) {
                    var txt = $("#" + card_id + " > .mdl-card__supporting-text > .section__circle-container > h4:contains('Charge')");
                    txt.text("Charge car in time for tomorrow " + time);
                }
                var uid = $("#" + card_id + " > .mdl-card__subtitle-text");
                uid.text(uuid_txt);
            }
            else {
                $("#alert-container").append(String.format('<div id="{0}" class="demo-card-event mdl-card mdl-cell mdl-cell--3-col mdl-shadow--2dp">\
				  <div class="mdl-card__title mdl-card--expand" style="display: flex; flex-flow: row wrap;">\
				    <button id="{4}-{5}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{6}" title="{7}">\
                    </button>\
                    <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{5}">\
                    </ul>\
					<h6 data-title="{4}">{3}</h6>\
					<i class="material-icons edit" style="display: none;">edit</i>\
				  </div>\
				  <span class="mdl-card__subtitle-text" style="font-size: 70%">{1}</span>\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
					<div class="section__circle-container mdl-cell mdl-cell--8-col">\
						<h4>Charge car in time for tomorrow {2}</h4>\
					</div>\
					<div class="section__text mdl-cell mdl-cell--4-col" style="text-align:center;">\
						<img src="image/car-icon.png" style="width: 75%; height:75%;">\
					</div>\
				  </div>\
				  <div class="mdl-card__actions mdl-card--border">\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect" style="color: #000" onclick="$.sh.now.dismiss_alert_card(this);">\
					  DISMISS\
					</a>\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect" style="color: #000">SET TIMER</a>\
				  </div>\
				</div>', card_id, uuid_txt, time, tag, title, data.resource_id, data.color.color, data.color.name));

                alert_card_number++;
                dropdown_need_update = true;
            }
        },
        update_motion_alert: function (data, show_uuid) {
            var uuid_txt = "";
            var time;
            if (data.value.length == 0) return;
            time = getTime(data.value, utc_offset, timezone);
            if (show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "MOTION SENSOR";
            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

            if ($("#" + card_id).length > 0) {
                //find the motion card and update time
                if (time) {
                    var txt = $("#" + card_id + " > .mdl-card__supporting-text > .section__circle-container > h4:contains('Someone')");
                    txt.text("Someone is at the front door " + time);
                }
                var uid = $("#" + card_id + " > .mdl-card__subtitle-text");
                uid.text(uuid_txt);
            }
            else {
                $("#alert-container").append(String.format('<div id ="{0}" class="demo-card-event mdl-card mdl-cell mdl-cell--3-col mdl-shadow--2dp">\
				  <div class="mdl-card__title mdl-card--expand" style="display: flex; flex-flow: row wrap;">\
				    <button id="{4}-{5}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{6}" title="{7}">\
                    </button>\
                    <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{5}">\
                    </ul>\
					<h6 data-title="{4}">{3}</h6>\
					<i class="material-icons edit" style="display: none;">edit</i>\
				  </div>\
				  <span class="mdl-card__subtitle-text" style="font-size: 70%">{1}</span>\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
					<div class="section__circle-container mdl-cell mdl-cell--8-col">\
						<h4>Someone is at the front door {2}</h4>\
					</div>\
					<div class="section__text mdl-cell mdl-cell--4-col" style="text-align:center;">\
						<img src="image/motion-icon.png">\
					</div>\
				  </div>\
				  <div class="mdl-card__actions mdl-card--border">\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect" onclick="$.sh.now.dismiss_alert_card(this);">\
					  DISMISS\
					</a>\
				  </div>\
				</div>', card_id, uuid_txt, time, tag, title, data.resource_id, data.color.color, data.color.name));

                alert_card_number++;
                dropdown_need_update = true;
            }
        },
        update_gas_alert: function (data, show_uuid) {
            var uuid_txt = "";
            var time;

            if (data.value.length == 0) return;
            time = getTime(data.value, utc_offset, timezone);
            if (show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "CO2 SENSOR";
            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

            if ($("#" + card_id).length > 0) {
                //find the gas card and update time
                if (time) {
                    var txt = $("#" + card_id + " > .mdl-card__supporting-text > .section__circle-container > h4:contains('Gas')");
                    txt.text("Gas detected in kitchen area " + time);
                }
                var uid = $("#" + card_id + " > .mdl-card__subtitle-text");
                uid.text(uuid_txt);
            }
            else {
                $("#alert-container").append(String.format('<div id="{0}" class="demo-card-event mdl-card mdl-cell mdl-cell--3-col mdl-shadow--2dp" style="background: #ed0042;">\
				  <div class="mdl-card__title mdl-card--expand" style="display: flex; flex-flow: row wrap;">\
				    <button id="{4}-{5}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{6}" title="{7}">\
                    </button>\
                    <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{5}">\
                    </ul>\
					<h6 style="color: #fff;" data-title="{4}">{3}</h6>\
					<i class="material-icons edit" style="display: none; color: #fff;">edit</i>\
				  </div>\
				  <span class="mdl-card__subtitle-text" style="font-size: 70%; color: #fff;">{1}</span>\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
					<div class="section__circle-container mdl-cell mdl-cell--8-col">\
						<h4 style="color: #fff;">Gas detected in kitchen area {2}</h4>\
					</div>\
					<div class="section__text mdl-cell mdl-cell--4-col" style="text-align:center;">\
						<img src="image/gas-icon.png">\
					</div>\
				  </div>\
				  <div class="mdl-card__actions mdl-card--border">\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect" onclick="$.sh.now.dismiss_alert_card(this);"  style="color: #fff;">\
					  DISMISS\
					</a>\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect"  style="color: #fff;">EMERGENCY</a>\
				  </div>\
				</div>', card_id, uuid_txt, time, tag, title, data.resource_id, data.color.color, data.color.name));

                alert_card_number++;
                dropdown_need_update = true;
            }
        },
        update_buzzer_alert: function (data, show_uuid) {
            var uuid_txt = "";
            var time;

            if (data.value.length == 0) return;
            time = getTime(data.value, utc_offset, timezone);

            if (show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "BUZZER";
            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var card_id = "resource-" + data.resource_id;

            if ($("#" + card_id).length > 0) {
                //find the buzzer card and update time
                if (time) {
                    var txt = $("#" + card_id + " > .mdl-card__supporting-text > .section__circle-container > h1");
                    txt.text(time);
                }
                var uid = $("#" + card_id + " > .mdl-card__subtitle-text");
                uid.text(uuid_txt);
            }
            else {
                $("#alert-container").append(String.format('<div id="{0}" class="demo-card-event mdl-card mdl-cell mdl-cell--3-col mdl-shadow--2dp">\
				  <div class="mdl-card__title mdl-card--expand" style="display: flex; flex-flow: row wrap;">\
				    <button id="{4}-{5}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{6}" title="{7}">\
                    </button>\
                    <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{5}">\
                    </ul>\
					<h6 data-title="{4}">{3}</h6>\
					<i class="material-icons edit" style="display: none;">edit</i>\
				  </div>\
				  <span class="mdl-card__subtitle-text" style="font-size: 70%">{1}</span>\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
					<div class="section__circle-container mdl-cell mdl-cell--8-col">\
						<h1>{2}</h1>\
					</div>\
					<div class="section__text mdl-cell mdl-cell--4-col" style="text-align:center;">\
						<img src="image/buzzer-icon.png">\
					</div>\
				  </div>\
				  <div class="mdl-card__actions mdl-card--border">\
					<a class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect" onclick="$.sh.now.dismiss_alert_card(this);">\
					  DISMISS\
					</a>\
				  </div>\
				</div>', card_id, uuid_txt, time, tag, title, data.resource_id, data.color.color, data.color.name));

                alert_card_number++;
                dropdown_need_update = true;
            }
        },
        update_status: function (type, data, show_uuid) {
            var color = "gray";
            var uuid_cell = "";
            if (data.value)
                color = "green";

            if (show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var tag = type;
            if (data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id + "'] i");

            if (menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
                      <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%;display:inline-block;">\
                            <button id="{4}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{5}" title="{6}">\
                            </button>\
                            <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{2}">\
                            </ul>\
                            <div class="mdl-cell mdl-cell--9-col" style="display: inline-flex;">\
                                <h6 title="{1}" data-title="{4}">{0}</h6>\
                                <i class="material-icons edit" style="display: none; margin-top: 1em; ">edit</i>\
                            </div>\
                          <div data-ID="{2}" class="mdl-card__menu">\
                              <i class="material-icons {3}">done</i>\
                          </div>\
                      </div>\
                    </div>', tag, uuid_cell, data.resource_id, color, type, data.color.color, data.color.name));
                var len = $(".status-card").length;
                if (len > 0) {
                    var zindex = 100 - len - 1;
                    $(".status-card").last().css("z-index", zindex);
                }
                dropdown_need_update = true;
            }
            else {
                menu.removeClass().addClass("material-icons " + color);
                var uid = menu.parent().prev().children('h6');
                uid.attr("title", uuid_cell);
            }
        },
        update_switch_status: function (data, title, show_uuid) {
            var uuid_cell = "";
            if (show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id + "'] label");

            if (menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%; display: inline-block">\
                        <button id="{3}-{1}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{4}" title="{5}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{3}-{1}">\
                        </ul>\
                        <div class="mdl-cell mdl-cell--9-col" style="display: inline-flex;">\
                            <h6 title="{0}" data-title="{3}">{2}</h6>\
                            <i class="material-icons edit" style="display: none; margin-top: 1em; ">edit</i>\
                        </div>\
					  <div data-ID="{1}" class="mdl-card__menu">\
						  <label title="switch on/off" class="mdl-switch mdl-js-switch mdl-js-ripple-effect" for="res-{1}">\
      						<input type="checkbox" id="res-{1}" class="mdl-switch__input" onclick="return toggle_status({1}, this, \'{3}\');">\
      						<span class="mdl-switch__label"></span>\
    					  </label>\
					  </div>\
				  </div>\
				</div>', uuid_cell, data.resource_id, tag, title, data.color.color, data.color.name));
                $("input[id=res-" + data.resource_id + "]").prop('checked', data.value);
                var len = $(".status-card").length;
                if (len > 0) {
                    var zindex = 100 - len - 1;
                    $(".status-card").last().css("z-index", zindex);
                }
                dropdown_need_update = true;
            }
            else {
                // toggle switch on/off
                var status = menu.find("input")[0].checked;
                if (status !== data.value) {
                    if (status) {
                        menu[0].MaterialSwitch.off();
                    }
                    else {
                        menu[0].MaterialSwitch.on();
                    }
                }
                var uid = menu.parent().prev().children('h6');
                uid.attr("title", uuid_cell);
            }
            // Expand all new MDL elements
            componentHandler.upgradeDom();
        },
        update_rgb_status: function (data, show_uuid) {
            var bgcolor = "bg-blue";
            var uuid_cell = "";
            if (data.value)
                bgcolor = "bg-red";

            if (show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var title = "RGB LED";
            var tag = title;
            if (data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id + "'] i");
            if (menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
                  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%;display: inline-block">\
                        <button id="{4}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{5}" title="{6}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{2}">\
                        </ul>\
                        <div class="mdl-cell mdl-cell--9-col" style="display: inline-flex">\
                            <h6 title="{1}" data-title="{4}">{3}</h6>\
                            <i class="material-icons edit" style="display: none; margin-top: 1em; ">edit</i>\
                        </div>\
                      <div data-ID="{2}" class="mdl-card__menu">\
                          <i class="material-icons {0}">lightbulb_outline</i>\
                      </div>\
                  </div>\
                </div>', bgcolor, uuid_cell, data.resource_id, tag, title, data.color.color, data.color.name));
                var len = $(".status-card").length;
                if (len > 0) {
                    var zindex = 100 - len - 1;
                    $(".status-card").last().css("z-index", zindex);
                }
                dropdown_need_update = true;
            }
            else {
                menu.removeClass().addClass("material-icons " + bgcolor);
                var uid = menu.parent().prev().children('h6');
                uid.attr("title", uuid_cell);
            }
        },
        update_sensor_data_without_unit: function (title, data, show_uuid) {
            this.update_sensor_data(title, data, '', show_uuid);
        },
        update_sensor_data: function (title, data, unit, show_uuid) {
            var uuid_cell = '';
            if (show_uuid)
                uuid_cell = '<span class="mdl-card__subtitle-text" style="font-size: 70%; flex-basis: 100%;">ID: '
                    + data.uuid + ':' + data.path + '</span>';

            var value = $("#data-container .sensor-card h1[data-ID='" + data.resource_id + "'][data-type='" + title + "']");

            var type = title;
            if (data.tag)
                type = type + data.tag;

            if (value.length == 0) {
                var html = String.format('<div class="sensor-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--3-col">\
                    <div class="mdl-card__title" style="display: flex; flex-flow: row wrap;">\
                        <button id="{5}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{6}" title="{7}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{5}-{2}">\
                        </ul>\
			  	        <h6 data-title="{0}">{5}</h6>\
			  	        <i class="material-icons edit" style="display: none;">edit</i>\
			  	        {1}\
                    </div>\
                    <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
                        <div class="mdl-cell mdl-cell--12-col" style="text-align:left;">\
                            <h1 data-ID="{2}" data-type="{0}" style="font-size: 3.8vw; display:inline;">{3}</h1>\
                            <h6 style="font-size: 0.9vw; margin-left: 2%; display:inline;">{4}</h6>\
                        </div>\
                    </div>\
                </div>', title, uuid_cell, data.resource_id, data.value, unit, type, data.color.color, data.color.name);
                $("#data-container").append(html);

                //Expand all new MDL elements
                componentHandler.upgradeDom();
                dropdown_need_update = true;
            }
            else {
                value.text(data.value);
                var subtitle = value.closest(".mdl-card__supporting-text").prev(".mdl-card__title").children("span");
                if (show_uuid) {
                    if (subtitle.length == 0)
                        value.closest(".mdl-card__supporting-text").prev(".mdl-card__title").children("i").after(uuid_cell);
                }
                else {
                    if (subtitle.length > 0)
                        subtitle.remove();
                }
            }
        },
        update_brillo_data: function (uuid, data, show_uuid) {
            var value = $("#" + uuid);
            var plist = null;
            if('playlist' in data['mp3player'])
                plist = JSON.parse(data['mp3player'].playlist);

            if (value.length == 0) {
                var html = String.format('<div class="demo-card-data mdl-card mdl-cell mdl-cell--6-col mdl-shadow--2dp">\
                    <div class="mdl-card__title mdl-card--expand" style="padding-left: 8%">\
                        <h6>Android Things</h6>\
                        <i class="material-icons edit" style="display: none;">edit</i>\
                    </div>\
                    <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" id="{0}">\
                        <div class="mdl-cell mdl-cell--2-col" style="text-align: left;">\
                            <span>Colour</span>\
                        </div>\
                        <div class="mdl-cell mdl-cell--10-col" style="text-align: left; padding-bottom: 20px;">\
                            <input type="text" class="basic" data-id="{1}" data-lock="0"/>\
                        </div>\
                        <div class="mdl-cell mdl-cell--3-col" style="text-align: left;">\
                            <span>MP3 Player</span>\
                        </div>\
                        <div class="mdl-cell mdl-cell--9-col"></div>\
                        <div class="mdl-cell mdl-cell--12-col mdl-grid mdl-grid--no-spacing" style="padding-left: 75px; height: 47px; margin-bottom: 15px;">\
                            <div class="mdl-chip mdl-cell mdl-cell--9-col" style="background:#ffc75f; height:60%">\
                                <select id="brillo-mp3-title-{2}" style="font-weight:700; color:#fff;" data-id="{2}" data-lock="0"></select>\
                                <div class="mdl-tooltip" for="brillo-mp3-title-{2}">MP3 title</div>\
                            </div>\
                            <div class="mdl-layout-spacer"></div>\
                            <button id="brillo-pause-{2}" class="mdl-cell mdl-cell--1-col mdl-button mdl-button--icon">\
                                <i class="material-icons" style="color: #455a64">play_arrow</i>\
                            </button>\
                            <div class="mdl-tooltip" for="brillo-pause-{2}">Play</div>\
                            <button id="brillo-clear-{2}" class="mdl-cell mdl-cell--1-col mdl-button mdl-button--icon">\
                                <i class="material-icons" style="color: #455a64">clear</i>\
                            </button>\
                            <div class="mdl-tooltip" for="brillo-clear-{2}">Clear</div>\
                        </div>\
                        <div class="mdl-cell mdl-cell--3-col" style="text-align: left;">\
                            <span >Brightness</span>\
                        </div>\
                        <div class="mdl-cell mdl-cell--9-col"></div>\
                        <div class="mdl-cell mdl-cell--12-col">\
                            <p class="slider-bar">\
                                <input class="mdl-slider mdl-js-slider brightness" name="br" type="range" min="0" max="100" data-id="{3}" value="0" data-lock="0">\
                            </p>\
                        </div>\
                        <div class=" mdl-cell mdl-cell--12-col mdl-grid mdl-grid--no-spacing">\
                            <span class="mdl-cell mdl-cell--3-col" style="text-align: left;">Audio volume</span>\
                            <div class="mdl-layout-spacer"></div>\
                            <label class="mdl-cell mdl-cell--1-col mdl-switch mdl-js-switch mdl-js-ripple-effect" for="brillo-mute-{4}">\
                                <input title="Mute on/off" id="brillo-mute-{4}" type="checkbox" class="mdl-switch__input" data-id="{4}" data-lock="0">\
                            </label>\
                        </div>\
                        <div class="mdl-cell mdl-cell--12-col">\
                            <p class="slider-bar">\
                                <input class="mdl-slider mdl-js-slider volume" type="range" min="0" max="100" value="0" data-id="{4}" data-lock="0">\
                            </p>\
                        </div>\
                    </div>\
                </div>', uuid, data['rgbled'].resource_id, data['mp3player'].resource_id, data['brightness'].resource_id,
                    data['audio'].resource_id);
                $("#brillo-container").append(html);

                if (!(typeof(componentHandler) == 'undefined')) {
                    componentHandler.upgradeAllRegistered();
                }

                $("#" + uuid + " .basic").spectrum({
                    showInput: true,
                    preferredFormat: "rgb",
                    clickoutFiresChange: true,
                    showButtons: false,
                    allowEmpty: true
                    // color: convertToRgb(data['rgbled'].rgbvalue)
                });
                if(data['rgbled'] && 'path' in data['rgbled']){
                    $("#" + uuid + " .basic").spectrum("set", convertToRgb(data['rgbled'].rgbvalue));
                }
                else {
                    // no data for rgbled, disable it
                    $("#" + uuid + " .basic").spectrum("disable");
                }

                if(plist) {
                    var data_src = new Array();
                    var selected_index = 0;
                    plist.forEach(function (value, key) {
                        // console.log(value);
                        data_src.push({'id': key, 'text': value});
                        if (value == data['mp3player'].title) selected_index = key;
                    });

                    $('#brillo-mp3-title-' + data['mp3player'].resource_id).select2({
                        data: data_src,
                        tags: "true",
                        width: "100%"
                    });

                    $('#brillo-mp3-title-' + data['mp3player'].resource_id).data('state', data['mp3player'].state);
                    if (data['mp3player'].state == "Playing") {
                        $("#brillo-pause-" + data['mp3player'].resource_id + " i").html('pause');
                        $("#brillo-pause-" + data['mp3player'].resource_id).next(".mdl-tooltip").html('Pause');
                        $('#brillo-mp3-title-' + data['mp3player'].resource_id).val(selected_index).trigger('change.select2');
                    }
                    else if (data['mp3player'].state == "Paused") {
                        $('#brillo-mp3-title-' + data['mp3player'].resource_id).val(selected_index).trigger('change.select2');
                    }
                    else { // Idle
                        $('#brillo-mp3-title-' + data['mp3player'].resource_id).val('').trigger('change.select2');
                    }
                }
                else{
                    // no data for mp3player, disable it
                    $('#brillo-mp3-title-' + data['mp3player'].resource_id).select2({
                        data: null,
                        tags: "true",
                        width: "100%"
                    });
                }

                if(data['audio'] && 'mute' in data['audio']) {
                    if (data['audio'].mute === false) {
                        $("#brillo-mute-" + data['audio'].resource_id).parent('label')[0].MaterialSwitch.on();
                        $("#" + uuid + " .slider-bar .volume")[0].MaterialSlider.change(data['audio'].volume);
                    }
                    else{
                        $("#" + uuid + " .slider-bar .volume").attr('disabled', true);
                    }

                    $("#brillo-mute-" + data['audio'].resource_id).on('change', function () {
                        if ($(this).is(':checked')) {
                            $("#" + uuid + " .slider-bar .volume").removeAttr('disabled');
                        }
                        else {
                            $("#" + uuid + " .slider-bar .volume").attr('disabled', true);
                        }
                    });
                }
                else{
                    // no data for audio, disable it
                    $("#" + uuid + " .slider-bar .volume").attr('disabled', true);
                    $("#brillo-mute-" + data['audio'].resource_id).attr('disabled', true);
                }

                var bright = $("#" + uuid + " .slider-bar .brightness");
                if(data['brightness'] && 'brightness' in data['brightness']){
                    bright[0].MaterialSlider.change(data['brightness'].brightness);
                }
                else{
                    // no data for brightness, disable it
                    bright.attr('disabled', true);
                }

                if (!(typeof(componentHandler) == 'undefined')) {
                    componentHandler.upgradeAllRegistered();
                }
            }
            else {
                var title = $('#brillo-mp3-title-' + data['mp3player'].resource_id);
                if(plist) {
                    if (title.data('lock') == "0") {
                        if (plist.length != title.find("option").length) {
                            var data_src = new Array();
                            var selected_index = 0;
                            plist.forEach(function (value, key) {
                                data_src.push({'id': key, 'text': value});
                                if (value == data['mp3player'].title) selected_index = key;
                            });
                            title.html('').select2({
                                data:data_src,
                                tags: "true",
                                width: "100%"
                            });
                            if(data['mp3player'].state == 'Idle')
                                title.val('').trigger('change.select2');
                            else
                                title.val(selected_index).trigger('change.select2');
                        }
                        var prevStat = title.data("state");
                        if (data['mp3player'].title) {
                            var tIndex = plist.indexOf(data['mp3player'].title);
                            if (tIndex > -1 && tIndex != title.val()) {
                                console.log('*****update title');
                                title.val(tIndex).trigger('change.select2');
                            }
                        }
                        if (prevStat !== data['mp3player'].state) {
                            if (data['mp3player'].state == "Idle") {
                                title.val('').trigger('change.select2');
                                $("#brillo-pause-" + data['mp3player'].resource_id + " i").html('play_arrow');
                                $("#brillo-pause-" + data['mp3player'].resource_id).next(".mdl-tooltip").html('Play');
                            }
                            else if (data['mp3player'].state == "Playing") {
                                $("#brillo-pause-" + data['mp3player'].resource_id + " i").html('pause');
                                $("#brillo-pause-" + data['mp3player'].resource_id).next(".mdl-tooltip").html('Pause');
                            }
                            else if (data['mp3player'].state == "Paused") {
                                $("#brillo-pause-" + data['mp3player'].resource_id + " i").html('play_arrow');
                                $("#brillo-pause-" + data['mp3player'].resource_id).next(".mdl-tooltip").html('Play');
                            }
                            title.data('state', data['mp3player'].state);
                        }
                    }
                }
                else {
                    title.html('').select2({data: null, width: "100%", tags: "true"});
                    $("#brillo-pause-" + data['mp3player'].resource_id + " i").html('play_arrow');
                }

                if (data['rgbled'] && 'rgbvalue' in data['rgbled']) {
                    $("#" + uuid + " .basic").spectrum("enable");
                    if ($("#" + uuid + " .basic").data("lock") == 0) {
                        // if the color picker panel is open, skip the update
                        if($(".sp-hidden").length > 0) {
                            var rgb = $("#" + uuid + " .basic").spectrum('get').toRgbString();
                            var newRgb = convertToRgb(data['rgbled'].rgbvalue);
                            if (rgb) {
                                // trim whitespaces
                                rgb = rgb.replace(/\s+/g, '');
                                newRgb = newRgb.replace(/\s+/g, '');
                                if (newRgb !== rgb) {
                                    console.log('*****update rgbled');
                                    $("#" + uuid + " .basic").spectrum("set", newRgb);
                                }
                            }
                        }
                    }
                }
                else{
                    $("#" + uuid + " .basic").spectrum("disable");
                }

                var bright = $("#" + uuid + " .slider-bar .brightness");
                if(data['brightness'] && 'brightness' in data['brightness']) {
                    var newbright = data['brightness'].brightness;
                    if (bright.data('lock') == 0) {
                        bright.attr('disabled', false);
                        if (newbright != bright.val()) {
                            bright[0].MaterialSlider.change(newbright);
                        }
                    }
                }
                else {
                    bright.attr('disabled', true);
                }

                var mute = $("#brillo-mute-" + data['audio'].resource_id);
                var volume = $("#" + uuid + " .slider-bar .volume");
                if(data['audio'] && 'mute' in data['audio']) {
                    var status = !mute[0].checked;
                    if (status !== data['audio'].mute) {
                        mute.attr('disabled', false);
                        console.log('*****update mute');
                        if (data['audio'].mute) {
                            mute.parent('label')[0].MaterialSwitch.off();
                            volume.attr('disabled', true);
                        }
                        else {
                            mute.parent('label')[0].MaterialSwitch.on();
                            volume.removeAttr('disabled');
                            var newVol = data['audio'].volume;
                            if (volume.data('lock') == 0) {
                                volume.attr('disabled', false);
                                if (newVol != volume.val()) {
                                    console.log('*****update volume');
                                    volume[0].MaterialSlider.change(newVol);
                                }
                            }
                        }
                    }
                }
                else{
                    volume.attr('disabled', true);
                    mute.attr('disabled', true);
                }
            }
        },
        update_generic_data: function (resource_id, data, show_uuid) {
            var uuid_cell = '';
            if (show_uuid)
                uuid_cell = '<span class="mdl-card__subtitle-text" style="font-size: 70%; flex-basis: 100%;">ID: '
                    + data.uuid + '</span>';

            var title = "";
            if (data.tag) {
                title = "(" + data.tag + ")";
            }

            var value = $(".generic button[id='generic-" + data.resource_id + "']");
            if (value.length == 0) {
                var rows = '';
                if (data.value) {
                    var jData = JSON.parse(data.value);
                    $.each(jData, function (key, value) {
                        if ($.isArray(value) || value instanceof Object)
                            value = JSON.stringify(value);
                        rows += String.format('<tr>\
                        <td class="mdl-data-table__cell--non-numeric" title="{0}">{0}</td>\
                        <td title="{1}">{1}</td>\
                        <td><i class="material-icons edit">edit</i></td>\
                        </tr>', key, value);
                    });
                }
                var html = String.format('<div class="generic sensor-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--3-col">\
                    <div class="mdl-card__title" style="display: flex; flex-flow: row wrap;">\
                        <button id="generic-{0}" class="mdl-button mdl-js-button mdl-button--raised" style="background:white; display: none;">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="generic-{0}">\
                        </ul>\
			  	        <h6>Generic resource {3}</h6>\
			  	        {1}\
                    </div>\
                    <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
                        <table data-id="{0}" class="mdl-data-table mdl-js-data-table mdl-shadow--2dp">\
                            <thead>\
                                <tr>\
                                  <th>Key</th>\
                                  <th>Value</th>\
                                  <th>   </th>\
                                </tr>\
                            </thead>\
                            <tbody>\
                                {2}\
                            </tbody>\
                        </table>\
                    </div>\
                </div>', resource_id, uuid_cell, rows, title);
                $("#generic-container").append(html);
                // resize the column width
                var tb = $(".generic table[data-id='" + data.resource_id + "']");
                var width = tb.width() - 10;
                tb.find("th:nth-child(1), tr td:nth-child(1)").css(
                    {
                        "max-width": width * 0.3,
                        "min-width": width * 0.3
                    });
                tb.find("th:nth-child(2), tr td:nth-child(2)").css(
                    {
                        "max-width": width * 0.45,
                        "min-width": width * 0.45
                    });
            }
            else {
                // update table
                if (data.value) {
                    var jData = JSON.parse(data.value);
                    var tbody = $(".generic table[data-id='" + data.resource_id + "'] tbody");
                    $.each(tbody.children(), function () {
                        // iterate each table row and update them one by one
                        if ($(this).find("div.overlay").length === 0) {
                            var key = $(this).children(':first-child').text();
                            if (key) {
                                // console.log(jData[key]);
                                $(this).children(':nth-child(2)').text(jData[key]);
                                $(this).children(':nth-child(2)').attr('title', jData[key]);
                            }
                        }
                    });
                }
                // value.parent().next().find("tbody").html(rows);
            }
        },
        update_activity_data: function(uuid, data, show_uuid){
            var uuid_cell = '';
            var bgcolor = "bg-blue";
            if (data.rgb_led == undefined)
                bgcolor = "bg-grey";
            else if(data.rgb_led == true)
                bgcolor = "bg-red";

            var title = "ACTIVITY SENSOR";
            if (show_uuid)
                uuid_cell = '<span class="mdl-card__subtitle-text" style="font-size: 70%; flex-basis: 100%;">UUID: '
                    + data.uuid + '</span>';

            // var value = $(".sensor-card h1[data-ID='" + data.resource_id + "'][data-type='" + title + "']");
            var value = $("#activity-container .sensor-card h1[data-ID='" + data.resource_id + "']");

            var type = title;
            if (data.tag)
                type = type + data.tag;

            if (value.length == 0) {
                var html = String.format('<div class="sensor-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--3-col">\
                    <div class="mdl-card__title" style="display: flex; flex-flow: row wrap;">\
                        <button id="{0}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="background:{5}" title="{0}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{0}-{2}">\
                        </ul>\
			  	        <h6>{4}</h6>\
			  	        <i class="material-icons edit" style="display: none;">edit</i>\
			  	        {1}\
                    </div>\
                    <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing">\
                        <div class="mdl-cell mdl-cell--12-col" style="display: inline-flex">\
                            <div class="mdl-cell mdl-cell--8-col">\
                              <h1 data-ID="{2}" data-type="{0}" style="font-size: 3.8vw;">{3}</h1>\
                            </div>\
                            <div class="mdl-cell mdl-cell--4-col" style="text-align: right;" title="RGB LED">\
                             <i class="material-icons md-48 {7}">lightbulb_outline</i>\
                            </div>\
                        </div>\
                    </div>\
                </div>', title, uuid_cell, data.resource_id, data.total, type, data.color.color, data.color.name, bgcolor);
                $("#activity-container").append(html);

                //Expand all new MDL elements
                componentHandler.upgradeDom();
            }
            else {
                value.text(data.total);
                var icon = value.parent().next().find("i");
                icon.removeClass().addClass("material-icons md-48 " + bgcolor);
            }
        },
        get_temperature_in_timezone: function (value) {
            var house_temp = null;
            var temp_unit = "°";
            //console.log('index: ' + timezone.indexOf("America") + " tz: " + timezone);
            if (timezone.indexOf('America') == 0 || timezone.indexOf('US') == 0) {
                house_temp = convertToF(parseFloat(value), 1);
                temp_unit += "F";
            }
            else {
                house_temp = parseFloat(value).toFixed(1);
                temp_unit += "C";
            }
            return house_temp.toString() + temp_unit;
        },
        parse_data: function (value_list, callback) {
            var show_uuid = false;
            if (value_list.length > 1)
                show_uuid = true;
            value_list.forEach(function (data) {
                callback(data, show_uuid);
            })
        },
        update_portal: function () {
            if (window.panel != 1) return;
            $.ajax({
                type: "GET",
                url: "/get_sensor",
                dataType: 'json',
                headers: {
                    "token": JSON.stringify(alert_token),
                },
                success: function (data) {
                    console.log(data);
                    var sensors = data.data;
                    $.sh.now.clear_data(sensors);
                    $.each(sensors['alert'], function (key, value_list) {
                        switch (key) {
                            case 'buzzer':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_buzzer_alert(data, show_uuid);
                                    if (data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            case 'motion':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_motion_alert(data, show_uuid);
                                    if (data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            case 'gas':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_gas_alert(data, show_uuid);
                                    if (data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            case 'button':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_car_alert(data, show_uuid);
                                    if (data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            default:
                                console.error("Unknown alert sensor type: " + key);
                        }
                        // console.log("number of alert cards " + alert_card_number);
                        if (alert_card_number > 0) {
                            $("#alert-status-title-quiet").hide();
                            $("#alert-status-title-alerts").show();
                        }
                    });
                    $.each(sensors['status'], function (key, value_list) {
                        switch (key) {
                            case 'fan':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_switch_status(data, "FAN", show_uuid);
                                });
                                break;
                            case 'led':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_status('LED', data, show_uuid);
                                });
                                break;
                            case 'rgbled':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_rgb_status(data, show_uuid);
                                });
                                break;
                            case 'buzzer':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_switch_status(data, "BUZZER", show_uuid);
                                });
                                break;
                            default:
                                console.error("Unknown status sensor type: " + key);
                        }
                    });
                    $.each(sensors['data'], function (key, value_list) {
                        switch (key) {
                            case 'temperature':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    data.value = $.sh.now.get_temperature_in_timezone(data.value);
                                    $.sh.now.update_sensor_data_without_unit('TEMPERATURE', data, show_uuid);
                                });
                                break;
                            case 'solar':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_sensor_data('SOLAR PANEL TILT', data, '%', show_uuid);
                                });
                                break;
                            case 'illuminance':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_sensor_data('AMBIENT LIGHT', data, 'lm', show_uuid);
                                });
                                break;
                            case 'power':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    data.value = data.value / 1000;
                                    $.sh.now.update_sensor_data('CURRENT ENERGY CONSUMPTION', data, 'Watt', show_uuid);
                                });
                                break;
                            case 'humidity':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    data.value = data.value;
                                    $.sh.now.update_sensor_data('HUMIDITY', data, '%', show_uuid);
                                });
                                break;
                            case 'pressure':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_sensor_data('PRESSURE', data, 'hPa', show_uuid);
                                });
                                break;
                            case 'uv_index':
                                $.sh.now.parse_data(value_list, function (data, show_uuid) {
                                    $.sh.now.update_sensor_data_without_unit('UV INDEX', data, show_uuid);
                                });
                                break;
                            default:
                                console.error("Unknown sensor data type: " + key);
                        }
                    });
                    $.each(sensors['brillo'], function (key, value) {
                        var show_uuid = false;
                        if (Object.keys(sensors['brillo']).length > 1)
                            show_uuid = true;
                        $.sh.now.update_brillo_data(key, value, show_uuid);
                    });
                    $.each(sensors['generic'], function (key, value) {
                        var show_uuid = true;
                        $.sh.now.update_generic_data(key, value, show_uuid);
                    });
                    $.each(sensors['activity'], function (key, value) {
                        var show_uuid = true;
                        $.sh.now.update_activity_data(key, value, show_uuid);
                    });
                }
            }).done(function () {
                //console.log( "second success" );
            }).fail(function () {
                console.log("getJson data error");
            }).always(function () {
                if (dropdown_need_update)
                    $.sh.now.update_sensor_group();
            })
        },
        update_billing: function () {
            draw_billing_pie_chart('today_container', 'Today\'s usage', [{
                name: "Grid Power",
                value: 90
            }, {name: "Solar Power", value: 210}]);
            draw_billing_pie_chart('current_container', 'Current bill', [{
                name: "Grid Power",
                value: 90
            }, {name: "Solar Power", value: 110}]);
            draw_billing_pie_chart('items_container', 'Items', [{name: "Heater", value: 90}, {
                name: "Oven",
                value: 110
            }, {name: "Refrigerator", value: 110}]);
        },
        init: function () {
            console.log("init now page.");
            window.panel = 1;
            $('#sh-before').hide();
            $('#sh-future').hide();
            $('#sh-now').show();
            $('#alert-status-card').show();
            $("#demo-welcome-message").html("This demo tells you what is <b>happening in your home right now.</b>");
            $.sh.now.update_portal();
            $.sh.now.register_actions();
            $.sh.now.update_billing();
            $(window).trigger('resize');
            // Expand all new MDL elements
            //componentHandler.upgradeDom();
            window.now_timer = setInterval($.sh.now.update_portal, 3000);
            // update weather every 1 hour
            // window.weather_timer = setInterval(updateWeather(), 3600 * 1000);
        }
    };

    $("a:contains('NOW')").on('click', function () {
        clearInterval(window.time_timer);
        clearInterval(window.now_timer);
        //clearInterval(window.weather_timer);
        //clearInterval(chart_timer);
        $.sh.now.init();
    });

    setInterval(function () {
        updateWelcomeCardsDateTime(utc_offset, timezone);
    }, 60 * 1000);

    $.sh.init();
    $.sh.now.init();
    updateWelcomeCardsDateTime(utc_offset, timezone);

    $(window).resize(function () {
        // resize the generic table column width
        $("#generic-container table").each(function () {
            var tb = $(this);
            var width = tb.width() - 10;
            tb.find("th:nth-child(1), tr td:nth-child(1)").css(
                {
                    "max-width": width * 0.3,
                    "min-width": width * 0.3
                });
            tb.find("th:nth-child(2), tr td:nth-child(2)").css(
                {
                    "max-width": width * 0.45,
                    "min-width": width * 0.45
                });
        });
    });
});
