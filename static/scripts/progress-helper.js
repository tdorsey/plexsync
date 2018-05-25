$ = require('jquery');

var _total = null;
var _current = null;
var _bar = null;
var _taskGUID = null;
var _interval = null;

function updateBar(bar, taskGUID) {
    _bar = bar;
    _taskGUID = taskGUID;
    _interval = setInterval(doUpdate, 10 *1000);
  
    }
    




function doUpdate() {

        $.ajax({
            type: "GET",
            url: `/task/${_taskGUID}`,
            success: function(response, textStatus)  {
                _total = response.total;
                _current = response.current;
                statusText = response.status;

                statusPercentage = Math.floor(( _current / _total) * 100);
                statusPercentageDisplay = `${statusPercentage}%`;


                $(_bar).closest(".card").toggle(true);
                $(_bar).attr('aria-valuemin', 0);
                $(_bar).attr('aria-valuemax', 100);
                $(_bar).attr('aria-valuenow', statusPercentage);
                $(_bar).width(statusPercentageDisplay);
                $(".progress-text").text(statusPercentageDisplay);

                if (_total === _current) {

                    clearInterval(_interval);
                    notify.showNotification("Transfer Completed", textStatus);

                }
            },
           
        });
       
};


    exports.updateBar = updateBar;

