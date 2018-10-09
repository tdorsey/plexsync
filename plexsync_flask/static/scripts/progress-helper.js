$ = require('jquery');
message = require('./message-helper');
mbps = require('mbps');
moment = require('moment');

function createBar(barID) {

    var bar =  $.parseHTML(`<div id="${barID}" class="progress-bar progress-bar-striped bg-success progress-bar-animated"
                                  role="progressbar" aria-valuemin="0" aria-valuemax="100">
                        <span class="progress-text"></span>
                </div>`);

    return $(bar);
}

function updateBar(bar, taskGUID) {
    doUpdate(taskGUID)
    interval = setInterval(doUpdate, 1 * 1000, [taskGUID]);

    }


function updateBarTooltip(bar, opts) {
    let defaults = {tooltip: "tooltip", placement: "top", text: null }
    let options = Object.assign({}, defaults, opts);

        bar.attr('data-toggle', options.tooltip);
        bar.attr('data-placement', options.placement);
        bar.attr('title', options.text);

}

function doUpdate(taskGUID) {

        $.ajax({
            type: "GET",
            url: `/task/${taskGUID}` }).done(
                function(response, textStatus)  {
                total = response.total;
                current = response.current;
                statusText = response.status;
                statusPercentage = Math.floor(response.percent);
                bytesPerSecond = Math.round(response.bytesPerSecond);
                statusPercentageDisplay = `${statusPercentage}%`;
                etaDisplay = `${moment().add(response.eta,'seconds').fromNow()}`
                speedDisplay = `${mbps(bytesPerSecond,1)}`;
                tooltipText = `${etaDisplay} at ${speedDisplay}`;

                var bar = $("#" + taskGUID);

                bar.closest(".card").toggle(true);
                bar.attr('aria-valuemin', 0);
                bar.attr('aria-valuemax', 100);
                bar.attr('aria-valuenow', statusPercentage);

                updateBarTooltip(bar, {'text' : tooltipText });

                bar.width(statusPercentageDisplay);
                bar.children(".progress-text").text(statusPercentageDisplay);

                if (response.state && response.state == "SUCCESS") {

                    clearInterval(interval);
                    notify.showNotification("Transfer Completed", response.message);

                }
            }).fail(function(response, status){
                clearInterval(interval);
                message.danger(response.responseText);
            });



        }
function  getExistingTasks() {
    items = JSON.parse(localStorage.getItem("itemsInProgress"));
        if (!items) {
            return
        }
    let data = {};
    data.guids =  [];

    items.forEach(item => {
        data.guids.push(item.guid);
        data.server = item.server;
        data.section = item.sectionID;
        createBar(item.task)
    });

        fetch( "/task/render", {
            method: 'POST',
            body: JSON.stringify(data), // data can be `string` or {object}!
            headers:{
                'Content-Type': 'application/json'
            }


        }).then(response => {
            if (response.ok) {
                return response.text();
            }
            else {
                message.danger(response.statusText);
                return null;
            }
            }).then(text => {
                $("#comparison_results").before(text);
            }).catch(msg => {
                console.error('Error:', msg);
                message.danger(msg);
                });
}

exports.createBar = createBar;
exports.updateBar = updateBar;
exports.getTransfersInProgress = getExistingTasks;
