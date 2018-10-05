var $ = require('jquery')
var io = require('socket.io-client');
var urlencode = require("urlencode");
var socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);

function onComparisonDone(response) {
        console.log("received comparison_done")
        let item = {"server" : response.message.server,
                       "section" : response.message.section  };
        item.server = urlencode.encode(item.server);
        item.section = urlencode.encode(item.section);
        response.message.items.forEach(guid =>
        {
           item.guid = urlencode.encode(guid);
           console.log(item.guid);
           fetch(`/item/${item.server}/${item.section}/${item.guid}`)
             .then(function(response) {
                return response.text();
                 })
            .then(function(html) {
                 $("#comparison_results").append(html);
                   item.guid = guid ;
                   console.log(`template rendered for ${item.guid}`);
                   socket.emit("render_template", item);
                });


     
         });

}

function onTemplateRendered(response) {
    console.log("template_rendered")
        $('#comparison_results').append(response.html);
}   


$(document).ready(function(){
    socket.on('template_rendered', onTemplateRendered);
    socket.on('comparison_done', onComparisonDone);
});


module.exports = socket;
