    function onSelectSection(e) {} 
    function onSelectServer(e) {
        console.log(e)
        
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

