    function onSelectSection(e) {
        var that = this;
        var section = $(this).val();
        var server = $("#serverA").val();
        var endpoint = $SCRIPTROOT + '/servers/' + server + '/' + section
        $.post(endpoint, { server : server, section : section }, function(response) {
            sectionMedia = $(that).siblings(".media")
            sectionMedia.empty()
            $.each(response, function(index, item) {
                sectionMedia.append('<li>' + item + '</li>');
            });
           $(that).parent().find(".section_title").text(server);
        }, 'json');

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
        var endpoint = $SCRIPTROOT + '/compare/' + serverA + '/' + serverB + '/' + section
        $.get(endpoint, { yourServerName : serverA, theirServerName : serverB, sectionName : section }, 
            function(response) {
                var resultList = $("#resultList")
                resultList.empty();
                    $.each(response, function(index, item) {
                        var li = $(`<li></li>`);
                        li.text(item.title);
                        li.addClass("list-group-item");
                        li.attr('data-guid', item.guid);
                        resultList.append(li);
                    });
        }, 'json');

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
      $(".server").change(onSelectServer);
      $(".section").change(onSelectSection);
      });

