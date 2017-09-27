    function onSelectSection(e) {
        var server = $('.server').val();
        var endpoint = $SCRIPTROOT + '/servers/' + server + '/' + section
        $.post(endpoint, { server : server, section : section }, function(response) {
            sectionMedia = $('.media')
            sectionMedia.empty()
            $.each(response, function(index, item) {
                sectionMedia.append('<li>' + item '</li>');
            });
        }, 'json');

} 
    function onSelectServer(e) {
        
        var server = $(this).val();
        var endpoint = $SCRIPTROOT + '/servers/' + server
        $.post(endpoint, { server : server }, function(response) {
            sectionSelect = $('.section')
            sectionSelect.empty()
            $.each(response, function(index, item) {
                sectionSelect.append(new Option(item, item));
            });
        }, 'json');
}
    $( document ).ready(function() {
      $(".server").change(onSelectServer);
      $(".section").change(onSelectSection);
      });

