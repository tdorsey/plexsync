let $ = require('jquery')
const PLEX_API_URL = "https://plex.tv/api/v2/";
const PLEX_OAUTH_URL = "https://app.plex.tv/auth#!"
const PLEX_CREATE_PIN_URL = "https://plex.tv/api/v2/pins?strong=true"
const PLEX_GET_PIN_URL = "https://plex.tv/api/v2/pins/"
const DEVICE_PRODUCT = "plexsync"
const DEVICE_PLATFORM = "Linux"
const PRODUCT_VERSION = "develop"
const PLATFORM_VERSION  = "4.9.0-7-amd64"

let htest = {
"X-PLEX-PROVIDES" : "1",
"X-PLEX-PLATFORM" : "2",
"X-PLEX-PLATFORM-VERSION" : "3",
"X-PLEX-PRODUCT" : "4",
"X-PLEX-VERSION" : "5",
"X-PLEX-DEVICE" : "6",
"X-PLEX-DEVICE-NAME" : "7",
"X-PLEX-CLIENT-IDENTIFIER" : "8"
};

let hworking = { "X-Plex-Client-Identifier" : "plexsync"};

let hcontext = {
'context[device][environment]': 11,
'context[device][layout]' : 12,
'context[device][product]' :13,
'context[device][platform]': 14,
'context[device][device]': 15
};



let code = null;
let pin = null;

async function createPinCode(clientId) {

const result = await $.ajax({
    url: PLEX_CREATE_PIN_URL,
    type: 'post',
    data: null,
    headers: hworking,
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
    data: pinId,
    headers: {
        "X-Plex-Client-Identifier": DEVICE_PRODUCT
    },
    dataType: 'json',
    always: function (data) {
        console.log(data) 
        
    }
});

return result;
}

async function getToken() {

let pinCodeResponse = await createPinCode(DEVICE_PRODUCT);
let code = pinCodeResponse.code

// clientID is random int less than 10

let randomID = Math.floor(Math.random() * Math.floor(10));

let params = {

forwardUrl : `https://ps.rtd3.me/pin/${pinCodeResponse.id}`,
pinID : pinCodeResponse.id,
code : pinCodeResponse.code,
'context[device][product]' : DEVICE_PRODUCT,
clientID : DEVICE_PRODUCT
}

const oauthURL = PLEX_OAUTH_URL + "?" + $.param(params);

let rtn = { url : oauthURL,
	    pin : pinCodeResponse.id } 
return rtn;

}


exports.getToken = getToken;
exports.getPin = getPin;
