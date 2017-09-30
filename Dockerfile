FROM lsiobase/alpine.python3

WORKDIR /app

COPY requirements.txt .

COPY app.py .
COPY config.ini /config/

COPY /plexsync/ ./plexsync
COPY /plexsync/ .

COPY /static  ./static
COPY /templates ./templates

RUN pip install -r requirements.txt 

# Expose the Flask port
EXPOSE 5000


ENTRYPOINT [ "python3" ]
CMD ["app.py"]
