from . import api
from . import plexsync

@api.route('/item/<string:serverName>/<string:sectionName>/<path:guid>', methods=['GET'])
def renderSingleItemPath(serverName, sectionName, guid):
            current_app.logger.info(f"Rendering GUID {guid}")
            serverName = urllib.parse.unquote(serverName)
            sectionName = urllib.parse.unquote(sectionName)
            guid = urllib.parse.unquote(guid)
            plexsync.getAccount()
            server = plexsync.getServer(serverName)
            section = plexsync.getSection(server, sectionName)
            result = section.search(guid=guid).pop()
            m = plexsync.prepareMediaTemplate(result)
            return render_template('media.html', media=m)
