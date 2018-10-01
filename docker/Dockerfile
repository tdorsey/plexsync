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
# Expose the Flask port
EXPOSE 5000

VOLUME /config
VOLUME /logs
VOLUME /downloads

VOLUME /plexsync_flask

#COPY plexsync_flask/* /plexsync_flask/

#build base >> gcc >> eventlet >> websockets
RUN apk update && apk add nodejs-npm python3 git nano build-base uwsgi-python

RUN npm install -g npm@latest
RUN npm install -g browserify

RUN pip3 install --upgrade pip

RUN chown -R plexsync:plexsync /plexsync_flask && chmod -R 770 /plexsync_flask


COPY requirements.txt /plexsync_flask/
RUN pip3 install -r /plexsync_flask/requirements.txt

COPY manage.py /plexsync_flask
COPY celeryconfig.py /plexsync_flask


##RUN chmod g+s .
#USER plexsync

COPY plexsync_flask/ /plexsync_flask/
COPY plexsync_flask/package.json .

RUN npm install --save
COPY plexsync_flask/templates/* /plexsync_flask/templates/
COPY plexsync_flask/static/*  /plexsync_flask/static/
#TODO: Symlinking should work here but doesn't, figure out why
RUN cp node_modules/octicons/build/svg/* /plexsync_flask/static/images/
RUN browserify -d  /plexsync_flask/static/scripts/main.js --debug -p [ parcelify -o /plexsync_flask/static/css/bundle.css ] > /plexsync_flask/static/scripts/bundle.js 

WORKDIR /plexsync_flask

COPY docker/entrypoint.sh /

RUN chown -R plexsync:plexsync /downloads && chmod -R 777 /downloads

COPY plexsync_flask/config.py /plexsync_flask


RUN chown -R  plexsync:plexsync /plexsync_flask




COPY /plexsync/ /plexsync
RUN pip3 install -e /plexsync

#RUN python3 manage.py createdb




