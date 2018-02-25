FROM lsiobase/alpine.python3

WORKDIR /app

# Expose the Flask port
EXPOSE 5000

ENTRYPOINT [ "python3" ]

CMD ["app.py"]

VOLUME /config
VOLUME /downloads

RUN apk update && apk add nodejs
RUN npm install -g browserify notifyjs
RUN npm link notifyjs

COPY requirements.txt .
COPY config.ini /config/
COPY /templates ./templates
COPY /static  ./static

RUN browserify -d ./static/scripts/main.js > ./static/scripts/bundle.js


COPY app.py .
COPY /plexsync/ ./plexsync

RUN pip install -r requirements.txt 





