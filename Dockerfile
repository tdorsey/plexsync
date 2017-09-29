FROM lsiobase/alpine.python3

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
COPY ./config.ini /config

# Expose the Flask port
EXPOSE 5000

CMD [ "python3", "/app/app.py" ]
