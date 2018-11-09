
from . import api
@api.route('/pin/redirect_to/<string:client>/<int:pin>', methods=['GET'])
def getRedirectURL(client,pin):
    forwardURL = url_for('main.exchangePinForAuth', clientId=client, pinId=pin, _scheme='https', _external=True )
    current_app.logger.debug(f"Got forwardURL {forwardURL}")
    return jsonify(forwardURL)

@api.route('/pin/<string:clientId>/<string:pinId>', methods=['GET'])
def exchangePinForAuth(clientId, pinId):
   try:
        current_app.logger.debug(f"received pin id: {pinId}")
        headers = {'X-Plex-Client-Identifier': clientId}
        url = f"https://plex.tv/api/v2/pins/{pinId}.json"
        r = requests.get(url=url, headers=headers )
        token = r.json()['authToken']
        session['token'] = token
        current_app.logger.debug(f"Got auth token {token}")
        return redirect(url_for('main.home'))
   except KeyError:
        
        current_app.logger.exception(f"An error occurred signing in to Plex: {r.json()}")
        return jsonify(r.json()['errors'].pop()['message'])
