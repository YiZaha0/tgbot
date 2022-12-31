FROM python:latest 

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get -y update && \
    apt-get install -y --no-install-recommends git ffmpeg sudo wkhtmltopdf && \
    rm -rf /var/lib/apt/lists/* 

RUN git clone https://github.com/YiZaha0/tgbot /root/tgbot-rep

WORKDIR /root/tgbot-rep

RUN pip install -U pip wheel && \
    pip install -r requirements.txt

CMD ["bash", "qstart"]
