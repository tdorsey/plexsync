var $ = require('jquery');
var notify = require('./notify-helper');
var progress = require('./progress-helper');


    function onSelectSection(e) {
        var that = this;
        var section = $(this).val();
        var server = $("#serverA").val();
        var endpoint = $`{SCRIPTROOT}/servers/{server}/{section}`;
} 

function onTransferClick(obj) {

  item = $(obj).data("item");  

   transfer(item).then(function(response) {

        var subtitle =  $(obj).parent().siblings(".card-subtitle");
        var bar = $(obj).siblings(".progress");
        sessionStorage.setItem(response.result.key, response.result);
        notify.showNotification("Transfer Started", response.message);
        subtitle.children(".text-muted").append(response.result.task);
        setTimeout(progress.updateBar, 5000, bar, response.result.task);
    }, null);
}
    function onSelectServer(e) {
        var server = $(this).val();
        var dropdownB = $("#serverB");
        $("#server1_collapse").show().text(`Collapse ${server}`);
        $("#server2_collapse").show().text(`Collapse ${dropdownB.val()}`);
        $("#results_collapse").show().text(`Collapse Results`);
        hideOptionInDropdown(this, dropdownB);

        var endpoint = $SCRIPTROOT + '/servers/' + server;
        $.post(endpoint, { server : server }, function(response) {
            toggleCompareFields();
            sectionSelect = $(".section");
            sectionSelect.empty();
            sectionSelect.append(new Option("Select a Section", null, true, true));

            $.each(response, function(index, item) {
                sectionSelect.append(new Option(item, item));
            });
        }, 'json');
    }

    function compareLibraries() {
        var serverA = $("#serverA").val();
        var serverB = $("#serverB").val();
        var section = $("#section").val();
        $("#comparison_title").text(`${serverB} has the following new ${section}` );
        var endpoint = '/compare/' + serverA + '/' + serverB + '/' + section;
         $.ajax({url: endpoint, 
            beforeSend: function(req) {
            //If this is returned as json, flask doesn't render the media item as JSON safely. By accepting html, we ensure the template sanitizes it.
                req.setRequestHeader("Accept", "text/html");
            },
            success: function(result){
                $("#comparison_results").append(result);
                resizeMediaDivs();
                $(".progress").toggle(false);

          }}); 

} 

    function sync() {
        $("#comparison_results").find(".list-group-item.active").each(function() {
            var guid = $(this).attr("data-guid");
            var sectionID = $(this).attr("data-sectionID");
            var item = { "sectionID" : sectionID, "guid" : guid }; 
            syncItem(item);
          });

}

       function syncItem(item) {
        theirServer = $("#serverB").val(); 
        var syncEndpoint = "/search";
         $.post(syncEndpoint, { server : theirServer, section : item.sectionID, guid : item.guid }, 
            function(result) {
                $("sync_results").append(result);
            });

}
    function downloadSelected() {
        $("#comparison_results").find(".list-group-item.active").each(function() {
            var guid = $(this).attr("data-guid");
            var sectionID = $(this).attr("data-sectionID");
            var item = { "sectionID" : sectionID, "guid" : guid }; 
            downloadItem(item);
          });

}

       function downloadItem(item) {
        theirServer = $("#serverB").val(); 
        var downloadEndpoint = "/download";
         $.post(downloadEndpoint, { server : theirServer, section : item.sectionID, guid : item.guid }, 
            function(result) {
                $("download_results").append(result);
            });

}
function transfer(item) {
    guid = encodeURIComponent(item.guid);
    var transferEndpoint = "/transfer";
    var trimmed = {
    	guid:  item.guid,
	    server: item.server,
	    section:  item.sectionID
    }
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "POST",
            url: transferEndpoint,
            data: trimmed,
            success: function(response, textStatus)  {
                resolve(response);
              },
              error: function(jqXHR, textStatus)  {
                reject(jqXHR.responseJSON);
            },
        });
    });

}
   function toggleSelected() {
        var that = this;
        var selected =  $("#toggleSelected").attr('data-selected');

        if (selected) {
            $(".list-group-item").each(function() {
                $(this).removeClass('active');
            });
        }
        else {

            $(".list-group-item").each(function() {
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
        dropdownB.children().each(function() {
            var option = $(this);
            if (valA == option.val()) {
                option.hide();
                option.siblings().show();
             }
        });
    }
   function resizeMediaDivs() {
    var maxHeight = 0;

    $(".result").each(function(index, result){
        parent = $(result).parent();
        h = $(".result").height();
        if (h > maxHeight) {
            maxHeight = h; 
            var movie = $(result).find(".list-group-item-heading").text();
            console.log(movie + " is taller" + h + "px"); 
        }
    });

    console.log(maxHeight);
    //$(".result").height(maxHeight);

    }

    $( document ).ready(function() {
          $(".server").prepend(new Option("Select a Server", null, true, true));  
          $("#serverA").change(onSelectServer);
          $(".section").change(onSelectSection);

          toggleCompareFields();
   
          $('#list').click(function(event){
            event.preventDefault();
            $('#comparison_results .item').addClass('list-group-item');});
    
          $('#grid').click(function(event){
                event.preventDefault();
                $('#comparison_results .item').removeClass('list-group-item');
                $('#comparison_results .item').addClass('grid-group-item');});

      });

exports.transfer = transfer
exports.compareLibraries = compareLibraries
exports.resizeMediaDivs = resizeMediaDivs
exports.onTransferClick = onTransferClick
