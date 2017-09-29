FROM lsiobase/alpine.python3

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

#Copy files
COPY app.py /app
COPY config.ini /config

#Copy folders
COPY plexsync /app/
COPY scripts /app/
COPY static /app/
COPY templates /app/

# Expose the Flask port
EXPOSE 5000

CMD [ "python3", "/app/app.py" ]
