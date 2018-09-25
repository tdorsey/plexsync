var $ = require('jquery')
var io = require('socket.io-client');
var socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);



$(document).ready(function(){
    socket.on('template_rendered', function(data) {
        console.log("template_rendered")
        $('#comparison_results').append(data.html);
    });
    socket.on('comparison_done', function(response) {
        console.log("received comparison_done")
        let message = {"server" : response.server,
                       "section" : response.section  };
        response.items.forEach(guid =>
		 {
                      message.guid = guid ;
                      socket.emit("render_template", message);
            });
    });
   
});


module.exports = socket;
