const $ = require('jquery');
const message = require('./message-helper');
const shortId = require('shortid');
const PLEX_API_URL = "https://plex.tv/api/v2/";
const PLEX_OAUTH_URL = "https://app.plex.tv/auth#!"
const PLEX_CREATE_PIN_URL = "https://plex.tv/api/v2/pins?strong=true"
const PLEX_GET_PIN_URL = "https://plex.tv/api/v2/pins/"
const DEVICE_PRODUCT = "plexsync"
const DEVICE_PLATFORM = "Linux"
const PRODUCT_VERSION = "develop"
const PLATFORM_VERSION  = "4.9.0-7-amd64"
const CLIENT_ID = shortId.generate();
let htest = {

    "X-Plex-Product" : DEVICE_PRODUCT,
    "X-Plex-Version" : PRODUCT_VERSION,
    "X-Plex-Client-Identifier" : CLIENT_ID
}

let code = null;
let pin = null;

async function createPinCode(clientId) {

const result = await $.ajax({
    url: PLEX_CREATE_PIN_URL,
    type: 'post',
    data: null,
    headers: htest,
    dataType: 'json',
    always: function (data) {
        console.log(data) 
        
    }
});

return result;
}
async function getPin(pinId) {

let pinURL = PLEX_GET_PIN_URL + pinId;

const result = await $.ajax({
    url: pinURL,
    type: 'get',
    dataType: 'json',
    always: function (data) {
        console.log(data) 

    }
});

return result;
}
async function getForwardURL(client, pin) {


       return fetch( `pin/redirect_to/${client}/${pin}`, {
            headers:{
                'Content-Type': 'application/json'
            }


        }).then(response => {
            if (response.ok) {
                return response.json();
            }
            else {
                message.danger(response.statusText, { "removeOthers" : true });
                return null;
            }
            }).then(json => {
                return json
            }).catch(msg => {
                console.error('Error:', msg);
                message.danger(msg);
                });
}

async function getToken() {

let pinCodeResponse = await createPinCode(CLIENT_ID);
let code = pinCodeResponse.code

 let forwardUrl = await getForwardURL(pinCodeResponse.clientIdentifier, pinCodeResponse.id);
let params = {
forwardUrl : `${forwardUrl}`,
pinID : pinCodeResponse.id,
code : pinCodeResponse.code,
clientID : pinCodeResponse.clientIdentifier,
"context[device][product]" : DEVICE_PRODUCT
}

const oauthURL = PLEX_OAUTH_URL + "?" + $.param(params);

let rtn = { url : oauthURL,
	        pin : pinCodeResponse.id } 
return rtn;

}


exports.getToken = getToken;
exports.getPin = getPin;
