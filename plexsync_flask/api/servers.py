from . import api

from . import plexsync

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

@api.route('/servers/<string:serverName>', methods=['GET','POST'])
def sections(serverName):
    current_app.logger.debug(f"routing for {serverName}")
    plexsync.getAccount()
    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)

    section_list = []
    
    for section in sections:
        result = {"id": section.key, "name": section.title, "type": section.type}
        section_list.append(result)
        sortedSections = sorted(section_list,key=lambda s: s.get("name"))
    with current_app.app_context():
        return jsonify(sortedSections)


@api.route('/servers/<string:serverName>/<string:section>', methods=['GET'])
def media(serverName, section):
    current_app.logger.debug(f"routing for {serverName} - {section}")
    plexsync.getAccount()
    
    server = plexsync.getServer(serverName)
    results = plexsync.getResults(server, section)

    sortedResults = sorted([r.title for r in results])
    with current_app.app_context():
        return jsonify(sortedResults)

@api.route('/compare/<string:yourServerName>/<string:theirServerName>', methods=['GET'])
@api.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:section>', methods=['GET'])
@api.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:sectionKey>', methods=['GET'])
def compare(yourServerName, theirServerName, sectionKey=None):
    try:
        with current_app.app_context():
            plexsync.getAccount()
            yourServer = plexsync.getServer(yourServerName)
            theirServer = plexsync.getServer(theirServerName)

            section = plexsync.getSection(theirServer, sectionKey)
            sectionName = section.title

            session['yourServer'] = yourServerName
            message = { "yourServer" : yourServerName,
                    "theirServer" : theirServerName,
                    "section" : sectionName  }

            current_app.logger.warning(f"{message}")
            signature = compare_task.s()
            task = signature.apply_async(args=[message])
            current_app.logger.debug(f" result backend {task.backend}")
            current_app.logger.debug(f"Compare Task: {task} ")
  
            message["task"] = task.id
            status_url = url_for('tasks.status', _scheme='https', _external=True, id=task.id)
            message["status_url"] = status_url
            return jsonify(message)

    except Exception as e:
        with current_app.app_context():
            current_app.logger.exception(e)
            response = jsonify(str(e))
            response.status_code = 500
            return response
        return render_template('media.html', media=result_list)
