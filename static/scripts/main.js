    function onSelectSection(e) {
        var that = this;
        var section = $(this).val();
        var server = $("#serverA").val();
        var endpoint = $`{SCRIPTROOT}/servers/{server}/{section}`;
} 
    function onSelectServer(e) {
        var that = this;
        var server = $(this).val();
        var dropdownB = $("#server2").find(".server");
        $("#server1_collapse").show().text(`Collapse ${server}`);
        $("#server2_collapse").show().text(`Collapse ${dropdownB.val()}`);
        $("#results_collapse").show().text(`Collapse Results`);
        hideOptionInDropdown(this, dropdownB);

        var endpoint = $SCRIPTROOT + '/servers/' + server;
        $.post(endpoint, { server : server }, function(response) {
            sectionSelect = $(that).siblings(".section");
            sectionSelect.empty();
            sectionSelect.append(new Option("Select a Section", null, true, true));
            $("#compare").show();
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
         $.ajax({url: endpoint, success: function(result){
                $("#comparison_results").append(result);

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
console.log(item);
guid = encodeURIComponent(item.guid);

var transferEndpoint = "/transfer";
var trimmed = {

	guid:  item.guid,
	server: item.server,
	section:  item.sectionID

 }


$.ajax({
  type: 'POST',
  url: transferEndpoint,
  data: trimmed
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

    $( document ).ready(function() {
          $(".server").prepend(new Option("Select a Server", null, true, true));  
          $("#serverA").change(onSelectServer);
          $(".section").change(onSelectSection);
          $("#compare").hide();
          $('#list').click(function(event){
            event.preventDefault();
            $('#comparison_results .item').addClass('list-group-item');});
    
          $('#grid').click(function(event){
                event.preventDefault();
                $('#comparison_results .item').removeClass('list-group-item');
                $('#comparison_results .item').addClass('grid-group-item');});

      });

