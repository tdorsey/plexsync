FROM lsiobase/alpine.python3

WORKDIR /app

COPY requirements.txt /app

#Copy files
COPY app.py .
COPY config.ini /config/

#Copy folders
COPY /plexsync/ ./plexsync
COPY /plexsync/ .

COPY /static/  /static/
COPY /templates/ /static/

RUN pip install -r requirements.txt 

# Expose the Flask port
EXPOSE 5000


ENTRYPOINT [ "python3" ]
CMD ["app.py"]
