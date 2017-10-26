    function onSelectSection(e) {
        var that = this;
        var section = $(this).val();
        var server = $("#serverA").val();
        var endpoint = $`{SCRIPTROOT}/servers/{server}/{section}`;
//        $.post(endpoint, { server : server, section : section }, function(response) {
 //           sectionMedia = $(that).siblings(".media")
   //         sectionMedia.empty()
     //       $.each(response, function(index, item) {
       //         sectionMedia.append('<li>' + item + '</li>');
         //   });
          // $(that).parent().find(".section_title").text(server);
//        }, 'json');

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
        var endpoint = $`{SCRIPTROOT}/compare/{serverA}/{serverB}/{section}`
         $.ajax({url: endpoint, success: function(result){
                $("#comparison_results").append(result);

          }}); 

} 

    function sync() {
        $("#comparison_results").find(".list-group-item.active").each(function() {
            var guid = $(this).attr("data-guid");
            var libraryID = $(this).attr("data-libraryID");
            var item = { "libraryID" : libraryID, "guid" : guid }; 
            syncItem(item);
          }});

        });
 
}

       function syncItem(item) {

        var syncEndpoint = $`{SCRIPTROOT}/sync/{item.libraryID}/{item.guid}`;
         $.ajax({url: syncEndpoint, success: function(result){
                $("#sync_results").append(result);
          }});
}

    function toggleSelect() {
        alert("toggling Select");
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
      });

