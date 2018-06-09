$ = require('jquery');
message = require('./message-helper');
function createBar(barID) {

    var bar =  $.parseHTML(`<div id="${barID}" class="progress-bar progress-bar-striped bg-success progress-bar-animated"
                                  role="progressbar" aria-valuemin="0" aria-valuemax="100">
                        <span class="progress-text"></span>
                </div>`);

    return $(bar);
}

function updateBar(bar, taskGUID) {
    doUpdate(taskGUID)
    interval = setInterval(doUpdate, 10 *1000, [taskGUID]);

    }

function doUpdate(taskGUID) {

        $.ajax({
            type: "GET",
            url: `/task/${taskGUID}` }).done(
                function(response, textStatus)  {
                total = response.total;
                current = response.current;
                statusText = response.status;

                statusPercentage = Math.floor(( current / total) * 100);
                statusPercentageDisplay = `${statusPercentage}%`;

                var bar = $("#" + taskGUID);

                bar.closest(".card").toggle(true);
                bar.attr('aria-valuemin', 0);
                bar.attr('aria-valuemax', 100);
                bar.attr('aria-valuenow', statusPercentage);
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

exports.createBar = createBar;
exports.updateBar = updateBar;

