var $ = require('jquery')
var io = require('socket.io-client');
var socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);



$(document).ready(function(){
    socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);
    socket.on('template_rendered', function(data) {
        console.log("template_rendered")
        $('#comparison_results').append(data.html);
    });

});


module.exports = socket;
