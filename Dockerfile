FROM lsiobase/alpine.python3

WORKDIR /app

# Expose the Flask port
EXPOSE 5000

ENTRYPOINT [ "python3" ]

#Set python output to unbuffered, so print statements are visible
CMD ["-u", "app.py"]

VOLUME /downloads

COPY requirements.txt .
COPY app.py .
COPY /plexsync/ ./plexsync


RUN pip install -r requirements.txt 


COPY config.ini /config/


COPY /static  ./static
COPY /templates ./templates


