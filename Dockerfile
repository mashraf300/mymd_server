FROM python:3.12.6

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

ENV FLASK_APP=db.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]