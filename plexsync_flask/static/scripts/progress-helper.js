$ = require('jquery');
message = require('./message-helper');
notify = require('./notify-helper');
mbps = require('mbps');
moment = require('moment');

function createBar(barID) {

    var bar =  $.parseHTML(`<div id="${barID}" class="progress-bar progress-bar-striped bg-success progress-bar-animated"
                                  role="progressbar" aria-valuemin="0" aria-valuemax="100">
                        <span class="progress-text"></span>
                </div>`);
    return $(bar);
}

function updateBar(taskGUID) {
    doUpdate(taskGUID);
    interval = setInterval(doUpdate, 1 * 1000, taskGUID);
    return interval;
    }


function updateBarTooltip(bar, opts) {
    let defaults = {tooltip: "tooltip", placement: "top", text: null }
    let options = Object.assign({}, defaults, opts);

        bar.attr('data-toggle', options.tooltip);
        bar.attr('data-placement', options.placement);
        bar.attr('title', options.text);

}

async function doUpdate(taskGUID) {

    let updateResponse = await fetch(`/api/task/${taskGUID}`);
     if (updateResponse.ok) {
            let response = await updateResponse.json()
               var bar = $(`#${taskGUID}`);
                if (response.state == "PENDING") {
                    bar.children(".progress-text").text("Waiting to start");
                    return;
                }

                if (!response.info) {
                    clearTaskInterval(taskGUID);
                }


                total = response.info.total;
                current = response.info.current;
                statusText = response.info.status;
                statusPercentage = Math.floor(response.info.percent);
                bytesPerSecond = Math.round(response.info.bytesPerSecond);
                statusPercentageDisplay = `${statusPercentage}%`;
                etaDisplay = `${moment().add(response.info.eta,'seconds').fromNow()}`
                speedDisplay = `${mbps(bytesPerSecond,1)}`;
                tooltipText = `${etaDisplay} at ${speedDisplay}`;
                bar.closest(".card").toggle(true);
                bar.attr('aria-valuemin', 0);
                bar.attr('aria-valuemax', 100);
                bar.attr('aria-valuenow', statusPercentage);

                updateBarTooltip(bar, {'text' : tooltipText });

                bar.width(statusPercentageDisplay);
                bar.children(".progress-text").text(statusPercentageDisplay);

                if (response.state && response.state == "SUCCESS") {

                    clearTaskInterval(taskGUID);
                    notify.showNotification("Transfer Completed", response.info.message);
                }
     }       
      else {
                clearInterval(taskGUID);
                message.danger(updateResponse.statusCode);
                }
        }

async function cancelUpdate(taskID) {
    let cancelResponse = await fetch(`/api/task/${taskID}`, { method: 'DELETE'} );
    if (cancelResponse.ok) {
        let json = await cancelResponse.json();
        clearTaskInterval(taskID);
        localStorage.removeItem(taskID);
        $("div #" + taskID).parents(".row").remove();
    }
}

function clearTaskInterval(taskID) {

    if (taskID) {
        let itemsInProgress = JSON.parse(localStorage.getItem("itemsInProgress"));
        if (!itemsInProgress) {
            return false;
        }
        let index = itemsInProgress.indexOf(taskID)
        if (index > -1) {
            let itemFound = itemsInProgress.splice(index,1);
            if (itemsInProgress.length > 0) {
                localStorage.setItem("itemsInProgress", JSON.stringify(itemsInProgress));
            }
            else {
                localStorage.removeItem("itemsInProgress");
            }
            let storedItem = localStorage.getItem(taskID);
                if (storedItem) {
                    let task = JSON.parse(storedItem);
                    if (task && task.interval) {
                        clearInterval(task.interval);
                        localStorage.removeItem(task);
                    }
                }
        }
    }
}


async function renderItemInProgress(i) {
    let item = JSON.parse(localStorage.getItem(i));
    if (!item) {
        console.log(`Couldn't get item ${i} from local storage`);
        return;
    }

    let data = { "guids": [] };

    data.guids.push(item.guid);
    data.server = item.server;
    data.section = item.sectionID;
    data.task =  item.task;

    let statusResponse = await fetch(`/api/task/${data.task}`, {
        headers: { 'Content-Type': 'application/json'}
    });

    if (statusResponse.ok) {
        let status = await statusResponse.json();
        if (status.state == "ABORTED") {
            localStorage.removeItem(data.task);
        }
        else {
            let renderResponse = await fetch("/task/render", {
                    method: 'POST',
                    body: JSON.stringify(data), 
                    headers: { 'Content-Type': 'application/json' }
            });

            let text = await renderResponse.text();

            if (text) {
                $("#comparison_results").before(text);
                barDiv = $(document).find(`#${data.task}-container`);
                bar = createBar(data.task);
                barDiv.append(bar);
                updateBar(data.task);
            }
        }
    }
}

async function  getExistingTasks() {
    items = JSON.parse(localStorage.getItem("itemsInProgress"));
        if (!items) {
            return
        }

    for (const i of items) {
      renderItemInProgress(i);
    }
}

exports.createBar = createBar;
exports.updateBar = updateBar;
exports.getTransfersInProgress = getExistingTasks;
exports.cancelUpdate = cancelUpdate;
