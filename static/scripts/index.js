let $ = require('jquery')
let login = require('./plex-oauth');
let pin = null;


$(document).ready(function(){

	$("#plex-oauth").click(function(e) {

		login.getToken().then( function(token) {
			console.log(token);
			window.open(token.url);
		});
	});

});
