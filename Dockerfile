FROM lsiobase/alpine.python3

WORKDIR /app


COPY requirements.txt .
COPY app.py .
COPY /plexsync/ ./plexsync


RUN pip install -r requirements.txt 


COPY config.ini /config/


COPY /static  ./static
COPY /templates ./templates


# Expose the Flask port
EXPOSE 5000

#ENTRYPOINT ["tail", "-f", "/dev/null"]

ENTRYPOINT [ "python3" ]
CMD ["app.py"]
