FROM ubuntu:20.04

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -y update && apt -y upgrade  && \
    apt install -y --no-install-recommends python3 python3-pip git ffmpeg

RUN git clone https://github.com/YiZaha0/tgbot /root/tgbot-rep

WORKDIR /root/tgbot-rep

RUN pip install -U pip wheel && \
    pip install -r requirements.txt

CMD ["bash", "qstart"]
