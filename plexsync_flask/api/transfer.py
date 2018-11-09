from . import api
from . import plexsync

@api.route('/download', methods=['POST'])
def download():
    guid = request.form['guid']
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync.getAccount()
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    result.download()


@api.route('/transfer', methods=['POST'])
def transfer():
        server = request.form['server']
        sectionID = request.form['section']
        guid = request.form['guid']
        guid = urllib.parse.unquote(guid)
        plexsync.getAccount()

        ownedServers = plexsync.getOwnedServers()
        currentUserServer = session['yourServer']
        current_app.logger.debug(f"ownedServers {ownedServers}")
        current_app.logger.debug(f"currentServer {currentUserServer}")
        authorized = False
        for s in ownedServers:
            if s.friendlyName == currentUserServer:
                authorized = True
            theirServer = plexsync.getServer(server)
            section = theirServer.library.sectionByID(sectionID)
            result = section.search(guid=guid).pop()
        if authorized:
            current_app.logger.debug(f"authorized")
            item = { "server" : theirServer.friendlyName,
                     "section" : section.title,
                     "guid" : guid  }

            response = transfer_item(item)
            return jsonify(response)

        else:
                current_app.logger.debug(f"not authorized")
                msg = f"Not authorized to transfer {result.title} to {currentUserServer}"
                status = 403
                response =  jsonify(message= {"text" : msg, "severity" : "danger" }, status=status)
                response.status_code = status
                return response
