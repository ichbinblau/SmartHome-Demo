/**
 * Scripts for the Now and Before page
 */
$(function() {
	//Set the object socket global.
	window.socket;
	window.socket = null;

	//The variable panel represents the current panel displayed by the browser.
	//0: Initial. No panel is specified.
	//1: the Now panel.
	//2: the Before panel
	window.panel;
	window.panel=0;

    //Number of alert cards displayed on NOW page
    var alert_card_number = 0;

	var now_timer;
	var time_timer;
    var weather_timer;

    var timezone = null;
    var utc_offset = null;

    // the token dict to store the last alert time for motion, gas, buzz and button sensors
    var alert_token = {};

    // check whether to update the sensor group list
    var dropdown_need_update = false;

    $.sh = {
        init: function() {
            //set initial timezone to Cookie
            console.log("load timezone...");
            if (!getTimezone()) {
                setTimezone(moment.tz.guess());
                console.log('set timezone in cookie: ' + getCookie('timezone'));
            }
            makeTimezoneSelect();

            $("#inst").on('click mouseover', function() {
                $.getJSON('/cf_instance', function(data) {
                        if (data.error != null) {
                            console.error('Cannot get the cf instance info.');
                        } else {
                            var inst = data.cf_instance;
                            if($.isEmptyObject(inst))
                                $("#instance_info").html('n/a');
                            else
                            {
                                var info = String.format('<div>Name <span>{0}</span></div><div style="word-break:break-all;">URL <a>{1}</a></div> \
                                    <table><tbody> \
                                    <tr><td>Instance ID</td><td style="word-break:break-all; width: 145px">{2}</td></tr> \
                                    <tr><td>Version</td><td>{3}</td></tr> \
                                    <tr><td>Index</td><td>{4}</td></tr> \
                                    <tr><td>Instance running</td><td>{5}</td></tr> \
                                    </tbody></table>', inst.name, inst.uris[0], inst.instance_id, inst.version, inst.Instance, inst.Total);
                                $("#instance_info").html(info);
                            }
                            $("#instance_info").show();

                            // to fix the wrong margin offset for the first time issue
                            var left_offset = $("#instance_info").css('margin-left');
                            if(left_offset == "0px") {
                                var tip = $("#instance_info");
                                $("#instance_info").css('margin-left', -1 * tip.width() + 'px');
                            }
                        }
                });
            });
        }
    };

    function getTimezone() {
        var tz = getCookie('timezone');
        var zones = moment.tz.names();
        if(zones.indexOf(tz) > 0) {
            console.log('get timezone in cookie: ' + tz);
            timezone = tz;
            utc_offset = moment.tz(timezone).utcOffset() / 60;
            return true;
        }
        else return false;
    };

    function setTimezone(tz) {
        timezone = tz;
        createCookie('timezone', timezone, 5);
        utc_offset = moment.tz(timezone).utcOffset()/60;
        console.log('current offset: ' + utc_offset);
    };

    function makeTimezoneSelect() {
        // reduce the timezone list size to 220.
        var cities = Object.keys(moment.tz._zones)
            .map(function(k) { if(typeof moment.tz._zones[k] === 'string') return moment.tz._zones[k].split('|')[0]; else return moment.tz._zones[k].name;})
            .filter(function(z) { return z.indexOf('/') >= 0; });

        var ordered_cities = [];
        var i = 0 ;
        for(var key in cities) {
            ordered_cities.push({
              id: i.toString(),
              text: '(GMT ' + moment.tz(cities[key]).format('Z') + ') ' + cities[key],
              offset: moment.tz(cities[key]).format('Z')
            });
            i++;
        }
        ordered_cities.sort(function(a, b){
            return parseInt(a.offset.replace(":", ""), 10) - parseInt(b.offset.replace(":", ""), 10);
        });

        $('#timezone').select2({
            data: ordered_cities,
            tags: "true",
            width: "300px",
            placeholder: '(GMT ' + moment.tz(timezone).format('Z') + ') ' + timezone,
        });

        $('#timezone').change(function() {
            var theSelection = $('#timezone option:selected').text();
            console.log('selected: ' + theSelection.split(') ')[1]);
            setTimezone(theSelection.split(') ')[1]);
            window.location.reload();
        });
    }

	window.onbeforeunload = function() {
		console.log("Leaving the page...");
		if(window.socket !=null)window.socket.close();
    };

	window.onload = function() {
    };

	$.sh.now = {
		register_actions: function(){
			console.log('sh-now: register_actions');
			$("a:contains('DISMISS')").on("click", function(){
				//find parent div
				dismiss(this);
			});

			$("label.mdl-icon-toggle").on('click', function(e) {
				e.preventDefault();
				e.stopImmediatePropagation();
				var unit = $(this).children("span:first").html();
				var temp = $(this).parent().prev().find("h1").html();
                if(temp.length == 0) return;
				if (unit == "C") {
					unit = "F";
					temp = convertToF(temp, 0);
				}
				else if (unit == "F") {
					unit = "C";
					temp = convertToC(temp, 0);
				}
				console.log('unit: ' + unit + ' temp: '+ temp);
				$(this).children("span:first").html(unit);
				$(this).parent().prev().find("h1").html(temp + '°');
			});

            $("#data-container, #alert-container").on('mouseover mouseout', '.mdl-card__title', function(e){
                // show edit icon on mouse over
                if(e.type == "mouseover")
                    $(this).children(".edit").show();
                else
                    $(this).children(".edit").hide();
            });

            $("#status-container").on('mouseover mouseout', '.mdl-card__supporting-text .mdl-cell', function(e) {
                // show edit icon on mouse over
                if(e.type == "mouseover")
                    $(this).children(".edit").show();
                else
                    $(this).children(".edit").hide();
            });

            $("#alert-container, #status-container, #data-container").on('click', '.edit', function(event) {
                // show text field
                var text = $(this).prev().text();

                var input = $('<input type="text" maxlength="30" value="' + text + '" required="required" />');
                input.data("initial", text);
                $(this).prev().text('').append(input);
                input.select();

                input.keydown(function() {
                    var title=$(this).parent().data("title");
                    var field=this;
                    setTimeout(function () {
                        if(field.value.indexOf(title) !== 0) {
                            $(field).val(title);
                        }
                    }, 1);
                });

                input.on("change focus blur", function() {
                    var prefix=$(this).parent().data("title");
                    var text = $(this).val();
                    var oldVal = $(this).data("initial");
                    var titleObj = $(this).parent();
                    var title = "Only alpha, digits, space, underscore, hyphen and dot are allowed.";
                    if(oldVal == text) {
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
                    if($(this).closest(".demo-card-event").length > 0) {
                        var res_id = $(this).closest(".demo-card-event").attr("id");
                        resource_id = res_id.split('-')[1];
                    }
                    else if($(this).closest(".status-card").length > 0)
                        resource_id  = $(this).closest(".mdl-card__supporting-text").find(".mdl-card__menu").attr("data-ID");
                    else if($(this).closest(".sensor-card").length > 0 ) {
                        resource_id = $(this).closest(".sensor-card").find("h1").attr("data-ID");
                        sensor_type = $(this).closest(".sensor-card").find("h1").attr("data-type");
                    }
                    var tag = text.substring(prefix.length, text.length);
                    titleObj.text(text);
                    $(this).remove();

                    $.sh.now.update_sensor_title(resource_id, tag, sensor_type, oldVal, titleObj);
                });
            });

            $("#data-container, #alert-container, #status-container").on('click', 'li', function(e) {
                if($(e.target).text().indexOf('Add Group') > -1 ) {
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
                                if($("#orrsDiag input:valid").length > 1) {
                                    var name = textbox.val();
                                    var color = $("#color-picker").spectrum('get').toHexString();
                                    if(getCookie('gateway_id')) {
                                        var data = {
                                            'name': name,
                                            'color': color,
                                            'gateway_id': parseInt(getCookie('gateway_id')),
                                        };
                                        $.ajax ({
                                            url: "/add_sensor_group",
                                            type: "POST",
                                            data: JSON.stringify(data),
                                            dataType: "json",
                                            contentType: "application/json; charset=utf-8",
                                            success: function(data) {
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
                            showPalette:true,
                            hideAfterPaletteSelect:true,
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

            // $("#data-container, #alert-container, #status-container").on('click', 'button', function(e) {
                // $.sh.now.update_sensor_group();
                //var listLen = $(this).next().find("ul").children("li");
                // if(listLen == 0) {
                //     e.preventDefault();
                //     return false;
                // }
            // });

		},
        _update_sensor_group: function(value, color, buttonElem) {
            $.ajax({
                type: "POST",
                url: "/update_sensor_attr",
                contentType: 'application/json',
                data: JSON.stringify(value),
                success: function(data) {
                    var resource_id = data.resource_id;
                    if (resource_id) {
                        buttonElem.css('background', color);
                        createSnackbar('Sensor group for resource ' + resource_id + ' is updated.', 'Dismiss');
                    }
                }
            }).done(function() {
            }).fail(function(jqXHR, textStatus, errorThrown){
                console.error("Failed to update sensor group: " + errorThrown);
                createSnackbar("Server error: " + errorThrown, 'Dismiss');
            });
        },
        update_sensor_title: function(resource_id, title, sensor_type, oldVal, titleObj) {
		    if(sensor_type.length > 0)
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
                success: function(data) {
                    // console.log(data);
                    // data = JSON.parse(data);
                    var resource_id = data.resource_id;
                    if (resource_id) {
                        createSnackbar('Sensor ' + resource_id + ' is updated.', 'Dismiss');
                    }
                }
            }).done(function() {
            }).fail(function(jqXHR, textStatus, errorThrown){
                console.error("Failed to update status " + errorThrown);
                createSnackbar("Server error: " + errorThrown, 'Dismiss');
                //change the title back if fail
                $(titleObj).text(oldVal);
            });
		},
        update_sensor_group: function(){
		    if(dropdown_need_update) {
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
        append_sensor_group: function(data) {
            $(".sensor-card ul, .demo-card-event ul, .status-card ul").each(function() {
                var len = $(this).children("li").length;
                var liElem = $(this).children("li:eq(" + (len - 2) + ")");
                $('<li/>').addClass('mdl-menu__item')
                    .css('color', data['color'])
                    .data('cid', data['id'])
                    .html("<span>" + data['name'] + "</span>")
                    .insertAfter(liElem);
            });
        },
        clear_data: function(data) {
		    var types = ["status", "data"];
		    var sensor_list = [];
            types.forEach(function(type) {
                $.each(data[type], function (key, value_list) {
                    value_list.forEach(function (value) {
                        var id = value.resource_id.toString();
                        if(!sensor_list.includes(id))
                            sensor_list.push(id);
                    });
                });
            });
            $('.sensor-card h1').each(function () {
                    var ID = $(this).attr('data-ID');
                    if (!sensor_list.includes(ID)){
                        // remove the sensor card
                        console.log('remove sensor:' + ID);
                        $(this).closest(".sensor-card").remove();
                    }
            });
            $('.status-card .mdl-card__menu').each(function (){
                var ID = $(this).attr('data-ID');
                if (!sensor_list.includes(ID)) {
                    $(this).closest(".status-card").remove();
                }
            });
        },
        dismiss_alert_card: function(obj){
            dismiss(obj);
            alert_card_number--;
            console.log("number of alert cards " + alert_card_number);
            if(alert_card_number <= 0)
            {
                $("#alert-status-title-quiet").show();
                $("#alert-status-title-alerts").hide();
            }
        },
		update_car_alert: function(data, show_uuid) {
            var uuid_txt = "";
            var time;
            if(data.value.length == 0 ) return;
            time = getTime(data.value, utc_offset, timezone);
            if(show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "ELECTRIC CAR ";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

			if($("#" + card_id).length > 0){
				//find the car card and update time
                if(time) {
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
		update_motion_alert: function(data, show_uuid){
            var uuid_txt = "";
            var time;
            if(data.value.length == 0 ) return;
            time = getTime(data.value, utc_offset, timezone);
            if(show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "MOTION SENSOR";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

			if($("#" + card_id).length > 0){
				//find the motion card and update time
                if(time) {
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
		update_gas_alert: function(data, show_uuid){
		    var uuid_txt = "";
            var time;

            if(data.value.length == 0 ) return;
            time = getTime(data.value, utc_offset, timezone);
            if(show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "CO2 SENSOR";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

			if($("#" + card_id).length > 0){
				//find the gas card and update time
                if(time) {
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
		update_buzzer_alert: function(data, show_uuid) {
		    var uuid_txt = "";
            var time;

            if(data.value.length == 0 ) return;
            time = getTime(data.value, utc_offset, timezone);

            if(show_uuid)
                uuid_txt = 'ID: ' + data.uuid + ':' + data.path;

            var title = "BUZZER";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var card_id = "res-" + data.resource_id;

			if($("#" + card_id).length > 0) {
                //find the buzzer card and update time
                if(time) {
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
		update_status: function(type, data, show_uuid) {
			var color = "gray";
            var uuid_cell = "";
			if (data.value)
				color = "green";

            if(show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var tag = type;
            if(data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id + "'] i");

            if(menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
                      <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%;">\
                            <button id="{4}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="margin-top: 8%; background:{5}" title="{6}">\
                            </button>\
                            <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{2}">\
                            </ul>\
                            <div class="mdl-cell mdl-cell--9-col" style="display: flex; flex-flow: row wrap;">\
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
		update_fan_status: function(data, show_uuid) {
            var uuid_cell = "";
            if(show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var title = "FAN";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id +"'] label");

            if(menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
				  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%;">\
                        <button id="{3}-{1}" class="mdl-button mdl-js-button mdl-button--raised" style="margin-top: 8%; background:{4}" title="{5}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{3}-{1}">\
                        </ul>\
                        <div class="mdl-cell mdl-cell--9-col" style="display: flex; flex-flow: row wrap;">\
                            <h6 title="{0}" data-title="{3}">{2}</h6>\
                            <i class="material-icons edit" style="display: none; margin-top: 1em; ">edit</i>\
                        </div>\
					  <div data-ID="{1}" class="mdl-card__menu">\
						  <label title="switch on/off" class="mdl-switch mdl-js-switch mdl-js-ripple-effect" for="res-{1}">\
      						<input type="checkbox" id="res-{1}" class="mdl-switch__input" onclick="return toggle_status({1}, this);">\
      						<span class="mdl-switch__label"></span>\
    					  </label>\
					  </div>\
				  </div>\
				</div>', uuid_cell, data.resource_id, tag, title, data.color.color, data.color.name));
                $("input[id=res-" + data.resource_id + "]").prop('checked', data.value);
                var len = $(".status-card").length;
                if(len > 0) {
                    var zindex = 100 - len - 1;
                    $(".status-card").last().css("z-index", zindex);
                }
                dropdown_need_update = true;
            }
            else{
                // toggle switch on/off
                var status = menu.find("input")[0].checked;
                if(status !== data.value) {
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
		update_rgb_status: function(data, show_uuid) {
			var bgcolor = "bg-blue";
            var uuid_cell = "";
			if(data.value)
				bgcolor = "bg-red";

            if(show_uuid)
                uuid_cell = 'ID: ' + data.uuid + ':' + data.path;

            var title = "RGB LED";
            var tag = title;
            if(data.tag)
                tag = tag + data.tag;

            var menu = $(".status-card div[data-ID='" + data.resource_id + "'] i");
            if(menu.length == 0) {
                $("#status-container").append(String.format('<div class="status-card mdl-card mdl-cell mdl-shadow--2dp mdl-cell--12-col">\
                  <div class="mdl-card__supporting-text mdl-grid mdl-grid--no-spacing" style="margin-left: 4%;">\
                        <button id="{4}-{2}" class="mdl-button mdl-js-button mdl-button--raised" style="margin-top: 8%; background:{5}" title="{6}">\
                        </button>\
                        <ul class="mdl-menu mdl-js-menu mdl-js-ripple-effect" for="{4}-{2}">\
                        </ul>\
                        <div class="mdl-cell mdl-cell--9-col" style="display: flex; flex-flow: row wrap;">\
                            <h6 title="{1}" data-title="{4}">{3}</h6>\
                            <i class="material-icons edit" style="display: none; margin-top: 1em; ">edit</i>\
                        </div>\
                      <div data-ID="{2}" class="mdl-card__menu">\
                          <i class="material-icons {0}">lightbulb_outline</i>\
                      </div>\
                  </div>\
                </div>', bgcolor, uuid_cell, data.resource_id, tag, title, data.color.color, data.color.name));
                var len = $(".status-card").length;
                if(len > 0) {
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
        update_sensor_data_without_unit: function(title, data, show_uuid) {
		    this.update_sensor_data(title, data, '', show_uuid);
        },
		update_sensor_data: function(title, data, unit, show_uuid) {
			var uuid_cell = '';
            if(show_uuid)
                uuid_cell = '<span class="mdl-card__subtitle-text" style="font-size: 70%; flex-basis: 100%;">ID: '
                    + data.uuid + ':' + data.path + '</span>';

            var value = $(".sensor-card h1[data-ID='" + data.resource_id + "'][data-type='" + title + "']");

            var type = title;
            if(data.tag)
                type = type + data.tag;

            if(value.length == 0) {
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
                        <div class="mdl-cell" style="text-align:left; width: auto;">\
                            <h1 data-ID="{2}" data-type="{0}" style="font-size: 3.8vw;">{3}</h1>\
                        </div>\
                        <div class="mdl-cell" style="display: flex; align-items: center;">\
								<h6 style="font-size: 0.8vw;">{4}</h6>\
                        </div>\
                    </div>\
                </div>', title, uuid_cell, data.resource_id, data.value, unit, type, data.color.color, data.color.name);
                $("#data-container").append(html);

                //Expand all new MDL elements
                componentHandler.upgradeDom();
                dropdown_need_update = true;
            }
            else{
                value.text(data.value);
                var subtitle = value.closest(".mdl-card__supporting-text").prev(".mdl-card__title").children("span");
                if(show_uuid) {
                    if(subtitle.length == 0)
                        value.closest(".mdl-card__supporting-text").prev(".mdl-card__title").children("i").after(uuid_cell);
                }
                else {
                    if(subtitle.length > 0)
                        subtitle.remove();
                }
            }
		},
        get_temperature_in_timezone: function(value) {
		    var house_temp = null;
            var temp_unit = "°";
            //console.log('index: ' + timezone.indexOf("America") + " tz: " + timezone);
            if(timezone.indexOf('America') == 0 || timezone.indexOf('US') == 0) {
                house_temp = convertToF(parseFloat(value), 1);
                temp_unit += "F";
            }
            else {
                house_temp = parseFloat(value).toFixed(1);
                temp_unit += "C";
            }
            return house_temp.toString() + temp_unit;
        },
        parse_data: function(value_list, callback){
            var show_uuid = false;
            if(value_list.length > 1)
                show_uuid = true;
            value_list.forEach(function(data){
                callback(data, show_uuid);
            })
        },
		update_portal: function() {
			if(window.panel != 1) return;
            $.ajax({
                type: "GET",
                url: "/get_sensor",
                dataType: 'json',
                headers: {
                    "token": JSON.stringify(alert_token),
                },
                success: function(data){
                    console.log(data);
                    var sensors = data.data;
                    $.sh.now.clear_data(sensors);
                    $.each(sensors['alert'], function (key, value_list) {
                        switch (key) {
                            case 'buzzer':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_buzzer_alert(data, show_uuid);
                                    if(data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            case 'motion':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_motion_alert(data, show_uuid);
                                    if(data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            case 'gas':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_gas_alert(data, show_uuid);
                                    if(data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
							case 'button':
							    $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_car_alert(data, show_uuid);
                                    if(data.value)
                                        alert_token[data.resource_id] = data.value;
                                });
                                break;
                            default:
                                console.error("Unknown alert sensor type: " + key);
                        }
                        // console.log("number of alert cards " + alert_card_number);
                        if(alert_card_number == 1)
                        {
                            $("#alert-status-title-quiet").hide();
                            $("#alert-status-title-alerts").show();
                        }
                    });
                    $.each(sensors['status'], function (key, value_list) {
                        switch (key) {
                            case 'fan':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_fan_status(data, show_uuid);
                                });
                                break;
                            case 'led':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_status('LED', data, show_uuid);
                                });
                                break;
                            case 'rgbled':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_rgb_status(data, show_uuid);
                                });
                                break;
                            default:
                                console.error("Unknown status sensor type: " + key);
                        }
                    });
                    $.each(sensors['data'], function (key, value_list) {
                        switch (key) {
                            case 'temperature':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    data.value = $.sh.now.get_temperature_in_timezone(data.value);
                                    $.sh.now.update_sensor_data_without_unit('TEMPERATURE', data, show_uuid);
                                });
                                break;
                            case 'solar':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_sensor_data('SOLAR PANEL TILT', data, '%', show_uuid);
                                });
                                break;
                            case 'illuminance':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_sensor_data('AMBIENT LIGHT', data, 'lm', show_uuid);
                                });
                                break;
                            case 'power':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    data.value = data.value/1000;
                                    $.sh.now.update_sensor_data('CURRENT ENERGY CONSUMPTION', data, 'Watt', show_uuid);
                                });
                                break;
                            case 'humidity':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    data.value = data.value + '%';
                                    $.sh.now.update_sensor_data_without_unit('HUMIDITY', data, show_uuid);
                                });
                                break;
                            case 'pressure':
                                $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_sensor_data('PRESSURE', data, 'hPa', show_uuid);
                                });
                                break;
                            case 'uv_index':
                               $.sh.now.parse_data(value_list, function(data, show_uuid){
                                    $.sh.now.update_sensor_data_without_unit('UV INDEX', data, show_uuid);
                                });
                                break;
                            default:
                                console.error("Unknown sensor data type: " + key);
                        }
                    });
                }
            }).done(function() {
			   //console.log( "second success" );
			}).fail(function() {
			    console.log( "getJson data error" );
			}).always(function() {
                if(dropdown_need_update)
                    $.sh.now.update_sensor_group();
			})
		},
        update_billing: function() {
            draw_billing_pie_chart('today_container', 'Today\'s usage', [{ name: "Grid Power", value:90},{ name:"Solar Power", value: 210}]);
            draw_billing_pie_chart('current_container', 'Current bill', [{ name: "Grid Power", value:90},{ name:"Solar Power", value: 110}]);
            draw_billing_pie_chart('items_container', 'Items', [{ name: "Heater", value:90},{ name:"Oven", value: 110}, { name:"Refrigerator", value: 110}]);
        },
		init: function() {
			console.log("init now page.");
			window.panel = 1;
            $('#sh-before').hide();
            $('#sh-now').show();
            $('#alert-status-card').show();
            $("#demo-welcome-message").html("This demo tells you what is <b>happening in your home right now.</b>");
			$.sh.now.update_portal();
			$.sh.now.register_actions();
            $.sh.now.update_billing();
            $(window).trigger('resize');
			// Expand all new MDL elements
      		//componentHandler.upgradeDom();
			now_timer = setInterval($.sh.now.update_portal, 3000);
            // update weather every 1 hour
            weather_timer = setInterval(updateWeather(), 3600*1000);
		}
	};

	$.sh.before = {
		register_actions: function(){
			console.log('sh-before: register_actions');
			$("a:contains('DISMISS')").on("click", function(){
				//find parent div
				dismiss(this);
			});

            // switch between the billing tabs
            $("a.mdl-tabs__tab").on("click", function(){
				var tid = $(this).attr( "href" );
				$("div"+tid).find("div[id*='container']").each(function () {
                    if(tid.indexOf('#tab') == 0)
                        $.sh.before.update_billing(tid);
                    else {
                        var id = $(this).attr('_echarts_instance_');
                        window.echarts.getInstanceById(id).resize();
                    }
				});
            });

		},
        update_billing: function(tab) {
            //set up tab bar
            tab = tab.substring(1);
            switch(tab) {
                case 'tab1':
                    draw_billing_pie_chart(tab + '_today_container', 'Today\'s usage', [{name: "Grid Power", value: 90
                    }, {name: "Solar Power", value: 210}]);
                    draw_billing_pie_chart(tab + '_current_container', 'Current bill', [{name: "Grid Power",value: 90
                    }, {name: "Solar Power", value: 110}]);
                    draw_billing_pie_chart(tab + '_items_container', 'Items', [{name: "Heater", value: 90
                    }, {name: "Oven", value: 110}, {name: "Refrigerator", value: 110}]);
                    break;
                case 'tab2':
                case 'tab3':
                    draw_billing_pie_chart(tab + '_today_container', 'Past week', [{name: "Grid Power",value: 90
                    }, {name: "Solar Power", value: 210}]);
                    draw_billing_pie_chart(tab + '_current_container', 'Past month', [{name: "Grid Power",value: 90
                    }, {name: "Solar Power", value: 110}]);
                    draw_billing_pie_chart(tab + '_items_container', 'Items', [{name: "Heater", value: 90
                    }, {name: "Oven", value: 110}, {name: "Refrigerator", value: 110}]);
                    break;
                case 'tab4':
                    draw_billing_pie_chart(tab + '_today_container', 'Past week', [{name: "Grid Power",value: 90
                    }, {name: "Solar Power", value: 210}]);
                    draw_billing_pie_chart(tab + '_current_container', 'Past month', [{name: "Grid Power", value: 90
                    }, {name: "Solar Power", value: 110}]);
                    draw_billing_pie_chart(tab + '_items_container', 'Past year', [{name: "Grid Power", value: 90
                    }, {name: "Solar Power", value: 110}]);
                    break;
            }
        },
        update_static_data: function() {
            var monthSolar = [1.67, 1.66, 1.67, 1.65, 1.61, 1.59, 1.58];
            var yearSolar = [50.96, 59.55, 83.12, 100.68, 117.62, 126.35, 126.64, 120.79, 106.03, 85.59, 62.14, 51.49];
            var weekGrid = [4.47, 4.82, 5.17, 5.10, 5.21, 5.07, 4.62];
            var monthGrid = [4.80, 4.88, 4.82, 4.87, 4.92, 5.02, 4.97];
            var yearGrid = [183.31, 203.80, 129.27, 95.66, 71.80, 42.18, 67.60, 94.03, 68.33, 48.08, 102.22, 156.58];
            var weekTemp = [70.448, 70.556, 70.268, 70.43, 70.646, 70.88, 70.826];
            var monthTemp = [70.826, 70.772, 70.664, 70.808, 71.096, 71.33, 71.42];
            var yearTemp = [70.844, 70.898, 70.97, 71.066, 71.114, 71.042, 71.096, 71.15, 71.276, 71.186, 70.916, 70.844];
            var weekSolar = [1.64, 1.68, 1.67, 1.69, 1.70, 1.67, 1.64];
            var weekbuzzer = [123,145,264,153,120,120,110];
            var monthbuzzer = [110,172,227,158,144,100,106];
            var yearbuzzer = [3000,3400,4300,2900,2400,3500,3200,2900,4000,4200,3800,3500];
            var weekgas = [120,110,123,153,120,145,264];
            var monthgas = [172,110,227,158,144,230,106];
            var yeargas = [3400,3000,4300,2900,4000,4200,2400,2900,3800,3200, 3500, 2800];
            var weeklight = [12.28,13.04,15.08,11.54,15.92,12.19,10.32];
            var monthlight = [12.43,13.04,12.08,11.26,15.92,15.92,12.32];
            var yearlight = [16.02,11.04,15.08,13.75,13.92,12.19,14.32, 15.03, 15.56, 14.34, 12.80, 12.79];

            drawcontainer('container', week, weekSolar, getWeek());
            drawcontainer('container_a', month, monthSolar, getMonth());
            drawcontainer('container_b', year, yearSolar, getYear());
            drawcontainer('container1', week, weekGrid, getWeek());
            drawcontainer('container1_a', month, monthGrid, getMonth());
            drawcontainer('container1_b', year, yearGrid, getYear());
            drawcontainerchart('container2_a',week,weekTemp,getWeek(),'Week(Day)', 'average temperature');
            drawcontainerchart('container2_b',month,monthTemp,getMonth(),'Month(Day)', 'average temperature');
            drawcontainerchart('container2_c',year,yearTemp,getYear(),'Year(Month)', 'average temperature');
            drawcontainerchart('container3_a',week,weekbuzzer,getWeek(),'Week(Day)','total times', 'times');
            drawcontainerchart('container3_b',month,monthbuzzer,getMonth(),'Month(Day)', 'total times', 'times');
            drawcontainerchart('container3_c',year,yearbuzzer,getYear(),'Year(Month)', 'total times', 'times');
            drawcontainerchart('container4_a',week,weekgas,getWeek(),'Week(Day)' ,'total times', 'times');
            drawcontainerchart('container4_b',month,monthgas,getMonth(),'Month(Day)', 'total times', 'times');
            drawcontainerchart('container4_c',year,yeargas,getYear(),'Year(Month)', 'total times', 'times');
            drawcontainerchart('container5_a',week,weeklight, getWeek(),'Week(Day)', 'average illuminance', 'lm');
            drawcontainerchart('container5_b',month,monthlight, getMonth(),'Month(Day)', 'average illuminance', 'lm');
            drawcontainerchart('container5_c',year,yearlight, getYear(),'Year(Month)', 'average illuminance', 'lm');
        },
    	loading: function () {
			var newmsg="<div style = 'text-align:center;'><img src='image/loading.gif' width='24px' height ='24px'/></div>";
			$("#container2").html(newmsg);
			$("#container3").html(newmsg);
			$("#container4").html(newmsg);
			$("#container5").html(newmsg);
    	},
    	sendrequest: function () {
			if(window.panel != 2) return;
            //var converted = moment.tz(moment(), timezone).format("YYYY-MM-DD");
            //console.log("timezone today: " + moment.tz(moment(), timezone).format());
			var full_format = "YYYY-MM-DD HH:mm:ss";
            // for the current day
            var utc_start_time = moment.tz(timezone).startOf('day').utc().format(full_format);;
            var utc_end_time = moment.tz(timezone).endOf('day').utc().format(full_format);;

            console.log("utc start and end: " + utc_start_time + " " + utc_end_time);
			window.socket.emit('my data', {data: "temperature", date: [utc_start_time, utc_end_time]});
			window.socket.emit('my data', {data: "gas", date: [utc_start_time, utc_end_time]});
			window.socket.emit('my data', {data: "illuminance", date: [utc_start_time, utc_end_time]});
			window.socket.emit('my data', {data: "buzzer", date: [utc_start_time, utc_end_time]});
    	},
    	socketinit: function () {
            var now = moment.utc();
            var hour = getHour(now, utc_offset);
            //var hour = moment(time).format();
            console.log('utc offset: ' + utc_offset + ' hour:' + hour);
			namespace = '/index'; // change to an empty string to use the global namespace
			var day = ['0', '1',
						'2', '3', '4',
						'5', '6','7',
						'8','9','10','11','12',
						'13','14',
						'15','16','17','18',
						'19','20','21','22','23'];
			// the socket.io documentation recommends sending an explicit package upon connection
			// this is specially important when using the global namespace
			if(window.socket != null)
			{
				$.sh.before.sendrequest();
				return;
			}

			window.socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

			setInterval($.sh.before.sendrequest,3600000);

			// event handler for server sent data
			// the data is displayed in the "Received" section of the page
			socket.on('my response', function (msg) {
				//alert(msg.data);
			});
			// event handler for new connections
			socket.on('connect', function () {
				console.log("i'm connected!");
			});
			socket.on( 'my temperature', function (msg ) {
				console.log( "temperature");
				var temp_data = msg.data;
                console.log(temp_data);
				if(temp_data.length==0)
				{
					var content = "<div style='text-align:center'><label>There is no data today.</label></div>";
					$("#container2").html(content);
				}
				else
				{
					var chart_data = Array.apply(null, Array(hour+1)).map(Number.prototype.valueOf,0);
                    var average_temp = 0;
                    var local_hour;
                    var is_Celsius = true;
                    var temp_unit = "°";
                    console.log('index: ' + timezone.indexOf("US") + " tz: " + timezone);
                    if(timezone.indexOf('America') == 0 || timezone.indexOf('US') == 0) {
                        is_Celsius = false;
                        temp_unit += "F";
                    }
                    else temp_unit += "C";

					for (var i =0;i<temp_data.length;i++)
					{
                        local_hour = utc_offset+temp_data[i][1];
                        if(local_hour < 0)
                            local_hour += 24;
                        else if (local_hour > 24)
                            local_hour -= 24;
                        //console.log('local hour: ' + local_hour);
                        console.log("is: " + is_Celsius + " c: " + parseFloat(temp_data[i][0].toFixed(2)) + " f:" + convertToF(parseFloat(temp_data[i][0]), 2));
                        var temp = is_Celsius? parseFloat(temp_data[i][0].toFixed(2)): parseFloat(convertToF(parseFloat(temp_data[i][0]), 2));
                        chart_data[local_hour] = temp;
						average_temp += temp;
					}
                    console.log('avg total: ' + average_temp);
					average_temp = (average_temp/temp_data.length).toFixed(2);
                    console.log('avg: ' + average_temp);
					$("#averagetemp").text(average_temp.toString()+ temp_unit);
					drawcontainerchart('container2',day,chart_data,getDay(),'Time(hour)', 'average temperature', temp_unit);
				}
			});
			socket.on('my gas', function (msg) {
				console.log("gas");
				var num = msg.data;
                //console.log(num);
				if(num.length==0)
				{
					var content = "<div style='text-align:center'><label>There is no data today.</label></div>";
					$("#container4").html(content);
				}
				else
				{
                    var chart_data = Array.apply(null, Array(hour+1)).map(Number.prototype.valueOf,0);
                    var local_hour;
                    for (var i =0;i<num.length;i++) {
                        local_hour = utc_offset + num[i][1];
                        if (local_hour < 0)
                            local_hour += 24;
                        else if (local_hour > 24)
                            local_hour -= 24;
                        chart_data[local_hour] = parseFloat(num[i][0].toFixed(2));
                    }
					drawcontainerchart('container4',day,chart_data, getDay(),'Time(hour)', 'total times', 'times');
					if(num[num.length-1]>0)
						$("#safestate").text("Unsafe");
					else
					    $("#safestate").text("Safe");
				}

			});
			socket.on('my buzzer', function (msg) {
				console.log("buzzer");
				var num = msg.data;
				if(num.length==0)
				{
					var content = "<div style='text-align:center'><label>There is no data today.</label></div>";
					$("#container3").html(content);
				}
				else {
                    var chart_data = Array.apply(null, Array(hour+1)).map(Number.prototype.valueOf, 0);
                    var local_hour;
                    for (var i = 0; i < num.length; i++) {
                        local_hour = utc_offset + num[i][1];
                        if (local_hour < 0)
                            local_hour += 24;
                        else if (local_hour > 24)
                            local_hour -= 24;
                        chart_data[local_hour] = parseFloat(num[i][0].toFixed(2));
                    }
                    drawcontainerchart('container3', day, chart_data, getDay(), 'Time(hour)', 'total times', 'times');
                }
			});

			socket.on('my illuminance', function (msg) {
				console.log("illuminance");
				var light_data = msg.data;
				if(light_data.length==0)
				{
					var content = "<div style='text-align:center'><label>There is no data today.</label></div>";
					$("#container5").html(content);
				}
				else
				{
                    var chart_data = Array.apply(null, Array(hour+1)).map(Number.prototype.valueOf,0);
                    var local_hour;
					for (var i =0;i<light_data.length;i++)
					{
                        local_hour = utc_offset+light_data[i][1];
                        if(local_hour < 0)
                            local_hour += 24;
                        else if (local_hour > 24)
                            local_hour -= 24;
                        chart_data[local_hour] = parseFloat(light_data[i][0].toFixed(2));
					}
					drawcontainerchart('container5',day,chart_data, getDay(),'Time(hour)', 'average illuminance', 'lm');
				}
			});

			$.sh.before.sendrequest();
    	},
		init: function() {
			console.log("init before page.");
            $("#demo-welcome-message").html("This demo tells you about your <b>home sensor history.</b>");
			window.panel = 2;
            $('#sh-before').show();
		    $('#sh-now').hide();
            $('#alert-status-card').hide();
			//window.trigger("resize");
			$.sh.before.register_actions();
			$.sh.before.loading();
            $.sh.before.update_billing("#tab1");
			$.sh.before.socketinit();
            $.sh.before.update_static_data();
		}
	};

	$("a:contains('NOW')").on('click', function() {
		clearInterval(time_timer);
        clearInterval(now_timer);
        clearInterval(weather_timer);
		//clearInterval(chart_timer);
		$.sh.now.init();
	});
	$("a:contains('BEFORE')").on('click', function() {
     	clearInterval(time_timer);
		clearInterval(now_timer);
        clearInterval(weather_timer);
		$.sh.before.init();
	});

    setInterval(function(){
        updateWelcomeCardsDateTime(utc_offset, timezone);
    }, 60 * 1000);


    $.sh.init();
    $.sh.now.init();
    updateWelcomeCardsDateTime(utc_offset, timezone);
});
