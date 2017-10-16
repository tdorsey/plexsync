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
    $( document ).ready(function() {
      $(".server").prepend(new Option("Select a Server", null, true, true));  
      $(".server").change(onSelectServer);
      $(".section").change(onSelectSection);
      });

