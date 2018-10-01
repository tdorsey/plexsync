var $ = require('jquery');
var notify = require('./notify-helper');
var progress = require('./progress-helper');
var message = require('./message-helper');
var socket = require('./sockets');


function onSelectSection(e) {
    var that = this;
    var section = $(this).val();
    var server = $("#serverA").val();
    var endpoint = $`{SCRIPTROOT}/servers/{server}/{section}`;
}

function onTransferClick(obj) {

    item = $(obj).data("item");
    transfer(item).then(function (response) {
        //display the progress bar

        var innerCardDeck = $(obj).parents(".card-deck");
        progressDiv = innerCardDeck.find(".progress");

        //start the transfer 
        response.result.forEach(element => {
            sessionStorage.setItem(element.key, element);
            bar =  progress.createBar(element.task);
            bar.closest(".card").toggle(true);

            progressDiv.append(bar);
            progress.updateBar(bar, element.task);
        });
        notify.showNotification("Transfer Started", response.message.text);

    }, function (response) {
        msg = `${response.status}: ${response.message.text}`;
        message.danger(msg);
    }
    );
}
function onSelectServer(e) {
    var server = $(this).val();
    var dropdownB = $("#serverB");
    $("#server1_collapse").show().text(`Collapse ${server}`);
    $("#server2_collapse").show().text(`Collapse ${dropdownB.val()}`);
    $("#results_collapse").show().text(`Collapse Results`);
    hideOptionInDropdown(this, dropdownB);

    var endpoint = $SCRIPTROOT + '/servers/' + server;
    $.post(endpoint, { server: server }, function (response) {
        toggleCompareFields();
        sectionSelect = $(".section");
        sectionSelect.empty();
        sectionSelect.append(new Option("Select a Section", null, true, true));
        response.forEach(section => {
            sectionSelect.append(new Option(section.name, section.name));
        })
    }, 'json');
}

function compareLibraries() {
    var serverA = $("#serverA").val();
    var serverB = $("#serverB").val();
    var section = $("#section").val();
    var sectionKey = $("#section").val();
    $("#comparison_title").text(`${serverB} has the following new ${section}`);
    $("#comparison_results").empty();
    var endpoint = '/compare/' + serverA + '/' + serverB + '/' + sectionKey;
    var compareRequest = $.ajax({ url: endpoint  }).done(function(response) {
	console.log(response);
	}
	).fail(
            function (xhr, status, error) {
                msg = `${xhr.status}: ${xhr.responseText}`;
                message.danger(msg);
            });

}

function sync() {
    $("#comparison_results").find(".list-group-item.active").each(function () {
        var guid = $(this).attr("data-guid");
        var sectionID = $(this).attr("data-sectionID");
        var item = { "sectionID": sectionID, "guid": guid };
        syncItem(item);
    });

}

function syncItem(item) {
    theirServer = $("#serverB").val();
    var syncEndpoint = "/search";
    $.post(syncEndpoint, { server: theirServer, section: item.sectionID, guid: item.guid },
        function (result) {
            $("sync_results").append(result);
        });

}
function downloadSelected() {
    $("#comparison_results").find(".list-group-item.active").each(function () {
        var guid = $(this).attr("data-guid");
        var sectionID = $(this).attr("data-sectionID");
        var item = { "sectionID": sectionID, "guid": guid };
        downloadItem(item);
    });

}

function downloadItem(item) {
    theirServer = $("#serverB").val();
    var downloadEndpoint = "/download";
    $.post(downloadEndpoint, { server: theirServer, section: item.sectionID, guid: item.guid },
        function (result) {
            $("download_results").append(result);
        });

}
function transfer(item) {
    guid = encodeURIComponent(item.guid);
    var transferEndpoint = "/transfer";
    var trimmed = {
        guid: item.guid,
        server: item.server,
        section: item.sectionID
    }

    return new Promise((resolve, reject) => {
        $.ajax({
            type: "POST",
            url: transferEndpoint,
            data: trimmed,
            success: function (response, textStatus) {
                resolve(response);
            },
            error: function (jqXHR, textStatus) {
                reject(jqXHR.responseJSON);
            },
        });
    });

}
function toggleSelected() {
    var that = this;
    var selected = $("#toggleSelected").attr('data-selected');

    if (selected) {
        $(".list-group-item").each(function () {
            $(this).removeClass('active');
        });
    }
    else {

        $(".list-group-item").each(function () {
            $(this).addClass('active');
        });

        selected.attr("data-selected", true);
    }
}

function toggleCompareFields() {
    //   $("#compare").toggle();
    $("#section").toggle();

}

function hideOptionInDropdown(dropdownA, dropdownB) {
    var valA = $(dropdownA).val();
    dropdownB.children().each(function () {
        var option = $(this);
        if (valA == option.val()) {
            option.hide();
            option.siblings().show();
        }
    });
}
function resizeMediaDivs() {
    var maxHeight = 0;

    $(".result").each(function (index, result) {
        parent = $(result).parent();
        h = $(".result").height();
        if (h > maxHeight) {
            maxHeight = h;
            var movie = $(result).find(".list-group-item-heading").text();
            console.log(movie + " is taller" + h + "px");
        }
    });

    // console.log(maxHeight);
    //$(".result").height(maxHeight);

}

$(document).ready(function () {
    $(".server").prepend(new Option("Select a Server", null, true, true));
    $("#serverA").change(onSelectServer);
    $(".section").change(onSelectSection);
    toggleCompareFields();
    message.hide();

    $('#list').click(function (event) {
        event.preventDefault();
        $('#comparison_results .item').addClass('list-group-item');
    });

    $('#grid').click(function (event) {
        event.preventDefault();
        $('#comparison_results .item').removeClass('list-group-item');
        $('#comparison_results .item').addClass('grid-group-item');
    });

});

exports.transfer = transfer
exports.compareLibraries = compareLibraries
exports.resizeMediaDivs = resizeMediaDivs
exports.onTransferClick = onTransferClick