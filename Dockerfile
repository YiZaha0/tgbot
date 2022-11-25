FROM python:latest

WORKDIR /root/tgbot

COPY . .

RUN pip install -U -r requirements.txt

CMD ["python", "main.py"]
