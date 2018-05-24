$ = require('jquery');

function updateBar(bar, taskGUID) {

        $.ajax({
            type: "GET",
            url: `/task/${taskGUID}`,
            success: function(response, textStatus)  {
                maxVal = response.total;
                current = response.current;
                statusText = response.status;

                if (maxVal === current) {
                    clearTimeout(timeout);
                }
                
                $(bar).toggle(true);
                $(bar).attr('max', maxVal);
                $(bar).attr('value', current);
            },
        });
    }

    exports.updateBar = updateBar;
   
       
    
