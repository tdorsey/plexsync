var $ = require('jquery')
var io = require('socket.io-client');
var urlencode = require("urlencode");
var message = require('./message-helper');

function onComparisonDone(response) {
        console.log("received comparison_done")
        let item = {"server" : response.message.server,
                       "section" : response.message.section  };
        item.server = urlencode.encode(item.server);
        item.section = urlencode.encode(item.section);
        message.warning(`Getting ${response.message.section} information`, { "removeOthers" : true });
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
        message.success("Done getting info", { "removeOthers" : true } );

}

function onComparisonEventStep(response) {
    socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);
    message.showMessage(response.message, { "messageType" : response.level, "removeOthers" : true });
}

function onTemplateRendered(response) {
    console.log("template_rendered")
        $('#comparison_results').append(response.html);
}

    socket = io.connect(`${location.protocol}//${document.domain}/plexsync`);
    socket.on('template_rendered', onTemplateRendered);
    //socket.on('comparison_done', onComparisonDone);

// register comparison catchalls

    socket.on('STARTING', onComparisonEventStep);
    socket.on('SCANNING', onComparisonEventStep);
    socket.on('COMPARING', onComparisonEventStep);
    socket.on('FINALIZING', onComparisonEventStep);
    socket.on('INTIALIZING', onComparisonEventStep);
    socket.on('CONNECTING', onComparisonEventStep);

    socket.on('SUCCESS', onComparisonDone);



module.exports = socket;
