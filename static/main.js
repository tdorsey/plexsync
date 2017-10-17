    function onSelectSection(e) {
        var that = this;
        var section = $(this).val();
        var server = $(this).siblings(".server").val();
        var endpoint = $SCRIPTROOT + '/servers/' + server + '/' + section
        $.post(endpoint, { server : server, section : section }, function(response) {
            sectionMedia = $(that).siblings(".media")
            sectionMedia.empty()
            $.each(response, function(index, item) {
                sectionMedia.append('<li>' + item + '</li>');
            });
        }, 'json');

} 
    function onSelectServer(e) {
        var that = this;
        var server = $(this).val();
        var dropdownB = $("#server2").find(".server");
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

