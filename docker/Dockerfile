FROM python:3.6-alpine3.6

USER root
WORKDIR /

ENV PUID ${PUID:-1100}
ENV PGID ${PGID:-1101}
RUN addgroup -S -g ${PGID} plexsync
RUN adduser -S -G plexsync -u ${PUID} plexsync

RUN mkdir /downloads # && chown -R plexsync:plexsync /downloads && chmod -R 770 /downloads
RUN mkdir /logs # && chown -R plexsync:plexsync /logs && chmod -R 770 /logs
RUN mkdir /config # && chown -R plexsync:plexsync /config && chmod -R 777 /config

ENTRYPOINT ["/entrypoint.sh"]
COPY entrypoint.sh /entrypoint.sh

# Expose the Flask port
EXPOSE 5000

VOLUME /config
VOLUME /logs
VOLUME /downloads

#System Reqs
RUN apk update && apk add nodejs-npm python3 git nano build-base uwsgi-python
RUN pip install --upgrade pip

#NPM globals
RUN npm install -g npm@latest
RUN npm install -g browserify


#Python Reqs

WORKDIR /plexsync_flask
COPY requirements.txt /plexsync_flask/
RUN pip install -r requirements.txt

COPY plexsync_flask/package.json /plexsync_flask/plexsync_flask/

WORKDIR /plexsync_flask/plexsync_flask
RUN npm install --save

RUN mkdir -p static/images && cp node_modules/octicons/build/svg/* static/images

WORKDIR /
COPY celeryconfig.py /plexsync_flask/
COPY config.py /plexsync_flask/
COPY manage.py /plexsync_flask/

COPY entrypoint.sh /

COPY plexsync/ /plexsync/
RUN pip install -e /plexsync/

WORKDIR /plexsync_flask/plexsync_flask

COPY webserver/ /plexsync_flask/webserver/
COPY tests/ /plexsync_flask/tests/

WORKDIR /plexsync_flask


COPY plexsync_flask/ plexsync_flask/
RUN python manage.py createdb

COPY plexsync_flask/static/ plexsync_flask/static/
COPY plexsync_flask/templates/ plexsync_flask/templates/


WORKDIR /plexsync_flask/plexsync_flask

RUN browserify -d  /plexsync_flask/plexsync_flask/static/scripts/main.js --debug -p [ parcelify -o /plexsync_flask/plexsync_flask/static/css/bundle.css ] > /plexsync_flask/plexsync_flask/static/scripts/bundle.js

WORKDIR /plexsync_flask
